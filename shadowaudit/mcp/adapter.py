"""In-process MCP adapter for ShadowAudit.

Wraps an MCP client session so that every tool call is gated
before execution. This is the in-process equivalent of the
stdio proxy gateway.

Usage:
    from shadowaudit.mcp.adapter import ShadowAuditMCPSession
    from shadowaudit.core.gate import Gate

    session = ShadowAuditMCPSession(
        underlying_session=mcp_client_session,
        gate=Gate(),
        agent_id="mcp-agent-1",
    )
    result = await session.call_tool("shell", {"command": "ls"})
"""

from __future__ import annotations

import logging
from typing import Any

from shadowaudit.core.gate import Gate
from shadowaudit.core.fsm import FailClosedFSM
from shadowaudit.types import GateResult

logger = logging.getLogger(__name__)


class AgentActionBlocked(Exception):
    """Raised when ShadowAudit blocks an MCP tool call."""

    def __init__(self, detail: str, gate_result: GateResult | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.gate_result = gate_result


class ShadowAuditMCPSession:
    """Wraps an MCP client session with ShadowAudit gating.

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
        """Call a tool through the ShadowAudit gate."""
        risk_category = self._default_risk_category or self._guess_category(name)
        result = self._gate.evaluate(
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

    @staticmethod
    def _guess_category(tool_name: str) -> str | None:
        """Heuristic risk category from tool name."""
        name = tool_name.lower()
        if any(k in name for k in ("shell", "exec", "run", "command", "bash", "sh")):
            return "command_execution"
        if any(k in name for k in ("pay", "transfer", "send", "disburse", "stripe")):
            return "payment_initiation"
        if any(k in name for k in ("delete", "remove", "drop", "wipe")):
            return "delete"
        if any(k in name for k in ("write", "update", "modify", "patch")):
            return "write"
        if any(k in name for k in ("read", "get", "list", "view", "query")):
            return "read_only"
        return None
