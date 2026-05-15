"""Tests for fail-closed FSM."""


from capfence.core.fsm import FailClosedFSM
from capfence.types import GateResult


class TestFSMTransition:
    def test_pass_returns_200(self):
        result = GateResult(passed=True, risk_score=0.1, threshold=0.5)
        outcome = FailClosedFSM.transition(result)
        assert outcome.decision == "pass"
        assert outcome.detail == "Execution authorized"
        assert outcome.gate_result is result

    def test_drift_returns_fail_drift(self):
        result = GateResult(passed=False, reason="drift_detected", risk_score=0.9, threshold=0.5)
        outcome = FailClosedFSM.transition(result)
        assert outcome.decision == "fail_drift"
        assert "drift" in outcome.detail.lower()

    def test_latency_returns_fail_latency(self):
        result = GateResult(passed=False, reason="latency_budget_exceeded")
        outcome = FailClosedFSM.transition(result)
        assert outcome.decision == "fail_latency"
        assert "latency" in outcome.detail.lower()

    def test_tamper_returns_fail_tamper(self):
        result = GateResult(passed=False, reason="payload_tamper_detected")
        outcome = FailClosedFSM.transition(result)
        assert outcome.decision == "fail_tamper"

    def test_unknown_returns_fail_error(self):
        result = GateResult(passed=False, reason="something_bad")
        outcome = FailClosedFSM.transition(result)
        assert outcome.decision == "fail_error"


class TestFSMDeterminism:
    def test_same_input_same_output(self):
        result = GateResult(passed=False, reason="drift_detected")
        o1 = FailClosedFSM.transition(result)
        o2 = FailClosedFSM.transition(result)
        assert o1.decision == o2.decision
        assert o1.detail == o2.detail

    def test_no_mutable_state(self):
        fsm = FailClosedFSM()
        r1 = GateResult(passed=True)
        r2 = GateResult(passed=False, reason="drift_detected")
        o1 = fsm.transition(r1)
        o2 = fsm.transition(r2)
        assert o1.decision == "pass"
        assert o2.decision == "fail_drift"
