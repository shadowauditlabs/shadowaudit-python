"""OpenAI Agents SDK integration — CapFence tool wrapper.

Wraps OpenAI Agents SDK tools with deterministic runtime enforcement.

Usage:
    from agents import Agent, Tool
    from capfence.framework.openai_agents import CapFenceOpenAITool

    safe_shell = CapFenceOpenAITool(
        tool=ShellTool(),
        agent_id="ops-agent-1",
        risk_category="command_execution",
        gate=Gate(),  # optional
    )

    agent = Agent(
        name="OpsAgent",
        tools=[safe_shell],
    )
"""

from __future__ import annotations

from typing import Any, cast

from capfence.core.gate import Gate
from capfence.core.fsm import FailClosedFSM
from capfence.errors import AgentActionBlocked

__all__ = ["CapFenceOpenAITool", "AgentActionBlocked"]


class CapFenceOpenAITool:
    """Transparent wrapper adding deterministic gate enforcement to OpenAI Agents SDK tools.

    Mirrors the OpenAI Agents Tool interface for drop-in replacement.
    """

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

        # Mirror tool metadata
        self.name = getattr(tool, "name", "unknown_tool")
        self.description = getattr(tool, "description", "")
        self.params_json_schema = getattr(tool, "params_json_schema", {})

    async def on_invoke_tool(self, context: Any, input_json: str) -> str:
        """Intercept tool invocation and evaluate through Gate."""
        import json
        try:
            arguments = json.loads(input_json)
        except json.JSONDecodeError:
            arguments = {"raw_input": input_json}

        result = await self._gate.evaluate_async(
            agent_id=self._agent_id,
            task_context=self.name,
            risk_category=self._risk_category,
            payload=arguments,
            capability=self._capability,
            policy_path=self._policy_path,
        )
        outcome = self._fsm.transition(result)
        if outcome.decision != "pass":
            raise AgentActionBlocked(
                detail=f"Tool '{self.name}' blocked: {result.reason}",
                gate_result=result,
            )

        # Forward to underlying tool
        if hasattr(self._tool, "on_invoke_tool"):
            return cast(str, await self._tool.on_invoke_tool(context, input_json))
        elif hasattr(self._tool, "invoke"):
            return str(self._tool.invoke(arguments))
        else:
            raise AgentActionBlocked(detail=f"Tool '{self.name}' has no invoke method")

    def __getattr__(self, name: str) -> Any:
        """Transparent passthrough for tool attributes."""
        return getattr(self._tool, name)
