"""Tests for TraceSimulator."""

import json


from capfence.assessment.simulator import TraceSimulator


class TestTraceSimulator:
    def test_simulate_basic(self, tmp_path):
        trace_file = tmp_path / "trace.jsonl"
        trace_file.write_text(
            "\n".join([
                json.dumps({"call_id": "1", "tool_name": "ReadTool", "payload": {"action": "view"}, "risk_category": "read_only"}),
                json.dumps({"call_id": "2", "tool_name": "DeleteTool", "payload": {"action": "destroy"}, "risk_category": "delete"}),
            ]) + "\n"
        )

        sim = TraceSimulator(taxonomy_path="general")
        summary = sim.run(trace_file, agent_id="test-agent")

        assert summary.total_calls == 2
        assert summary.static_blocked >= 0

    def test_simulate_with_adaptive_gap(self, tmp_path):
        trace_file = tmp_path / "trace.jsonl"
        calls = []
        for i in range(5):
            calls.append(json.dumps({
                "call_id": str(i),
                "tool_name": "PaymentTool",
                "payload": {"action": "pay"},
                "risk_category": "payment_initiation",
            }))
        trace_file.write_text("\n".join(calls) + "\n")

        sim = TraceSimulator(taxonomy_path="general")
        summary = sim.run(trace_file, agent_id="test-agent", verbose=True)

        assert summary.total_calls == 5
        assert summary.adaptive_blocked >= summary.static_blocked

    def test_empty_trace(self, tmp_path):
        trace_file = tmp_path / "trace.jsonl"
        trace_file.write_text("")

        sim = TraceSimulator()
        summary = sim.run(trace_file)

        assert summary.total_calls == 0
        assert summary.recommendation != ""

    def test_invalid_json_lines_skipped(self, tmp_path):
        trace_file = tmp_path / "trace.jsonl"
        trace_file.write_text(
            "\n".join([
                json.dumps({"call_id": "1", "tool_name": "ReadTool", "payload": {}, "risk_category": "read_only"}),
                "not valid json",
                json.dumps({"call_id": "2", "tool_name": "ReadTool", "payload": {}, "risk_category": "read_only"}),
            ]) + "\n"
        )

        sim = TraceSimulator()
        summary = sim.run(trace_file)
        assert summary.total_calls == 2

    def test_compare_mode_verbose(self, tmp_path):
        trace_file = tmp_path / "trace.jsonl"
        trace_file.write_text(
            json.dumps({
                "call_id": "1", "tool_name": "ReadTool", "payload": {"action": "view"}, "risk_category": "read_only"
            }) + "\n"
        )

        sim = TraceSimulator()
        summary = sim.run(trace_file, verbose=True)
        assert summary.total_calls == 1
