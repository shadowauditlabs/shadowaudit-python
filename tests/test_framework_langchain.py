"""Tests for LangChain CapFenceTool wrapper."""

import pytest

from capfence.framework.langchain import CapFenceTool, AgentActionBlocked


class MockTool:
    """Simple mock tool for testing."""
    name = "mock"
    description = "Mock tool"

    def run(self, tool_input, **kwargs):
        return f"result: {tool_input}"


class TestCapFenceTool:
    def test_passes_allows_execution(self):
        tool = CapFenceTool(
            tool=MockTool(),
            agent_id="test-agent",
            risk_category="read_only",  # low risk, should pass
        )
        result = tool.run("view dashboard")
        assert "result:" in result

    def test_blocks_on_risk(self):
        tool = CapFenceTool(
            tool=MockTool(),
            agent_id="test-agent",
            risk_category="delete",  # risky keywords in input
        )
        with pytest.raises(AgentActionBlocked) as exc_info:
            tool.run("delete all records and drop tables")

        assert "BLOCKED" in str(exc_info.value) or "blocked" in exc_info.value.detail.lower()
        assert exc_info.value.gate_result is not None

    def test_preserves_tool_attributes(self):
        tool = CapFenceTool(tool=MockTool(), agent_id="test", risk_category="read_only")
        assert tool.name == "mock"
        assert tool.description == "Mock tool"

    def test_metadata_in_exception(self):
        tool = CapFenceTool(
            tool=MockTool(),
            agent_id="test-agent",
            risk_category="execute",  # risky: execute, run, exec
        )
        with pytest.raises(AgentActionBlocked) as exc_info:
            tool.run("execute rm -rf /")

        assert exc_info.value.gate_result is not None
        assert exc_info.value.gate_result.metadata is not None
        assert "K" in exc_info.value.gate_result.metadata


class TestGuardDecorator:
    def test_decorator_blocks(self):
        from capfence.framework.langchain import capfence_guard

        @capfence_guard(agent_id="test-agent", risk_category="delete")
        def risky_delete(id: str) -> str:
            return f"deleted {id}"

        with pytest.raises(AgentActionBlocked):
            risky_delete("delete drop remove all records")

    def test_decorator_allows(self):
        from capfence.framework.langchain import capfence_guard

        @capfence_guard(agent_id="test-agent", risk_category="read_only")
        def safe_view(id: str) -> str:
            return f"viewed {id}"

        result = safe_view("record-123")
        assert result == "viewed record-123"
