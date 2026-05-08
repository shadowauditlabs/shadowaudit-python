"""Local rule-based Cognitive Gate.

Uses fixed thresholds from taxonomy with pluggable risk scoring.
Works offline. No API key needed. SQLite-backed state tracking.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from shadowaudit.types import GateResult
from shadowaudit.core.state import AgentStateStore
from shadowaudit.core.taxonomy import TaxonomyLoader
from shadowaudit.core.hash import compute_payload_hash
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.scorer import BaseScorer, KeywordScorer, load_scorer

logger = logging.getLogger(__name__)


def score_payload(
    payload: dict[str, Any],
    risk_keywords: list[str],
    scorer: BaseScorer | None = None,
    category_config: dict[str, Any] | None = None,
    agent_id: str | None = None,
) -> float:
    """Score payload risk using a pluggable scorer.

    Args:
        payload: The tool call payload to evaluate.
        risk_keywords: Keywords to match against from taxonomy.
        scorer: Optional custom scorer. Uses KeywordScorer if None.
        category_config: Full category config for adaptive scorers.
        agent_id: Agent identifier for behavioral scoring context.
    """
    _scorer = scorer or KeywordScorer()
    return _scorer.score(payload, risk_keywords, category_config, agent_id=agent_id)


def compute_threshold(delta: float) -> float:
    """Compute static threshold from taxonomy delta."""
    return delta


class Gate:
    """Rule-based runtime risk evaluator.

    Works offline. No API key needed. SQLite-backed state tracking.
    Pluggable scorer architecture — swap scoring strategies via constructor.
    """

    def __init__(
        self,
        state_store: AgentStateStore | None = None,
        taxonomy_path: str | None = None,
        cloud_client: Any | None = None,
        audit_logger: AuditLogger | None = None,
        scorer: BaseScorer | None = None,
    ) -> None:
        self._store = state_store or AgentStateStore()
        self._taxonomy_path = taxonomy_path
        self._cloud = cloud_client
        self._audit = audit_logger or AuditLogger()
        self._scorer = scorer or load_scorer(state_store=self._store)

    def evaluate(
        self,
        agent_id: str,
        task_context: str,
        risk_category: str | None,
        payload: dict[str, Any],
    ) -> GateResult:
        """Evaluate payload risk and return pass/fail decision.

        Always records decision for next K computation and audit log,
        even on failure.
        """
        start_ms = int(time.time() * 1000)

        # 1. Look up taxonomy
        taxonomy_entry = TaxonomyLoader.lookup(risk_category, taxonomy_path=self._taxonomy_path)
        delta = taxonomy_entry.get("delta", 0.1)
        risk_keywords = taxonomy_entry.get("risk_keywords", [])

        # 2. Compute K and V (for telemetry, future adaptive use)
        K = self._store.compute_K(agent_id)
        V = self._store.compute_V(agent_id)

        # 3. Score payload risk with pluggable scorer
        # Inject risk category name so scorer can make category-aware decisions
        # IMPORTANT: copy the dict to avoid mutating the cached taxonomy object
        taxonomy_entry = dict(taxonomy_entry)
        taxonomy_entry["name"] = risk_category
        risk_score = score_payload(payload, risk_keywords, self._scorer, taxonomy_entry, agent_id=agent_id)

        # 4. Compute threshold
        if self._cloud is not None and hasattr(self._cloud, "get_threshold"):
            try:
                threshold = self._cloud.get_threshold(K=K, V=V, delta=delta)
            except Exception:
                logger.warning("Cloud threshold fetch failed, falling back to local delta=%.3f", delta)
                threshold = compute_threshold(delta)
        else:
            threshold = compute_threshold(delta)

        # 5. Decision
        passed = risk_score <= threshold

        # 6. Record for next K — now with full tool context for behavioral analysis
        payload_hash = compute_payload_hash(payload)
        tool_name = task_context
        amount = self._extract_amount(payload)
        self._store.record_decision(
            agent_id, passed,
            payload_hash=payload_hash,
            tool_name=tool_name,
            risk_category=risk_category,
            amount=amount,
        )

        elapsed = int(time.time() * 1000) - start_ms
        result = GateResult(
            passed=passed,
            risk_score=risk_score,
            threshold=threshold,
            risk_category=risk_category,
            reason="pass" if passed else "drift_detected",
            latency_ms=elapsed,
            metadata={
                "K": K,
                "V": V,
                "delta": delta,
                "payload_hash": payload_hash,
                "scorer_type": type(self._scorer).__name__,
            },
        )

        # 7. Audit log
        try:
            self._audit.record(agent_id, task_context, risk_category, result, payload_hash=payload_hash)
        except Exception as e:
            # Audit failure is a tamper signal — do not silently swallow
            logger.warning("Audit log failure for agent_id=%s: %s", agent_id, type(e).__name__)
            # Decision already recorded to state store (step 6); escalate through FSM
            result = GateResult(
                passed=result.passed,
                risk_score=result.risk_score,
                threshold=result.threshold,
                risk_category=result.risk_category,
                reason="audit_failure_" + type(e).__name__ if result.passed else result.reason,
                latency_ms=result.latency_ms,
                metadata={**result.metadata, "audit_error": type(e).__name__},
            )

        # 8. Optional cloud telemetry (fire-and-forget)
        if self._cloud is not None and hasattr(self._cloud, "evaluate"):
            try:
                self._cloud.evaluate(
                    agent_id=agent_id,
                    task_context=task_context,
                    risk_category=risk_category,
                    payload=payload,
                    local_result=result.__dict__,
                )
            except Exception:
                logger.debug("Cloud telemetry fire-and-forget failed for agent_id=%s", agent_id)

        return result

    def _extract_amount(self, payload: dict[str, Any]) -> float | None:
        """Extract monetary amount from common payload fields."""
        for key in ("amount", "total", "value", "sum", "quantity", "price"):
            val = payload.get(key)
            if val is not None:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    continue
        return None

