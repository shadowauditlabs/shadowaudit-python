"""SQLite-backed agent state tracking.

Tracks historical decisions and request velocity per agent_id.
Replaces Redis for the open-source SDK (zero external dependencies).
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class AgentStateStore:
    """SQLite-backed rolling history and velocity tracking.

    Thread-safe. Auto-creates schema on first use.
    For :memory: databases, a single persistent connection is kept
    so that data survives across SQL operations.
    """

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
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA wal_autocheckpoint=1000")
        return conn

    def _init_schema(self) -> None:
        conn = self._connection()
        with self._lock:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_decisions (
                    agent_id TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    payload_hash TEXT,
                    tool_name TEXT,
                    risk_category TEXT,
                    amount REAL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_time ON agent_decisions(agent_id, timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_tool ON agent_decisions(agent_id, tool_name, timestamp)"
            )
            conn.commit()

    def record_decision(
        self,
        agent_id: str,
        passed: bool,
        payload_hash: str | None = None,
        tool_name: str | None = None,
        risk_category: str | None = None,
        amount: float | None = None,
    ) -> None:
        conn = self._connection()
        with self._lock:
            conn.execute(
                "INSERT INTO agent_decisions (agent_id, passed, timestamp, payload_hash, tool_name, risk_category, amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (agent_id, 1 if passed else 0, time.time(), payload_hash, tool_name, risk_category, amount),
            )
            conn.commit()

    def record_decision_batch(
        self,
        records: list[tuple[str, bool, str | None, str | None, str | None, float | None]],
    ) -> None:
        """Batch insert multiple decisions for high-throughput scenarios.

        Args:
            records: List of (agent_id, passed, payload_hash, tool_name, risk_category, amount) tuples.
        """
        conn = self._connection()
        now = time.time()
        with self._lock:
            conn.executemany(
                "INSERT INTO agent_decisions (agent_id, passed, timestamp, payload_hash, tool_name, risk_category, amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (agent_id, 1 if passed else 0, now, payload_hash, tool_name, risk_category, amount)
                    for agent_id, passed, payload_hash, tool_name, risk_category, amount in records
                ],
            )
            conn.commit()

    def compute_K(self, agent_id: str, window_seconds: float = 86400.0) -> float:
        """Historical accuracy: fraction of pass decisions in rolling window.

        K in [0, 1]. No history → 0.0.
        """
        cutoff = time.time() - window_seconds
        conn = self._connection()
        with self._lock:
            cur = conn.execute(
                "SELECT passed FROM agent_decisions WHERE agent_id = ? AND timestamp >= ?",
                (agent_id, cutoff),
            )
            rows = cur.fetchall()
        if not rows:
            return 0.0
        return sum(int(r[0]) for r in rows) / len(rows)

    def compute_V(self, agent_id: str, window_seconds: float = 60.0) -> float:
        """Request velocity: count of decisions in window.

        Clamped to minimum 1.0 to prevent log10(0) in downstream formula.
        """
        cutoff = time.time() - window_seconds
        conn = self._connection()
        with self._lock:
            cur = conn.execute(
                "SELECT COUNT(*) FROM agent_decisions WHERE agent_id = ? AND timestamp >= ?",
                (agent_id, cutoff),
            )
            count = cur.fetchone()[0]
        return max(float(count), 1.0)

    def get_history(self, agent_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve recent decisions for an agent (for inspection / debugging)."""
        conn = self._connection()
        with self._lock:
            cur = conn.execute(
                "SELECT passed, timestamp, payload_hash, tool_name, risk_category, amount FROM agent_decisions WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                (agent_id, limit),
            )
            rows = cur.fetchall()
        return [
            {
                "passed": bool(r[0]),
                "timestamp": r[1],
                "payload_hash": r[2],
                "tool_name": r[3],
                "risk_category": r[4],
                "amount": r[5],
            }
            for r in rows
        ]

    def get_recent_tools(self, agent_id: str, window_seconds: float = 300.0, limit: int = 20) -> list[str]:
        """Get list of recent tool names in a time window (most recent first)."""
        cutoff = time.time() - window_seconds
        conn = self._connection()
        with self._lock:
            cur = conn.execute(
                "SELECT tool_name FROM agent_decisions WHERE agent_id = ? AND timestamp >= ? AND tool_name IS NOT NULL ORDER BY timestamp DESC LIMIT ?",
                (agent_id, cutoff, limit),
            )
            rows = cur.fetchall()
        return [r[0] for r in rows if r[0]]

    def get_total_amount(self, agent_id: str, window_seconds: float = 300.0, risk_category: str | None = None) -> float:
        """Sum of monetary amounts in recent window (for financial anomaly detection)."""
        cutoff = time.time() - window_seconds
        conn = self._connection()
        with self._lock:
            if risk_category:
                cur = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM agent_decisions WHERE agent_id = ? AND timestamp >= ? AND risk_category = ? AND amount IS NOT NULL",
                    (agent_id, cutoff, risk_category),
                )
            else:
                cur = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM agent_decisions WHERE agent_id = ? AND timestamp >= ? AND amount IS NOT NULL",
                    (agent_id, cutoff),
                )
            result = cur.fetchone()[0]
        return float(result or 0.0)

    def detect_velocity_spike(self, agent_id: str, tool_name: str | None = None, window_seconds: float = 60.0, threshold: int = 3) -> bool:
        """Detect if tool calls exceed threshold count in a window."""
        cutoff = time.time() - window_seconds
        conn = self._connection()
        with self._lock:
            if tool_name:
                cur = conn.execute(
                    "SELECT COUNT(*) FROM agent_decisions WHERE agent_id = ? AND timestamp >= ? AND tool_name = ?",
                    (agent_id, cutoff, tool_name),
                )
            else:
                cur = conn.execute(
                    "SELECT COUNT(*) FROM agent_decisions WHERE agent_id = ? AND timestamp >= ?",
                    (agent_id, cutoff),
                )
            count = cur.fetchone()[0]
        return int(count or 0) >= threshold

