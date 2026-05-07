"""CrewAI integration — ShadowAuditCrewAITool wrapper.

Wraps any CrewAI BaseTool with deterministic runtime enforcement.

Usage:
    from crewai.tools import BaseTool
    from shadowaudit.framework.crewai import ShadowAuditCrewAITool

    safe_tool = ShadowAuditCrewAITool(
        tool=MyCrewAITool(),
        agent_id="ops-agent-1",
        risk_category="command_execution",
        gate=Gate(),  # optional: custom gate instance
    )

    # Use exactly like the original CrewAI tool
    result = safe_tool.run("input here")

A blocked call raises AgentActionBlocked — catch and handle in your agent loop.
"""

from __future__ import annotations

from typing import Any

from shadowaudit.core.gate import Gate
from shadowaudit.core.fsm import FailClosedFSM
from shadowaudit.types import GateResult


class AgentActionBlocked(Exception):
    """Raised when ShadowAudit blocks a tool execution."""

    def __init__(self, detail: str, gate_result: GateResult | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.gate_result = gate_result


class ShadowAuditCrewAITool:
    """Transparent wrapper adding deterministic gate enforcement to any CrewAI tool.

    Mirrors the CrewAI BaseTool interface for drop-in replacement.
    """

    def __init__(
        self,
        tool: Any,  # CrewAI BaseTool or duck-typed
        agent_id: str,
        risk_category: str | None = None,
        gate: Gate | None = None,
    ) -> None:
        self._tool = tool
        self._agent_id = agent_id
        self._risk_category = risk_category
        self._gate = gate or Gate()
        self._fsm = FailClosedFSM()

        # Mirror tool metadata
        self.name = getattr(tool, "name", "unknown_tool")
        self.description = getattr(tool, "description", "")

    def run(self, tool_input: str | dict[str, Any], **kwargs: Any) -> Any:
        """Run the tool after gate evaluation."""
        # Normalize input to dict for gating
        if isinstance(tool_input, str):
            payload = {"input": tool_input}
        else:
            payload = dict(tool_input)

        # Evaluate
        result = self._gate.evaluate(
            agent_id=self._agent_id,
            task_context=self.name,
            risk_category=self._risk_category,
            payload=payload,
        )

        # FSM transition — fail-closed
        outcome = self._fsm.transition(result)

        if outcome.decision != "pass":
            raise AgentActionBlocked(
                detail=outcome.detail,
                gate_result=result,
            )

        # Execute wrapped tool
        return self._tool.run(tool_input, **kwargs)

    def __getattr__(self, name: str) -> Any:
        # Transparent passthrough for tool attributes
        return getattr(self._tool, name)
