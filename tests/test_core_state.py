"""Tests for SQLite-backed AgentStateStore."""

import pytest

from capfence.core.state import AgentStateStore


class TestKComputation:
    def test_new_agent_zero(self):
        store = AgentStateStore()
        assert store.compute_K("new-agent") == 0.0

    def test_perfect_history(self):
        store = AgentStateStore()
        store.record_decision("perfect", True)
        store.record_decision("perfect", True)
        store.record_decision("perfect", True)
        assert store.compute_K("perfect") == 1.0

    def test_mixed_history(self):
        store = AgentStateStore()
        store.record_decision("mixed", True)
        store.record_decision("mixed", False)
        store.record_decision("mixed", True)
        store.record_decision("mixed", False)
        assert store.compute_K("mixed") == pytest.approx(0.5)

    def test_all_fails_zero(self):
        store = AgentStateStore()
        store.record_decision("fails", False)
        store.record_decision("fails", False)
        assert store.compute_K("fails") == 0.0


class TestVComputation:
    def test_no_traffic_clamped(self):
        store = AgentStateStore()
        assert store.compute_V("no-traffic") == 1.0

    def test_high_traffic(self):
        store = AgentStateStore()
        for _ in range(50):
            store.record_decision("high", True)
        v = store.compute_V("high")
        assert v >= 50


class TestPersistence:
    def test_history_retrieval(self):
        store = AgentStateStore()
        store.record_decision("agent-1", True, payload_hash="abc123")
        store.record_decision("agent-1", False, payload_hash="def456")
        history = store.get_history("agent-1")
        assert len(history) == 2
        # get_history returns DESC order (most recent first)
        assert history[0]["passed"] is False
        assert history[1]["passed"] is True
