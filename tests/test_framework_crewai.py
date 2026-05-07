"""Tests for CrewAI framework adapter."""

import pytest

from shadowaudit.framework.crewai import AgentActionBlocked, ShadowAuditCrewAITool
from shadowaudit.core.gate import Gate


class MockCrewAITool:
    name = "mock_tool"
    description = "A mock tool for testing"

    def run(self, tool_input):
        return f"executed: {tool_input}"


class TestShadowAuditCrewAITool:
    def test_passes_low_risk(self):
        tool = ShadowAuditCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="read_only",
            gate=Gate(),
        )
        result = tool.run("list files")
        assert result == "executed: list files"

    def test_blocks_high_risk(self):
        tool = ShadowAuditCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="delete",
            gate=Gate(),
        )
        with pytest.raises(AgentActionBlocked):
            tool.run("delete drop remove all records")

    def test_tool_attributes_mirrored(self):
        tool = ShadowAuditCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="read_only",
        )
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"

    def test_dict_input(self):
        tool = ShadowAuditCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="read_only",
            gate=Gate(),
        )
        result = tool.run({"input": "list files"})
        assert "executed" in result

    def test_error_detail_contains_reason(self):
        tool = ShadowAuditCrewAITool(
            tool=MockCrewAITool(),
            agent_id="crew-test",
            risk_category="delete",
            gate=Gate(),
        )
        with pytest.raises(AgentActionBlocked) as exc_info:
            tool.run("delete drop remove purge all records")
        assert exc_info.value.detail is not None
