"""LangGraph integration — ShadowAudit node wrapper.

Wraps LangGraph tool nodes with deterministic runtime enforcement.

Usage:
    from langgraph.prebuilt import ToolNode
    from shadowaudit.framework.langgraph import ShadowAuditToolNode

    safe_node = ShadowAuditToolNode(
        tools=[shell_tool, payment_tool],
        agent_id="ops-agent-1",
        gate=Gate(),  # optional
    )

    # Use in a StateGraph
    graph.add_node("tools", safe_node)
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


class ShadowAuditToolNode:
    """Wraps a LangGraph ToolNode with ShadowAudit gate enforcement.

    Mirrors the LangGraph ToolNode interface for drop-in replacement.
    """

    def __init__(
        self,
        tools: list[Any],
        agent_id: str,
        gate: Gate | None = None,
        risk_category_map: dict[str, str] | None = None,
    ) -> None:
        self._tools = {t.name: t for t in tools}
        self._agent_id = agent_id
        self._gate = gate or Gate()
        self._fsm = FailClosedFSM()
        self._risk_category_map = risk_category_map or {}

    def _get_risk_category(self, tool_name: str) -> str | None:
        """Look up risk category for a tool name."""
        if tool_name in self._risk_category_map:
            return self._risk_category_map[tool_name]
        # Heuristic fallback
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

    def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute tool calls from state['messages'] with gating."""
        messages = state.get("messages", [])
        tool_calls: list[dict[str, Any]] = []
        for msg in messages:
            if hasattr(msg, "tool_calls"):
                tool_calls.extend(msg.tool_calls)
            elif isinstance(msg, dict) and "tool_calls" in msg:
                tool_calls.extend(msg["tool_calls"])

        results: list[Any] = []
        for call in tool_calls:
            tool_name = call.get("name", call.get("function", {}).get("name", "unknown"))
            arguments = call.get("args", call.get("arguments", {}))
            call_id = call.get("id", "unknown")

            risk_category = self._get_risk_category(tool_name)
            result = self._gate.evaluate(
                agent_id=self._agent_id,
                task_context=tool_name,
                risk_category=risk_category,
                payload=arguments,
            )
            outcome = self._fsm.transition(result)
            if outcome.decision != "pass":
                raise AgentActionBlocked(
                    detail=f"Tool '{tool_name}' blocked: {result.reason}",
                    gate_result=result,
                )

            tool = self._tools.get(tool_name)
            if tool is None:
                raise AgentActionBlocked(detail=f"Tool '{tool_name}' not found")
            tool_result = tool.invoke(arguments)
            results.append({"call_id": call_id, "tool_name": tool_name, "result": tool_result})

        return {**state, "tool_results": results}
