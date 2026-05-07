"""LangChain integration — ShadowAuditTool wrapper.

Wraps any LangChain BaseTool with deterministic runtime enforcement.

Usage:
    from langchain.tools import ShellTool
    from shadowaudit.framework.langchain import ShadowAuditTool

    safe_shell = ShadowAuditTool(
        tool=ShellTool(),
        agent_id="ops-agent-1",
        risk_category="command_execution",
        gate=Gate(),  # optional: custom gate instance
    )

    # Use exactly like ShellTool
    result = safe_shell.run("ls -la")

A blocked call raises AgentActionBlocked — catch and handle in your agent loop.
"""

from __future__ import annotations

from typing import Any, Callable

from shadowaudit.core.gate import Gate
from shadowaudit.core.fsm import FailClosedFSM
from shadowaudit.types import GateResult


class AgentActionBlocked(Exception):
    """Raised when ShadowAudit blocks a tool execution."""

    def __init__(self, detail: str, gate_result: GateResult | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.gate_result = gate_result


class ShadowAuditTool:
    """Transparent wrapper adding deterministic gate enforcement to any tool.

    Implements the same interface as the wrapped tool for drop-in replacement.
    """

    def __init__(
        self,
        tool: Any,  # BaseTool or duck-typed
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


# Convenience decorator for function tools

def shadowaudit_guard(
    agent_id: str,
    risk_category: str | None = None,
    gate: Gate | None = None,
) -> Callable[..., Any]:
    """Decorator factory for function-based LangChain tools.

    Usage:
        @shadowaudit_guard(agent_id="finance-1", risk_category="disbursement")
        def disburse_funds(account: str, amount: float) -> str:
            ...
    """
    _gate = gate or Gate()
    _fsm = FailClosedFSM()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            payload = {"args": args, "kwargs": kwargs, "task_context": func.__name__}
            result = _gate.evaluate(
                agent_id=agent_id,
                task_context=func.__name__,
                risk_category=risk_category,
                payload=payload,
            )
            outcome = _fsm.transition(result)
            if outcome.decision != "pass":
                raise AgentActionBlocked(detail=outcome.detail, gate_result=result)
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
