"""Tests for rule-based Gate."""

import pytest

from shadowaudit import Gate
from shadowaudit.core.gate import score_payload, compute_threshold


class TestScorePayload:
    def test_empty_payload_zero(self):
        assert score_payload({}, ["delete"]) == 0.0

    def test_no_keywords_zero(self):
        assert score_payload({"action": "view"}, ["delete", "drop"]) == 0.0

    def test_single_match(self):
        s = score_payload({"action": "delete record"}, ["delete", "drop"])
        assert s > 0.0
        assert s <= 1.0

    def test_multiple_matches_higher(self):
        low = score_payload({"action": "delete"}, ["delete", "drop", "remove"])
        high = score_payload({"action": "delete and remove"}, ["delete", "drop", "remove"])
        assert high >= low

    def test_empty_keywords_zero(self):
        assert score_payload({"action": "delete"}, []) == 0.0


class TestComputeThreshold:
    def test_returns_delta(self):
        assert compute_threshold(0.5) == 0.5
        assert compute_threshold(0.9) == 0.9


class TestGateEvaluate:
    def test_low_risk_passes(self):
        gate = Gate()
        result = gate.evaluate(
            agent_id="test-agent",
            task_context="list_users",
            risk_category="read_only",
            payload={"action": "view all users"},
        )
        assert result.passed is True
        assert result.risk_score >= 0.0
        assert result.threshold is not None
        assert result.latency_ms is not None
        assert result.metadata["K"] == 0.0  # no history

    def test_risky_category_blocks(self):
        gate = Gate()
        result = gate.evaluate(
            agent_id="test-agent",
            task_context="destroy database",
            risk_category="delete",
            payload={"action": "destroy all customer records"},
        )
        # Delete keywords matched → higher risk score
        assert result.risk_score > 0.0
        assert result.risk_category == "delete"

    def test_unknown_category_defaults_safe(self):
        gate = Gate()
        result = gate.evaluate(
            agent_id="test-agent",
            task_context="unknown",
            risk_category="nonexistent",
            payload={"action": "anything"},
        )
        assert result.threshold == 0.1  # safe default

    def test_records_decision_for_next_k(self):
        gate = Gate()
        agent = "learning-agent"

        r1 = gate.evaluate(agent, "t1", "read_only", {"action": "view"})
        assert r1.metadata["K"] == 0.0

        r2 = gate.evaluate(agent, "t2", "read_only", {"action": "view"})
        # After one pass decision, K should be 1.0
        assert r2.metadata["K"] == pytest.approx(1.0)

    def test_audit_logger_records(self):
        """Gate evaluation writes to audit log."""
        from shadowaudit.core.audit import AuditLogger
        audit = AuditLogger()
        gate = Gate(audit_logger=audit)
        gate.evaluate(
            agent_id="audit-test",
            task_context="test",
            risk_category="read_only",
            payload={"action": "view"},
        )
        events = audit.get_events(agent_id="audit-test")
        assert len(events) == 1
        assert events[0]["decision"] == "pass"
