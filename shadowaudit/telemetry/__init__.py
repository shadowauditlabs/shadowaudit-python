"""Async telemetry client for opt-in hashed metadata export.

Sends anonymized decision metadata to the ShadowAudit Cloud API.
Zero payload data leaves the local machine — only hashes, scores,
and category names are transmitted.
"""

from shadowaudit.telemetry.client import TelemetryClient

__all__ = ["TelemetryClient"]
