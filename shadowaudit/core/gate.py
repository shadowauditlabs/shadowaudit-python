"""Local rule-based Cognitive Gate.

Uses fixed thresholds from taxonomy with pluggable risk scoring.
Works offline. No API key needed. SQLite-backed state tracking.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import threading
import time
from typing import Any, Generator

from shadowaudit.types import GateResult
from shadowaudit.core.state import AgentStateStore
from shadowaudit.core.taxonomy import TaxonomyLoader
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.scorer import BaseScorer, KeywordScorer, load_scorer
from shadowaudit.core.policy import PolicyLoader, Policy
from shadowaudit.core.approvals import ApprovalManager
from shadowaudit.errors import ConfigurationError

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
        policy_loader: PolicyLoader | None = None,
        approval_manager: ApprovalManager | None = None,
    ) -> None:
        if mode not in (GATE_MODE_ENFORCE, GATE_MODE_OBSERVE):
            raise ConfigurationError(f"Invalid gate mode '{mode}'. Use 'enforce' or 'observe'.")
        self._store = state_store or AgentStateStore()
        self._taxonomy_path = taxonomy_path
        self._cloud = cloud_client
        self._audit = audit_logger or AuditLogger()
        self._scorer = scorer or load_scorer(state_store=self._store)
        self._mode = mode
        self._policy_loader = policy_loader or PolicyLoader()
        self._approval_manager = approval_manager or ApprovalManager()
        # Per-agent bypass stack: agent_id → list[reason]
        self._bypass_stack: dict[str, list[str]] = {}
        # Protects _bypass_stack from concurrent agents sharing one Gate.
        self._bypass_lock = threading.RLock()

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
            raise ConfigurationError("bypass() requires a non-empty reason for audit trail.")
        with self._bypass_lock:
            stack = self._bypass_stack.setdefault(agent_id, [])
            stack.append(reason)
        try:
            yield
        finally:
            with self._bypass_lock:
                stack.pop()
                if not stack:
                    self._bypass_stack.pop(agent_id, None)

    def _bypass_reason(self, agent_id: str) -> str | None:
        """Return active bypass reason for agent_id, or None."""
        with self._bypass_lock:
            stack = self._bypass_stack.get(agent_id)
            return stack[-1] if stack else None

    def evaluate(
        self,
        agent_id: str,
        task_context: str,
        risk_category: str | None,
        payload: dict[str, Any],
        capability: str | None = None,
        policy_path: str | None = None,
        policy_context: dict[str, Any] | None = None,
        require_human_approval: bool = False,
    ) -> GateResult:
        """Evaluate payload risk and return pass/fail decision.

        Always records decision for next K computation and audit log,
        even on failure.
        """
        from shadowaudit.core.hash import compute_payload_hash
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

        # --------------------------------------------------
        # Policy & Approval Evaluation
        # --------------------------------------------------
        policy_action = None
        if policy_path:
            try:
                policy = self._policy_loader.load(policy_path)
                p_context = policy_context or {}
                if capability:
                    policy_action = policy.evaluate(capability, p_context, payload)
                
                # If no direct capability match, map risk_level to action
                if policy_action is None:
                    # simplistic mapping of score to risk level
                    if risk_score > threshold * 1.5:
                        rl = "critical"
                    elif risk_score > threshold:
                        rl = "high"
                    elif risk_score > threshold * 0.5:
                        rl = "medium"
                    else:
                        rl = "low"
                    policy_action = policy.evaluate_risk_level(rl)
            except Exception as e:
                logger.warning("Policy evaluation failed: %s", e)

        requires_approval_flag = require_human_approval or policy_action == "require_approval"

        if requires_approval_flag:
            # Check if there's a pending/approved request matching this payload
            # For simplicity, if bypass isn't active, we fail closed with a reason of "approval_required"
            # and insert into the approval queue.
            # In a real async flow, this would pause execution. Here, we fail-closed.
            if bypass_reason is None:
                req = self._approval_manager.request_approval(
                    agent_id=agent_id,
                    tool_name=task_context,
                    capability=capability,
                    payload=payload,
                    reason=f"Risk Score: {risk_score:.2f}, Category: {risk_category}",
                )
                raw_passed = False
                bypass_reason = None
                reason = f"approval_required: {req.id}"

        if policy_action == "deny" or policy_action == "block":
            raw_passed = False
            if bypass_reason is None:
                reason = "policy_deny"
        elif policy_action == "allow":
            if bypass_reason is None and not requires_approval_flag:
                raw_passed = True
                reason = "policy_allow"

        if bypass_reason is not None:
            # Bypass: always pass; audit trail records the override
            passed = True
            reason = f"bypassed: {bypass_reason}"
        elif self._mode == GATE_MODE_OBSERVE:
            # Observe mode: always pass; metadata records what would have happened
            passed = True
            if "approval_required" not in locals().get("reason", "") and policy_action != "deny":
                reason = "observed"
        else:
            passed = raw_passed
            if "reason" not in locals() or (reason != "policy_allow" and reason != "policy_deny" and not reason.startswith("approval_required")):
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

    async def evaluate_async(
        self,
        agent_id: str,
        task_context: str,
        risk_category: str | None,
        payload: dict[str, Any],
    ) -> GateResult:
        """Async wrapper around :meth:`evaluate`.

        Runs the synchronous scoring + SQLite I/O on the default thread-pool
        executor so an event loop is never blocked. Use this from async agent
        frameworks (LangChain ``ainvoke``, LangGraph async nodes, OpenAI
        Agents SDK, MCP).
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.evaluate,
            agent_id,
            task_context,
            risk_category,
            payload,
        )

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
