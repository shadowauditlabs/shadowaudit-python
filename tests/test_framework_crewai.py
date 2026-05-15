"""Tests for CrewAI framework adapter."""

import pytest

from capfence.framework.crewai import AgentActionBlocked, CapFenceCrewAITool
from capfence.core.gate import Gate


class MockCrewAITool:
    name = "mock_tool"
    description = "A mock tool for testing"

    def run(self, tool_input):
        return f"executed: {tool_input}"


class TestCapFenceCrewAITool:
    def test_passes_low_risk(self):
        tool = CapFenceCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="read_only",
            gate=Gate(),
        )
        result = tool.run("list files")
        assert result == "executed: list files"

    def test_blocks_high_risk(self):
        tool = CapFenceCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="delete",
            gate=Gate(),
        )
        with pytest.raises(AgentActionBlocked):
            tool.run("delete drop remove all records")

    def test_tool_attributes_mirrored(self):
        tool = CapFenceCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="read_only",
        )
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"

    def test_dict_input(self):
        tool = CapFenceCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="read_only",
            gate=Gate(),
        )
        result = tool.run({"input": "list files"})
        assert "executed" in result

    def test_error_detail_contains_reason(self):
        tool = CapFenceCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="delete",
            gate=Gate(),
        )
        with pytest.raises(AgentActionBlocked) as exc_info:
            tool.run("delete drop remove purge all records")
        assert exc_info.value.detail is not None
