"""Tests for async telemetry client."""

import asyncio

from capfence.telemetry.client import TelemetryClient


class TestTelemetryClient:
    def test_disabled_without_env(self):
        client = TelemetryClient(api_key="test-key")
        assert client.enabled is False

    def test_enabled_with_env(self, monkeypatch):
        monkeypatch.setenv("CAPFENCE_TELEMETRY", "1")
        client = TelemetryClient(api_key="test-key")
        assert client.enabled is True

    def test_send_decision_noop_when_disabled(self):
        client = TelemetryClient(api_key="test-key")
        # Should not raise
        asyncio.run(client.send_decision(
            agent_id="a", task_context="t", risk_category="r",
            decision="pass", risk_score=0.1, threshold=0.5,
            payload_hash="abc", latency_ms=5,
        ))

    def test_queue_drops_when_full(self, monkeypatch):
        monkeypatch.setenv("CAPFENCE_TELEMETRY", "1")
        client = TelemetryClient(api_key="test-key")
        client._queue = asyncio.Queue(maxsize=1)
        asyncio.run(client.send_decision(
            agent_id="a", task_context="t", risk_category="r",
            decision="pass", risk_score=0.1, threshold=0.5,
            payload_hash="abc", latency_ms=5,
        ))
        # Second item should be dropped
        asyncio.run(client.send_decision(
            agent_id="a", task_context="t", risk_category="r",
            decision="pass", risk_score=0.1, threshold=0.5,
            payload_hash="abc", latency_ms=5,
        ))
        assert client._queue.qsize() == 1
