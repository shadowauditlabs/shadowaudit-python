"""Tests for the unified exception hierarchy."""
import pytest

import shadowaudit
from shadowaudit.errors import (
    AgentActionBlocked,
    ConfigurationError,
    ShadowAuditError,
)
from shadowaudit.framework.langchain import AgentActionBlocked as LCBlocked
from shadowaudit.framework.crewai import AgentActionBlocked as CrewBlocked
from shadowaudit.framework.langgraph import AgentActionBlocked as LGBlocked
from shadowaudit.framework.openai_agents import AgentActionBlocked as OAIBlocked
from shadowaudit.mcp.adapter import AgentActionBlocked as MCPBlocked


def test_version_exposed():
    assert isinstance(shadowaudit.__version__, str)
    assert shadowaudit.__version__.count(".") >= 1


def test_all_framework_agent_blocked_is_same_class():
    """A user catching shadowaudit.AgentActionBlocked must catch every adapter's block."""
    assert LCBlocked is AgentActionBlocked
    assert CrewBlocked is AgentActionBlocked
    assert LGBlocked is AgentActionBlocked
    assert OAIBlocked is AgentActionBlocked
    assert MCPBlocked is AgentActionBlocked
    assert shadowaudit.AgentActionBlocked is AgentActionBlocked


def test_agent_blocked_inherits_shadowaudit_error():
    exc = AgentActionBlocked(detail="blocked")
    assert isinstance(exc, ShadowAuditError)


def test_configuration_error_keeps_value_error_compat():
    """Existing code that catches ValueError on bad config must keep working."""
    err = ConfigurationError("bad mode")
    assert isinstance(err, ValueError)
    assert isinstance(err, ShadowAuditError)


def test_bad_gate_mode_raises_configuration_error():
    from shadowaudit.core.gate import Gate
    with pytest.raises(ConfigurationError):
        Gate(mode="stealth")
    # Backward compat: also catchable as ValueError
    with pytest.raises(ValueError):
        Gate(mode="stealth")


def test_empty_bypass_reason_raises_configuration_error():
    from shadowaudit.core.gate import Gate
    gate = Gate()
    with pytest.raises(ConfigurationError):
        with gate.bypass("a1", reason=""):
            pass


def test_agent_blocked_carries_detail_and_result():
    exc = AgentActionBlocked(detail="payout too large")
    assert exc.detail == "payout too large"
    assert exc.gate_result is None
    assert str(exc) == "payout too large"
