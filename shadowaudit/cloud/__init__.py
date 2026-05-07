"""Cloud client for optional remote threshold scoring.

Works with or without an API key. Gracefully falls back to local rule-based
gating when offline, unauthorized, or rate-limited.
"""

from shadowaudit.cloud.client import CloudClient

__all__ = ["CloudClient"]
