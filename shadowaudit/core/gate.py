"""Local rule-based Cognitive Gate.

Uses fixed thresholds from taxonomy with pluggable risk scoring.
Works offline. No API key needed. SQLite-backed state tracking.
"""

from __future__ import annotations

import contextlib
import logging
import time
from typing import Any, Generator

from shadowaudit.types import GateResult
from shadowaudit.core.state import AgentStateStore
from shadowaudit.core.taxonomy import TaxonomyLoader
from shadowaudit.core.hash import compute_payload_hash
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.scorer import BaseScorer, KeywordScorer, load_scorer

logger = logging.getLogger(__name__)

# Gate operating modes
GATE_MODE_ENFORCE = "enforce"   # block when risk_score > threshold (default)
GATE_MODE_OBSERVE = "observe"   # log but never block (staged rollout / shadow mode)


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

    Modes:
        ``enforce`` (default) — blocks tool calls that exceed the risk threshold.
        ``observe`` — logs decisions without blocking; use for staged rollout.

    Example — observe mode for gradual rollout::

        gate = Gate(mode="observe")
        result = gate.evaluate(...)
        # result.passed is always True in observe mode;
        # result.metadata["would_have_blocked"] is True when enforce would block

    Example — bypass with audit trail::

        with gate.bypass(agent_id="agent-1", reason="manual override by ops"):
            result = gate.evaluate("agent-1", ...)
        # result.passed is True; audit log records bypass_reason
    """

    def __init__(
        self,
        state_store: AgentStateStore | None = None,
        taxonomy_path: str | None = None,
        cloud_client: Any | None = None,
        audit_logger: AuditLogger | None = None,
        scorer: BaseScorer | None = None,
        mode: str = GATE_MODE_ENFORCE,
    ) -> None:
        if mode not in (GATE_MODE_ENFORCE, GATE_MODE_OBSERVE):
            raise ValueError(f"Invalid gate mode '{mode}'. Use 'enforce' or 'observe'.")
        self._store = state_store or AgentStateStore()
        self._taxonomy_path = taxonomy_path
        self._cloud = cloud_client
        self._audit = audit_logger or AuditLogger()
        self._scorer = scorer or load_scorer(state_store=self._store)
        self._mode = mode
        # Per-agent bypass stack: agent_id → list[reason]
        self._bypass_stack: dict[str, list[str]] = {}

    @property
    def mode(self) -> str:
        """Current operating mode ('enforce' or 'observe')."""
        return self._mode

    @contextlib.contextmanager
    def bypass(self, agent_id: str, reason: str) -> Generator[None, None, None]:
        """Context manager that bypasses blocking for a single agent.

        The bypass is recorded in the audit log with the supplied reason.
        Use this only for human-approved overrides; the audit trail is immutable.

        Example::

            with gate.bypass("agent-1", reason="approved by oncall #4521"):
                result = gate.evaluate("agent-1", ...)
            # result.passed is True; audit log shows bypass_reason
        """
        if not reason or not reason.strip():
            raise ValueError("bypass() requires a non-empty reason for audit trail.")
        stack = self._bypass_stack.setdefault(agent_id, [])
        stack.append(reason)
        try:
            yield
        finally:
            stack.pop()
            if not stack:
                del self._bypass_stack[agent_id]

    def _bypass_reason(self, agent_id: str) -> str | None:
        """Return active bypass reason for agent_id, or None."""
        stack = self._bypass_stack.get(agent_id)
        return stack[-1] if stack else None

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

        taxonomy_entry = TaxonomyLoader.lookup(risk_category, taxonomy_path=self._taxonomy_path)
        delta = taxonomy_entry.get("delta", 0.1)
        risk_keywords = taxonomy_entry.get("risk_keywords", [])

        K = self._store.compute_K(agent_id)
        V = self._store.compute_V(agent_id)

        # Inject risk category name so scorer can make category-aware decisions
        # IMPORTANT: copy the dict to avoid mutating the cached taxonomy object
        taxonomy_entry = dict(taxonomy_entry)
        taxonomy_entry["name"] = risk_category
        risk_score = score_payload(payload, risk_keywords, self._scorer, taxonomy_entry, agent_id=agent_id)

        if self._cloud is not None and hasattr(self._cloud, "get_threshold"):
            try:
                threshold = self._cloud.get_threshold(K=K, V=V, delta=delta)
            except Exception:
                logger.warning("Cloud threshold fetch failed, falling back to local delta=%.3f", delta)
                threshold = compute_threshold(delta)
        else:
            threshold = compute_threshold(delta)

        raw_passed = risk_score <= threshold
        bypass_reason = self._bypass_reason(agent_id)

        if bypass_reason is not None:
            # Bypass: always pass; audit trail records the override
            passed = True
            reason = f"bypassed: {bypass_reason}"
        elif self._mode == GATE_MODE_OBSERVE:
            # Observe mode: always pass; metadata records what would have happened
            passed = True
            reason = "observed"
        else:
            passed = raw_passed
            reason = "pass" if passed else "drift_detected"

        payload_hash = compute_payload_hash(payload)
        tool_name = task_context
        amount = self._extract_amount(payload)
        self._store.record_decision(
            agent_id, raw_passed,   # record actual risk decision, not bypass/observe override
            payload_hash=payload_hash,
            tool_name=tool_name,
            risk_category=risk_category,
            amount=amount,
        )

        # distance from threshold normalised to [0,1]; 0.0 = right at threshold
        confidence = abs(risk_score - threshold) / max(threshold, 1e-9)
        confidence = min(confidence, 1.0)

        elapsed = int(time.time() * 1000) - start_ms
        metadata: dict[str, Any] = {
            "K": K,
            "V": V,
            "delta": delta,
            "payload_hash": payload_hash,
            "scorer_type": type(self._scorer).__name__,
            "gate_mode": self._mode,
            "confidence": round(confidence, 4),
        }
        if self._mode == GATE_MODE_OBSERVE or bypass_reason is not None:
            metadata["would_have_blocked"] = not raw_passed
        if bypass_reason is not None:
            metadata["bypass_reason"] = bypass_reason

        result = GateResult(
            passed=passed,
            risk_score=risk_score,
            threshold=threshold,
            risk_category=risk_category,
            reason=reason,
            latency_ms=elapsed,
            metadata=metadata,
        )

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
