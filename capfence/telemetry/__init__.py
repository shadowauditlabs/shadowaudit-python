"""Async telemetry client for opt-in hashed metadata export.

Sends anonymized decision metadata to the CapFence Cloud API.
Zero payload data leaves the local machine — only hashes, scores,
and category names are transmitted.
"""

from capfence.telemetry.client import TelemetryClient

__all__ = ["TelemetryClient"]
