"""The Telemetry Bridge (CloudInterceptor) and RemoteEvaluator for W13."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, cast

class RemoteEvaluator:
    """Evaluates telemetry remotely on the Cloud endpoint."""
    
    DEFAULT_BASE_URL = "https://api.shadowaudit.io/v1"
    
    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 1.5):
        self.base_url = (base_url or os.getenv("SHADOWAUDIT_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self.api_key = api_key or os.getenv("SHADOWAUDIT_API_KEY")
        self.timeout = timeout
        
    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send hashed tool-call metadata to the /evaluate endpoint."""
        if not self.api_key:
            return {"status": "offline"}
            
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "shadowaudit-sdk/0.4.0",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        req = urllib.request.Request(
            f"{self.base_url}/evaluate",
            data=body,
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return cast(dict[str, Any], json.loads(resp.read().decode("utf-8")))
        except Exception as e:
            return {"status": "error", "reason": str(e)}

class CloudInterceptor:
    """The Telemetry Bridge that wraps RemoteEvaluator."""
    
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 1.5):
        self.evaluator = RemoteEvaluator(base_url=base_url, api_key=api_key, timeout=timeout)
        self.offline_mode = not bool(self.evaluator.api_key)
        
    def get_threshold(self, *, K: float, V: float, delta: float) -> float:
        """Fetch adaptive threshold from cloud API."""
        # This will be fully implemented in W15 (Oracle Scoring Engine).
        # For now, it returns delta, falling back gracefully.
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
        """Construct the payload and dispatch via RemoteEvaluator.
        Fire-and-forget: returns immediately.
        """
        if self.offline_mode:
            return local_result
            
        body = {
            "agent_id": agent_id,
            "task_context": task_context,
            "risk_category": risk_category,
            "payload_hash": local_result.get("metadata", {}).get("payload_hash"),
            "risk_score": local_result.get("risk_score"),
            "threshold": local_result.get("threshold"),
            "passed": local_result.get("passed", False),
            "timestamp": time.time(),
        }
        self.evaluator.evaluate(body)
        return local_result
