"""Async telemetry client for opt-in hashed metadata export.

Sends anonymized gate decision metadata to the ShadowAudit Cloud API.
Only hashes, scores, and category names are transmitted — no raw payloads.

Usage:
    from shadowaudit.telemetry.client import TelemetryClient

    client = TelemetryClient(api_key=os.getenv("SHADOWAUDIT_API_KEY"))
    await client.send_decision(
        agent_id="agent-1",
        task_context="shell_tool",
        risk_category="command_execution",
        decision="pass",
        risk_score=0.1,
        threshold=0.2,
        payload_hash="abc123...",
        latency_ms=5,
    )

Opt-in only. Set SHADOWAUDIT_TELEMETRY=1 to enable.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


class TelemetryClient:
    """Async fire-and-forget telemetry exporter.

    Sends hashed metadata to the cloud API. Never blocks the gate path.
    """

    DEFAULT_BASE_URL = "https://api.shadowaudit.io/v1"
    TIMEOUT_SECONDS = 3
    MAX_QUEUE_SIZE = 1000

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key or os.getenv("SHADOWAUDIT_API_KEY")
        self._base_url = (base_url or os.getenv("SHADOWAUDIT_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._enabled = os.getenv("SHADOWAUDIT_TELEMETRY", "0") == "1" and self._api_key is not None
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self._worker_task: asyncio.Task[None] | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self) -> None:
        """Start the background worker task."""
        if not self._enabled:
            return
        # Synchronous guard; async callers should await _async_start()
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())

    async def _async_start(self) -> None:
        """Thread-safe async start."""
        if not self._enabled:
            return
        async with self._lock:
            if self._worker_task is None or self._worker_task.done():
                self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        """Stop the background worker and flush remaining items."""
        async with self._lock:
            if self._worker_task is not None and not self._worker_task.done():
                await self._queue.put({"_shutdown": True})
                try:
                    await asyncio.wait_for(self._worker_task, timeout=5.0)
                except asyncio.TimeoutError:
                    self._worker_task.cancel()
                    try:
                        await self._worker_task
                    except asyncio.CancelledError:
                        pass

    async def send_decision(
        self,
        *,
        agent_id: str,
        task_context: str,
        risk_category: str | None,
        decision: str,
        risk_score: float | None,
        threshold: float | None,
        payload_hash: str | None,
        latency_ms: int | None,
    ) -> None:
        """Enqueue a decision record for async export.

        Never blocks. Drops items if queue is full.
        """
        if not self._enabled:
            return

        item = {
            "agent_id": agent_id,
            "task_context": task_context,
            "risk_category": risk_category,
            "decision": decision,
            "risk_score": risk_score,
            "threshold": threshold,
            "payload_hash": payload_hash,
            "latency_ms": latency_ms,
            "timestamp": time.time(),
        }

        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            logger.warning("Telemetry queue full. Dropping decision for agent_id=%s", agent_id)

    async def _worker(self) -> None:
        """Background worker that drains the queue and sends batches."""
        while True:
            item = await self._queue.get()
            if item.get("_shutdown"):
                self._queue.task_done()
                break

            # Simple single-item POST for now; batching can be added later
            await self._post_item(item)
            self._queue.task_done()

    async def _post_item(self, item: dict[str, Any]) -> None:
        """POST a single telemetry item to the cloud API."""
        body = json.dumps(item).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/ingest",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "shadowaudit-sdk/0.4.0",
            },
            method="POST",
        )

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=self._timeout),
            )
            self._last_error = None
        except urllib.error.HTTPError as e:
            self._last_error = f"HTTP {e.code}: {e.reason}"
            logger.debug("Telemetry HTTP error: %s", self._last_error)
        except urllib.error.URLError as e:
            self._last_error = f"Network error: {e.reason}"
            logger.debug("Telemetry network error: %s", self._last_error)
        except Exception as e:
            self._last_error = f"Unexpected: {type(e).__name__}: {e}"
            logger.debug("Telemetry unexpected error: %s", self._last_error)
