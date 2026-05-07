"""Cloud client for optional remote threshold scoring.

Implements a resilient client that:
1. Attempts remote API for threshold computation
2. Falls back to local rule-based gating on any failure
3. Respects rate limits and offline environments
4. Works without an API key (local-only mode)
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class CloudClient:
    """Optional cloud client with graceful offline fallback.

    Usage:
        client = CloudClient(api_key=os.getenv("SHADOWAUDIT_API_KEY"))
        gate = Gate(cloud_client=client)

    Without API key or network, the client silently falls back
    to local rule-based gating. No exception raised.
    """

    DEFAULT_BASE_URL = "https://api.shadowaudit.io/v1"
    TIMEOUT_SECONDS = 3

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key or os.getenv("SHADOWAUDIT_API_KEY")
        self._base_url = (base_url or os.getenv("SHADOWAUDIT_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._last_error: str | None = None
        self._offline_mode = self._api_key is None

    @property
    def offline_mode(self) -> bool:
        """True if no API key is configured."""
        return self._offline_mode

    @property
    def last_error(self) -> str | None:
        """Last cloud error message, if any."""
        return self._last_error

    def get_threshold(
        self,
        *,
        K: float,
        V: float,
        delta: float,
    ) -> float:
        """Request adaptive threshold from cloud API.

        Falls back to local delta on any failure.
        """
        if self._offline_mode:
            self._last_error = None
            return delta

        payload = json.dumps({
            "K": K,
            "V": V,
            "delta": delta,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self._base_url}/threshold",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "shadowaudit-sdk/0.3.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._last_error = None
                return float(data.get("threshold", delta))
        except urllib.error.HTTPError as e:
            self._last_error = f"HTTP {e.code}: {e.reason}"
            return delta
        except urllib.error.URLError as e:
            self._last_error = f"Network error: {e.reason}"
            return delta
        except Exception as e:
            self._last_error = f"Unexpected: {type(e).__name__}: {e}"
            return delta

    def evaluate(
        self,
        *,
        agent_id: str,
        task_context: str,
        risk_category: str | None,
        payload: dict[str, Any],
        local_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Send evaluation to cloud for behavioral intelligence and audit trail.

        Fire-and-forget: returns immediately, does not block gate decision.
        Falls back silently on any error.
        """
        if self._offline_mode:
            return local_result

        body = json.dumps({
            "agent_id": agent_id,
            "task_context": task_context,
            "risk_category": risk_category,
            "payload_hash": local_result.get("metadata", {}).get("payload_hash"),
            "risk_score": local_result.get("risk_score"),
            "threshold": local_result.get("threshold"),
            "passed": local_result.get("passed"),
            "timestamp": time.time(),
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self._base_url}/evaluate",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "shadowaudit-sdk/0.3.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout):
                pass
        except Exception:
            pass  # Fire-and-forget: never fail the gate

        return local_result

