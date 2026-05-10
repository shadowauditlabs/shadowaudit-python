"""Tests for Gate observe mode, bypass context manager, and confidence metadata."""
import pytest
from shadowaudit.core.gate import Gate, GATE_MODE_OBSERVE, GATE_MODE_ENFORCE


RISKY_PAYLOAD = {
    "action": "create_payout",
    "disburse": True,
    "amount": 95000,
    "payout": True,
    "transfer_to_bank": True,
}


def test_enforce_mode_blocks_risky_payload():
    gate = Gate(taxonomy_path="financial")
    result = gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    assert not result.passed
    assert result.metadata["gate_mode"] == GATE_MODE_ENFORCE


def test_observe_mode_never_blocks():
    gate = Gate(taxonomy_path="financial", mode=GATE_MODE_OBSERVE)
    result = gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    assert result.passed
    assert result.metadata["gate_mode"] == GATE_MODE_OBSERVE
    assert result.metadata["would_have_blocked"] is True


def test_observe_mode_passes_benign():
    gate = Gate(taxonomy_path="financial", mode=GATE_MODE_OBSERVE)
    result = gate.evaluate("a1", "balance", "balance_inquiry", {"account": "acct_1"})
    assert result.passed
    assert result.metadata.get("would_have_blocked") is False


def test_invalid_mode_raises():
    with pytest.raises(ValueError, match="Invalid gate mode"):
        Gate(mode="stealth")


def test_bypass_overrides_block():
    gate = Gate(taxonomy_path="financial")
    with gate.bypass("a1", reason="approved by oncall #1234"):
        result = gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    assert result.passed
    assert "approved by oncall #1234" in result.metadata["bypass_reason"]
    assert result.metadata["would_have_blocked"] is True


def test_bypass_requires_reason():
    gate = Gate()
    with pytest.raises(ValueError, match="non-empty reason"):
        with gate.bypass("a1", reason=""):
            pass


def test_bypass_is_scoped_to_context():
    gate = Gate(taxonomy_path="financial")
    with gate.bypass("a1", reason="override"):
        result_in = gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    result_out = gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    assert result_in.passed
    assert not result_out.passed


def test_bypass_scoped_to_agent():
    gate = Gate(taxonomy_path="financial")
    with gate.bypass("agent-allowed", reason="approved"):
        r1 = gate.evaluate("agent-allowed", "payout", "stripe_payout", RISKY_PAYLOAD)
        r2 = gate.evaluate("agent-blocked", "payout", "stripe_payout", RISKY_PAYLOAD)
    assert r1.passed
    assert not r2.passed


def test_confidence_in_metadata():
    gate = Gate(taxonomy_path="financial")
    result = gate.evaluate("a1", "balance", "balance_inquiry", {"account": "acct_1"})
    assert "confidence" in result.metadata
    assert 0.0 <= result.metadata["confidence"] <= 1.0


def test_observe_mode_reason_string():
    gate = Gate(taxonomy_path="financial", mode=GATE_MODE_OBSERVE)
    result = gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    assert result.reason == "observed"


def test_bypass_reason_in_audit_log():
    from shadowaudit.core.audit import AuditLogger
    audit = AuditLogger()
    gate = Gate(taxonomy_path="financial", audit_logger=audit)
    with gate.bypass("a1", reason="emergency override"):
        gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    events = audit.get_events(agent_id="a1")
    assert len(events) == 1
    assert events[0]["decision"] == "pass"  # bypass forced pass
