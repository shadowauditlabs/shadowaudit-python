"""LangChain integration — CapFenceTool wrapper.

Wraps any LangChain BaseTool with deterministic runtime enforcement.

Usage:
    from langchain.tools import ShellTool
    from capfence.framework.langchain import CapFenceTool

    safe_shell = CapFenceTool(
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

from capfence.core.gate import Gate
from capfence.core.fsm import FailClosedFSM
from capfence.errors import AgentActionBlocked
from capfence.framework._base import _GuardedToolMixin

__all__ = ["CapFenceTool", "AgentActionBlocked", "capfence_guard"]


class CapFenceTool(_GuardedToolMixin):
    """Transparent wrapper adding deterministic gate enforcement to any tool.

    Implements the same interface as the wrapped tool for drop-in replacement.
    """

    def __init__(
        self,
        tool: Any,  # BaseTool or duck-typed
        agent_id: str,
        risk_category: str | None = None,
        capability: str | None = None,
        policy_path: str | None = None,
        gate: Gate | None = None,
    ) -> None:
        self._tool = tool
        self._agent_id = agent_id
        self._risk_category = risk_category
        self._capability = capability
        self._policy_path = policy_path
        self._gate = gate or Gate()
        self._fsm = FailClosedFSM()

        # Mirror tool metadata
        self.name = getattr(tool, "name", "unknown_tool")
        self.description = getattr(tool, "description", "")

    def run(self, tool_input: str | dict[str, Any], **kwargs: Any) -> Any:
        """Run the wrapped tool after a synchronous gate check."""
        payload = self._build_payload(tool_input)
        self._check(payload)
        return self._tool.run(tool_input, **kwargs)

    async def arun(self, tool_input: str | dict[str, Any], **kwargs: Any) -> Any:
        """Async variant. Runs the gate check off the event loop, then awaits
        the wrapped tool's ``arun`` if it has one (otherwise falls back to sync ``run``)."""
        payload = self._build_payload(tool_input)
        await self._acheck(payload)
        if hasattr(self._tool, "arun"):
            return await self._tool.arun(tool_input, **kwargs)
        return self._tool.run(tool_input, **kwargs)

    def __getattr__(self, name: str) -> Any:
        # Transparent passthrough for tool attributes
        return getattr(self._tool, name)


# Convenience decorator for function tools

def capfence_guard(
    agent_id: str,
    risk_category: str | None = None,
    capability: str | None = None,
    policy_path: str | None = None,
    gate: Gate | None = None,
) -> Callable[..., Any]:
    """Decorator factory for function-based LangChain tools.

    Usage:
        @capfence_guard(agent_id="finance-1", risk_category="disbursement")
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
                capability=capability,
                policy_path=policy_path,
            )
            outcome = _fsm.transition(result)
            if outcome.decision != "pass":
                raise AgentActionBlocked(detail=outcome.detail, gate_result=result)
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
