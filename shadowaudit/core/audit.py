"""Local audit logging.

SQLite-backed append-only log of all gate decisions.
Cloud sync is optional and async (fire-and-forget).
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from shadowaudit.types import GateResult


class AuditLogger:
    """Append-only audit log with optional cloud sync."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._lock = threading.RLock()
        self._persistent_conn: sqlite3.Connection | None = None
        if self._db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
        self._init_schema()

    def _connection(self) -> sqlite3.Connection:
        if self._persistent_conn is not None:
            return self._persistent_conn
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self) -> None:
        conn = self._connection()
        with self._lock:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    task_context TEXT,
                    risk_category TEXT,
                    decision TEXT NOT NULL,
                    risk_score REAL,
                    threshold REAL,
                    payload_hash TEXT,
                    reason TEXT,
                    latency_ms INTEGER,
                    timestamp REAL NOT NULL
                )
                """
            )
            conn.commit()

    def record(
        self,
        agent_id: str,
        task_context: str,
        risk_category: str | None,
        result: GateResult,
        payload_hash: str | None = None,
    ) -> None:
        conn = self._connection()
        with self._lock:
            conn.execute(
                """
                INSERT INTO audit_events
                (agent_id, task_context, risk_category, decision, risk_score, threshold, payload_hash, reason, latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    task_context,
                    risk_category,
                    "pass" if result.passed else "fail",
                    result.risk_score,
                    result.threshold,
                    payload_hash,
                    result.reason,
                    result.latency_ms,
                    time.time(),
                ),
            )
            conn.commit()

    def get_events(
        self,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        conn = self._connection()
        with self._lock:
            if agent_id:
                cur = conn.execute(
                    "SELECT id, agent_id, task_context, risk_category, decision, "
                    "risk_score, threshold, payload_hash, reason, latency_ms, timestamp "
                    "FROM audit_events WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (agent_id, limit, offset),
                )
            else:
                cur = conn.execute(
                    "SELECT id, agent_id, task_context, risk_category, decision, "
                    "risk_score, threshold, payload_hash, reason, latency_ms, timestamp "
                    "FROM audit_events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in rows]

