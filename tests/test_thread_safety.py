"""Concurrency smoke tests for Gate.bypass and FlowTracer."""
import threading

from shadowaudit.core.gate import Gate
from shadowaudit.flow.tracer import FlowTracer, TrustLevel


RISKY_PAYLOAD = {
    "action": "create_payout",
    "disburse": True,
    "amount": 95000,
    "payout": True,
    "transfer_to_bank": True,
}


def test_bypass_stack_concurrent_agents():
    """Two threads bypassing different agents should not corrupt each other's stack."""
    gate = Gate(taxonomy_path="financial")
    errors: list[str] = []

    def run_agent(agent_id: str, reason: str) -> None:
        try:
            for _ in range(50):
                with gate.bypass(agent_id, reason=reason):
                    r = gate.evaluate(agent_id, "payout", "stripe_payout", RISKY_PAYLOAD)
                    if not r.passed:
                        errors.append(f"{agent_id}: bypass failed to override")
        except Exception as e:
            errors.append(f"{agent_id}: {type(e).__name__}: {e}")

    threads = [
        threading.Thread(target=run_agent, args=(f"agent-{i}", f"reason-{i}"))
        for i in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"bypass corruption under concurrency: {errors}"
    # After all threads exit, no bypasses should remain active
    assert gate._bypass_stack == {}


def test_flow_tracer_concurrent_writes():
    """Concurrent record_output calls should not corrupt internal state."""
    tracer = FlowTracer()
    errors: list[str] = []

    def writer(agent_id: str, count: int) -> None:
        try:
            for i in range(count):
                tracer.record_output(agent_id, {"i": i}, TrustLevel.INTERNAL)
        except Exception as e:
            errors.append(f"{agent_id}: {type(e).__name__}: {e}")

    threads = [
        threading.Thread(target=writer, args=(f"agent-{i}", 100))
        for i in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"FlowTracer corruption under concurrency: {errors}"
    summary = tracer.flow_summary()
    assert summary["total_flows"] == 400
    assert len(summary["agents"]) == 4


def test_flow_tracer_concurrent_annotate_and_record():
    """Reads (annotate) interleaved with writes (record_output) should not crash."""
    tracer = FlowTracer()
    errors: list[str] = []

    def writer() -> None:
        try:
            for i in range(200):
                tracer.record_output("scraper", {"i": i}, TrustLevel.UNTRUSTED)
        except Exception as e:
            errors.append(f"writer: {e}")

    def reader() -> None:
        try:
            for _ in range(200):
                tracer.annotate(
                    receiving_agent="payment-agent",
                    source_agents=["scraper"],
                    declared_trust=TrustLevel.SYSTEM,
                )
        except Exception as e:
            errors.append(f"reader: {e}")

    t1 = threading.Thread(target=writer)
    t2 = threading.Thread(target=reader)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"FlowTracer read/write race: {errors}"
