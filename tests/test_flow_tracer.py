"""Tests for multi-agent FlowTracer and trust propagation."""
from capfence.flow.tracer import FlowTracer, TrustLevel


def test_trust_levels_ordered():
    assert TrustLevel.UNTRUSTED < TrustLevel.EXTERNAL
    assert TrustLevel.EXTERNAL < TrustLevel.INTERNAL
    assert TrustLevel.INTERNAL < TrustLevel.SYSTEM


def test_record_output_tracks_min_trust():
    tracer = FlowTracer()
    tracer.record_output("agent-a", {"data": 1}, TrustLevel.UNTRUSTED)
    assert tracer.get_agent_trust("agent-a") == TrustLevel.UNTRUSTED


def test_record_output_min_trust_is_lowest():
    tracer = FlowTracer()
    tracer.record_output("agent-a", {"data": 1}, TrustLevel.SYSTEM)
    tracer.record_output("agent-a", {"data": 2}, TrustLevel.UNTRUSTED)
    tracer.record_output("agent-a", {"data": 3}, TrustLevel.INTERNAL)
    assert tracer.get_agent_trust("agent-a") == TrustLevel.UNTRUSTED


def test_flow_propagates_trust():
    tracer = FlowTracer()
    tracer.record_output("scraper", {"page": "..."}, TrustLevel.UNTRUSTED)
    tracer.record_flow("scraper", "parser", {"parsed": "..."})
    assert tracer.get_agent_trust("parser") == TrustLevel.UNTRUSTED


def test_annotate_propagates_untrusted():
    tracer = FlowTracer()
    tracer.record_output("web-scraper", {"content": "evil"}, TrustLevel.UNTRUSTED)
    tracer.record_flow("web-scraper", "summariser", {"text": "evil"})

    annotation = tracer.annotate(
        receiving_agent="payment-agent",
        source_agents=["summariser"],
        declared_trust=TrustLevel.SYSTEM,
    )
    assert annotation.effective_trust == TrustLevel.UNTRUSTED
    assert "summariser" in annotation.contaminated_by


def test_annotate_clean_chain_preserves_declared_trust():
    # annotate() only lowers trust, never raises it.
    # A declared INTERNAL agent stays INTERNAL even if its data source is SYSTEM.
    tracer = FlowTracer()
    tracer.record_output("internal-db", {"balance": 1000}, TrustLevel.SYSTEM)
    tracer.record_flow("internal-db", "risk-scorer", {"balance": 1000})

    annotation = tracer.annotate(
        receiving_agent="payment-agent",
        source_agents=["risk-scorer"],
        declared_trust=TrustLevel.INTERNAL,
    )
    assert annotation.effective_trust == TrustLevel.INTERNAL  # not elevated to SYSTEM
    assert annotation.contaminated_by == []


def test_annotate_mixed_sources():
    tracer = FlowTracer()
    tracer.record_output("trusted-source", {"data": "ok"}, TrustLevel.SYSTEM)
    tracer.record_output("untrusted-source", {"data": "evil"}, TrustLevel.UNTRUSTED)

    annotation = tracer.annotate(
        receiving_agent="tool-user",
        source_agents=["trusted-source", "untrusted-source"],
        declared_trust=TrustLevel.SYSTEM,
    )
    assert annotation.effective_trust == TrustLevel.UNTRUSTED
    assert "untrusted-source" in annotation.contaminated_by


def test_flow_summary():
    tracer = FlowTracer()
    tracer.record_output("a1", {"x": 1}, TrustLevel.INTERNAL)
    tracer.record_flow("a1", "a2", {"y": 2})
    summary = tracer.flow_summary()
    assert summary["total_flows"] == 2
    assert "a1" in summary["agents"]
    assert "a2" in summary["agents"]


def test_reset_clears_state():
    tracer = FlowTracer()
    tracer.record_output("agent", {"data": 1}, TrustLevel.UNTRUSTED)
    tracer.reset()
    assert tracer.get_agent_trust("agent") == TrustLevel.INTERNAL
    assert tracer.flow_summary()["total_flows"] == 0


def test_flow_inherits_trust_without_explicit():
    tracer = FlowTracer()
    tracer.record_output("source", {"d": 1}, TrustLevel.EXTERNAL)
    edge = tracer.record_flow("source", "dest", {"d": 2})
    assert edge.trust == TrustLevel.EXTERNAL
