"""PydanticAI integration — ShadowAudit tool wrapper.

Wraps PydanticAI tools or callables with deterministic runtime enforcement.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

from shadowaudit.core.gate import Gate
from shadowaudit.core.fsm import FailClosedFSM
from shadowaudit.errors import AgentActionBlocked
from shadowaudit.framework._base import _GuardedToolMixin

__all__ = ["ShadowAuditPydanticTool", "AgentActionBlocked"]


class ShadowAuditPydanticTool(_GuardedToolMixin):
    """Transparent wrapper for PydanticAI tools or callables."""

    def __init__(
        self,
        tool: Callable[..., Any],
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

        self.name = getattr(tool, "name", getattr(tool, "__name__", "tool"))
        self.description = getattr(tool, "description", "")

    @staticmethod
    def _build_payload_from_call(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        payload = {"args": list(args)}
        payload.update(kwargs)
        return payload

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        payload = self._build_payload_from_call(args, kwargs)
        self._check(payload)
        return self._tool(*args, **kwargs)

    async def acall(self, *args: Any, **kwargs: Any) -> Any:
        payload = self._build_payload_from_call(args, kwargs)
        await self._acheck(payload)
        result = self._tool(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
