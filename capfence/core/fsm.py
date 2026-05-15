"""Deterministic fail-closed state machine.

Any evaluation that is not an explicit pass is a hard failure.
No warn, no log-only. Block or execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from capfence.types import GateResult


@dataclass(frozen=True)
class FSMOutcome:
    """Outcome of a fail-closed FSM transition."""
    decision: Literal["pass", "fail_drift", "fail_latency", "fail_tamper", "fail_error"]
    detail: str
    gate_result: GateResult | None = None


class FailClosedFSM:
    """One accepting state: pass. Everything else is terminal failure."""

    @staticmethod
    def transition(result: GateResult) -> FSMOutcome:
        if result.passed:
            return FSMOutcome(
                decision="pass",
                detail="Execution authorized",
                gate_result=result,
            )

        reason = (result.reason or "").lower()

        if "latency" in reason:
            decision: Literal["fail_drift", "fail_latency", "fail_tamper", "fail_error"] = "fail_latency"
            detail = "Blocked: cognitive Gate latency budget exceeded"
        elif "drift" in reason or "audit_failure" in reason:
            decision = "fail_drift"
            detail = "Blocked: agentic drift detected — payload risk exceeds threshold"
        elif "tamper" in reason:
            decision = "fail_tamper"
            detail = "Blocked: payload integrity check failed — possible tampering"
        else:
            decision = "fail_error"
            detail = f"Blocked: {reason}"

        return FSMOutcome(
            decision=decision,
            detail=detail,
            gate_result=result,
        )

