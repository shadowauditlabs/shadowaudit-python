"""Example: Opt-in telemetry client (Week 13).

Demonstrates the async telemetry exporter for hashed decision metadata.
"""

import asyncio
import os
from capfence.telemetry.client import TelemetryClient


def main():
    print("Telemetry Client Demo")
    print("=" * 40)

    # Without env var — disabled by default
    client_disabled = TelemetryClient(api_key="test-key")
    print(f"Default state: enabled={client_disabled.enabled}")

    # Enable via environment variable
    os.environ["CAPFENCE_TELEMETRY"] = "1"
    client_enabled = TelemetryClient(api_key="test-key")
    print(f"With CAPFENCE_TELEMETRY=1: enabled={client_enabled.enabled}")

    # Simulate sending a decision
    if client_enabled.enabled:
        asyncio.run(client_enabled.send_decision(
            agent_id="demo-agent",
            task_context="shell_tool",
            risk_category="execute",
            decision="block",
            risk_score=0.85,
            threshold=0.2,
            payload_hash="abc123def456",
            latency_ms=5,
        ))
        print("Decision queued for telemetry export")

    # Cleanup
    del os.environ["CAPFENCE_TELEMETRY"]

    print("\nNote: Telemetry is opt-in. Set CAPFENCE_TELEMETRY=1 to enable.")
    print("Only hashed metadata is sent — no raw payloads leave your system.")


if __name__ == "__main__":
    main()
