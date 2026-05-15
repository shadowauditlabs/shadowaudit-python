"""LlamaIndex integration — CapFence tool wrapper.

Wraps LlamaIndex tools with deterministic runtime enforcement.
"""

from __future__ import annotations

import inspect
from typing import Any

from capfence.core.gate import Gate
from capfence.core.fsm import FailClosedFSM
from capfence.errors import AgentActionBlocked
from capfence.framework._base import _GuardedToolMixin

__all__ = ["CapFenceLlamaIndexTool", "AgentActionBlocked"]


class CapFenceLlamaIndexTool(_GuardedToolMixin):
    """Transparent wrapper for LlamaIndex tools."""

    def __init__(
        self,
        tool: Any,
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

        self.name = getattr(tool, "name", "tool")
        self.description = getattr(tool, "description", "")

    def call(self, tool_input: str | dict[str, Any], **kwargs: Any) -> Any:
        payload = self._build_payload(tool_input)
        self._check(payload)
        if hasattr(self._tool, "call"):
            return self._tool.call(tool_input, **kwargs)
        return self._tool(tool_input, **kwargs)

    async def acall(self, tool_input: str | dict[str, Any], **kwargs: Any) -> Any:
        payload = self._build_payload(tool_input)
        await self._acheck(payload)
        if hasattr(self._tool, "acall"):
            return await self._tool.acall(tool_input, **kwargs)
        result = self._tool(tool_input, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
