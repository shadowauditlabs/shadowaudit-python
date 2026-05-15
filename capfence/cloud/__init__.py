"""Cloud client for optional remote threshold scoring.

Works with or without an API key. Gracefully falls back to local rule-based
gating when offline, unauthorized, or rate-limited.
"""

from capfence.cloud.client import CloudClient
from capfence.cloud.evaluator import CloudInterceptor, RemoteEvaluator

__all__ = ["CloudClient", "CloudInterceptor", "RemoteEvaluator"]
