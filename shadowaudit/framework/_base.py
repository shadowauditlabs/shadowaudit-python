"""Shared helpers for framework adapters.

The single-tool adapters (LangChain, CrewAI) all do the same three things:
build a payload dict from heterogeneous tool input, run a sync gate check,
or run an async gate check. This mixin centralises that logic so each
adapter only implements the framework-specific run/arun glue.
"""
from __future__ import annotations

from typing import Any

from shadowaudit.core.fsm import FailClosedFSM
from shadowaudit.core.gate import Gate
from shadowaudit.errors import AgentActionBlocked


class _GuardedToolMixin:
    """Provides `_build_payload`, `_check`, `_acheck` to single-tool adapters.

    Subclasses must set: ``_gate``, ``_fsm``, ``_agent_id``,
    ``_risk_category``, and ``name``.
    """

    _gate: Gate
    _fsm: FailClosedFSM
    _agent_id: str
    _risk_category: str | None
    _capability: str | None
    _policy_path: str | None
    name: str

    @staticmethod
    def _build_payload(tool_input: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(tool_input, str):
            return {"input": tool_input}
        return dict(tool_input)

    def _check(self, payload: dict[str, Any]) -> None:
        result = self._gate.evaluate(
            agent_id=self._agent_id,
            task_context=self.name,
            risk_category=self._risk_category,
            payload=payload,
            capability=getattr(self, "_capability", None),
            policy_path=getattr(self, "_policy_path", None),
        )
        outcome = self._fsm.transition(result)
        if outcome.decision != "pass":
            raise AgentActionBlocked(detail=outcome.detail, gate_result=result)

    async def _acheck(self, payload: dict[str, Any]) -> None:
        result = await self._gate.evaluate_async(
            agent_id=self._agent_id,
            task_context=self.name,
            risk_category=self._risk_category,
            payload=payload,
            capability=getattr(self, "_capability", None),
            policy_path=getattr(self, "_policy_path", None),
        )
        outcome = self._fsm.transition(result)
        if outcome.decision != "pass":
            raise AgentActionBlocked(detail=outcome.detail, gate_result=result)
