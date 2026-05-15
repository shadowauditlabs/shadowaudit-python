"""Tests for OpenAI Agents adapter."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("pytest_asyncio", reason="pytest-asyncio not installed")

from capfence.core.gate import Gate
from capfence.core.fsm import FailClosedFSM
from capfence.types import GateResult
from capfence.framework.openai_agents import CapFenceOpenAITool, AgentActionBlocked


class MockOpenAITool:
    """Mock OpenAI Agents SDK tool."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.params_json_schema = {}

    async def on_invoke_tool(self, context, input_json: str) -> str:
        return f"invoked {self.name} with {input_json}"

    def invoke(self, arguments: dict) -> str:
        return f"invoked {self.name} with {arguments}"


class TestCapFenceOpenAITool:
    """Tests for CapFenceOpenAITool."""

    def test_init_defaults(self):
        tool = MockOpenAITool("read_tool")
        wrapped = CapFenceOpenAITool(tool=tool, agent_id="agent-1")
        assert wrapped.name == "read_tool"
        assert wrapped._agent_id == "agent-1"
        assert wrapped._risk_category is None
        assert isinstance(wrapped._gate, Gate)
        assert isinstance(wrapped._fsm, FailClosedFSM)

    def test_init_custom(self):
        gate = Gate()
        tool = MockOpenAITool("shell")
        wrapped = CapFenceOpenAITool(
            tool=tool,
            agent_id="agent-1",
            risk_category="execute",
            gate=gate,
        )
        assert wrapped._risk_category == "execute"
        assert wrapped._gate is gate

    def test_init_mirrors_metadata(self):
        tool = MockOpenAITool("payment", "Process payments")
        tool.params_json_schema = {"type": "object"}
        wrapped = CapFenceOpenAITool(tool=tool, agent_id="agent-1")
        assert wrapped.name == "payment"
        assert wrapped.description == "Process payments"
        assert wrapped.params_json_schema == {"type": "object"}

    def test_init_unknown_tool_defaults(self):
        """Tool without name/description gets defaults."""

        class BareTool:
            pass

        wrapped = CapFenceOpenAITool(tool=BareTool(), agent_id="agent-1")
        assert wrapped.name == "unknown_tool"
        assert wrapped.description == ""
        assert wrapped.params_json_schema == {}

    @pytest.mark.asyncio
    async def test_on_invoke_tool_passes_safe(self):
        tool = MockOpenAITool("read_tool")
        wrapped = CapFenceOpenAITool(tool=tool, agent_id="agent-1")
        result = await wrapped.on_invoke_tool(None, json.dumps({"query": "test"}))
        assert "read_tool" in result

    @pytest.mark.asyncio
    async def test_on_invoke_tool_blocks_high_risk(self):
        tool = MockOpenAITool("shell")
        wrapped = CapFenceOpenAITool(
            tool=tool,
            agent_id="agent-1",
            risk_category="execute",
        )
        with pytest.raises(AgentActionBlocked):
            await wrapped.on_invoke_tool(None, json.dumps({"command": "exec rm -rf /"}))

    @pytest.mark.asyncio
    async def test_on_invoke_tool_invalid_json(self):
        tool = MockOpenAITool("read_tool")
        wrapped = CapFenceOpenAITool(tool=tool, agent_id="agent-1")
        result = await wrapped.on_invoke_tool(None, "not json")
        assert "read_tool" in result

    @pytest.mark.asyncio
    async def test_on_invoke_tool_fallback_invoke(self):
        """Tool without on_invoke_tool falls back to invoke."""

        class InvokeOnlyTool:
            name = "simple"
            description = ""
            params_json_schema = {}

            def invoke(self, arguments: dict) -> str:
                return f"invoked with {arguments}"

        wrapped = CapFenceOpenAITool(tool=InvokeOnlyTool(), agent_id="agent-1")
        result = await wrapped.on_invoke_tool(None, json.dumps({"key": "val"}))
        assert "invoked" in result

    @pytest.mark.asyncio
    async def test_on_invoke_tool_no_method_raises(self):
        """Tool with no invoke method raises."""

        class NoMethodTool:
            name = "broken"
            description = ""
            params_json_schema = {}

        wrapped = CapFenceOpenAITool(tool=NoMethodTool(), agent_id="agent-1")
        with pytest.raises(AgentActionBlocked):
            await wrapped.on_invoke_tool(None, json.dumps({}))

    def test_getattr_passthrough(self):
        tool = MockOpenAITool("read_tool")
        wrapped = CapFenceOpenAITool(tool=tool, agent_id="agent-1")
        assert wrapped.name == "read_tool"
        assert wrapped.description == ""

    def test_agent_action_blocked_exception(self):
        result = GateResult(passed=False, reason="test")
        exc = AgentActionBlocked(detail="blocked", gate_result=result)
        assert exc.detail == "blocked"
        assert exc.gate_result is result
        assert str(exc) == "blocked"
