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
from shadowaudit.core.chain import compute_entry_hash, verify_chain_from_rows
from shadowaudit.core.keys import ensure_keypair, sign_entry


class AuditLogger:
    """Append-only audit log with optional cloud sync."""

    def __init__(self, db_path: str | Path = ":memory:", sign_entries: bool = False) -> None:
        self._db_path = str(db_path)
        self._lock = threading.RLock()
        self._persistent_conn: sqlite3.Connection | None = None
        self._sign_entries = sign_entries
        self._keypair: tuple[str, str] | None = None
        if self._sign_entries:
            self._keypair = ensure_keypair()
        if self._db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
        self._init_schema()
        self._migrate_legacy_entries()

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
                    timestamp REAL NOT NULL,
                    prev_hash TEXT NOT NULL DEFAULT '',
                    entry_hash TEXT NOT NULL DEFAULT '',
                    signature TEXT
                )
                """
            )
            conn.commit()

    def _migrate_legacy_entries(self) -> None:
        """Backfill prev_hash and entry_hash for legacy rows that lack them."""
        conn = self._connection()
        with self._lock:
            cur = conn.execute(
                "SELECT id FROM audit_events WHERE entry_hash = '' OR entry_hash IS NULL ORDER BY id ASC"
            )
            legacy_ids = [row[0] for row in cur.fetchall()]
            if not legacy_ids:
                return

            prev_hash = ""
            for entry_id in legacy_ids:
                cur = conn.execute(
                    "SELECT agent_id, task_context, risk_category, decision, risk_score, "
                    "threshold, payload_hash, reason, latency_ms, timestamp "
                    "FROM audit_events WHERE id = ?",
                    (entry_id,),
                )
                row = cur.fetchone()
                if not row:
                    continue
                (
                    agent_id,
                    task_context,
                    risk_category,
                    decision,
                    risk_score,
                    threshold,
                    payload_hash,
                    reason,
                    latency_ms,
                    timestamp_raw,
                ) = row
                timestamp = round(float(timestamp_raw), 6)
                fields = {
                    "agent_id": agent_id,
                    "task_context": task_context,
                    "risk_category": risk_category,
                    "decision": decision,
                    "risk_score": risk_score,
                    "threshold": threshold,
                    "payload_hash": payload_hash,
                    "reason": reason,
                    "latency_ms": latency_ms,
                    "timestamp": timestamp,
                }
                entry_hash = compute_entry_hash(fields, prev_hash)
                conn.execute(
                    "UPDATE audit_events SET prev_hash = ?, entry_hash = ? WHERE id = ?",
                    (prev_hash, entry_hash, entry_id),
                )
                prev_hash = entry_hash
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
            # Fetch previous entry hash for chaining
            cur = conn.execute(
                "SELECT entry_hash FROM audit_events ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            prev_hash = row[0] if row else ""

            timestamp = round(time.time(), 6)
            fields = {
                "agent_id": agent_id,
                "task_context": task_context,
                "risk_category": risk_category,
                "decision": "pass" if result.passed else "fail",
                "risk_score": result.risk_score,
                "threshold": result.threshold,
                "payload_hash": payload_hash,
                "reason": result.reason,
                "latency_ms": result.latency_ms,
                "timestamp": timestamp,
            }
            entry_hash = compute_entry_hash(fields, prev_hash)

            signature: str | None = None
            if self._sign_entries and self._keypair:
                sign_fields = {**fields, "prev_hash": prev_hash, "entry_hash": entry_hash}
                signature = sign_entry(sign_fields, self._keypair[1])

            conn.execute(
                """
                INSERT INTO audit_events
                (agent_id, task_context, risk_category, decision, risk_score, threshold, payload_hash, reason, latency_ms, timestamp, prev_hash, entry_hash, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    timestamp,
                    prev_hash,
                    entry_hash,
                    signature,
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
                    "risk_score, threshold, payload_hash, reason, latency_ms, timestamp, "
                    "prev_hash, entry_hash, signature "
                    "FROM audit_events WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (agent_id, limit, offset),
                )
            else:
                cur = conn.execute(
                    "SELECT id, agent_id, task_context, risk_category, decision, "
                    "risk_score, threshold, payload_hash, reason, latency_ms, timestamp, "
                    "prev_hash, entry_hash, signature "
                    "FROM audit_events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in rows]

    def get_events_chronological(
        self,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return events in chronological order (oldest first) for chain verification."""
        conn = self._connection()
        with self._lock:
            if agent_id:
                cur = conn.execute(
                    "SELECT id, agent_id, task_context, risk_category, decision, "
                    "risk_score, threshold, payload_hash, reason, latency_ms, timestamp, "
                    "prev_hash, entry_hash, signature "
                    "FROM audit_events WHERE agent_id = ? ORDER BY timestamp ASC, id ASC LIMIT ? OFFSET ?",
                    (agent_id, limit, offset),
                )
            else:
                cur = conn.execute(
                    "SELECT id, agent_id, task_context, risk_category, decision, "
                    "risk_score, threshold, payload_hash, reason, latency_ms, timestamp, "
                    "prev_hash, entry_hash, signature "
                    "FROM audit_events ORDER BY timestamp ASC, id ASC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in rows]

    def verify(self) -> tuple[bool, list[str]]:
        """Verify hash-chain integrity of the entire audit log.

        Returns:
            Tuple of (all_valid, list_of_error_messages).
        """
        rows = self.get_events_chronological(limit=1000000)
        return verify_chain_from_rows(rows)

