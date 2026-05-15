"""In-process MCP adapter for CapFence.

Wraps an MCP client session so that every tool call is gated
before execution. This is the in-process equivalent of the
stdio proxy gateway.

Usage:
    from capfence.mcp.adapter import CapFenceMCPSession
    from capfence.core.gate import Gate

    session = CapFenceMCPSession(
        underlying_session=mcp_client_session,
        gate=Gate(),
        agent_id="mcp-agent-1",
    )
    result = await session.call_tool("shell", {"command": "ls"})
"""

from __future__ import annotations

import logging
from typing import Any

from capfence.core.gate import Gate
from capfence.core.fsm import FailClosedFSM
from capfence.errors import AgentActionBlocked
from capfence.framework._risk import guess_risk_category

logger = logging.getLogger(__name__)

__all__ = ["CapFenceMCPSession", "AgentActionBlocked"]


class CapFenceMCPSession:
    """Wraps an MCP client session with CapFence gating.

    Transparent passthrough for all methods except tool calls.
    """

    def __init__(
        self,
        underlying_session: Any,
        gate: Gate | None = None,
        agent_id: str = "mcp-agent",
        default_risk_category: str | None = None,
    ) -> None:
        self._session = underlying_session
        self._gate = gate or Gate()
        self._agent_id = agent_id
        self._default_risk_category = default_risk_category
        self._fsm = FailClosedFSM()

    def __getattr__(self, name: str) -> Any:
        """Transparent passthrough for non-wrapped methods."""
        return getattr(self._session, name)

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call a tool through the CapFence gate."""
        risk_category = self._default_risk_category or self._guess_category(name)
        result = await self._gate.evaluate_async(
            agent_id=self._agent_id,
            task_context=name,
            risk_category=risk_category,
            payload=arguments or {},
        )
        outcome = self._fsm.transition(result)
        if outcome.decision != "pass":
            logger.warning(
                "Blocked MCP tool call: %s (score=%.2f, threshold=%.2f)",
                name, result.risk_score or 0.0, result.threshold or 0.0,
            )
            raise AgentActionBlocked(
                detail=f"Tool '{name}' blocked: {result.reason}",
                gate_result=result,
            )
        # Forward to underlying session
        return await self._session.call_tool(name, arguments)

    _guess_category = staticmethod(guess_risk_category)
