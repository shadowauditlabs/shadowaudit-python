"""Human Approval Workflows.

Manage pending, approved, and rejected runtime actions.
"""

from __future__ import annotations

import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any



@dataclass
class ApprovalRequest:
    id: str
    agent_id: str
    tool_name: str
    capability: str | None
    payload: dict[str, Any]
    reason: str
    status: str  # "pending", "approved", "rejected", "expired"
    created_at: float
    expires_at: float | None
    resolved_at: float | None = None
    resolved_by: str | None = None


class ApprovalManager:
    """Manages approval queues."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._lock = threading.RLock()
        self._persistent_conn: sqlite3.Connection | None = None
        if self._db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:", check_same_thread=False)
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
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    capability TEXT,
                    payload TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL,
                    resolved_at REAL,
                    resolved_by TEXT
                )
                """
            )
            conn.commit()

    def request_approval(
        self,
        agent_id: str,
        tool_name: str,
        capability: str | None,
        payload: dict[str, Any],
        reason: str,
        expires_in: float | None = 3600.0,
    ) -> ApprovalRequest:
        """Create a new pending approval request."""
        import json

        req_id = str(uuid.uuid4())
        now = time.time()
        expires_at = now + expires_in if expires_in else None

        req = ApprovalRequest(
            id=req_id,
            agent_id=agent_id,
            tool_name=tool_name,
            capability=capability,
            payload=payload,
            reason=reason,
            status="pending",
            created_at=now,
            expires_at=expires_at,
        )

        conn = self._connection()
        with self._lock:
            conn.execute(
                """
                INSERT INTO approvals
                (id, agent_id, tool_name, capability, payload, reason, status, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    req.id,
                    req.agent_id,
                    req.tool_name,
                    req.capability,
                    json.dumps(req.payload),
                    req.reason,
                    req.status,
                    req.created_at,
                    req.expires_at,
                ),
            )
            conn.commit()
        return req

    def get_pending(self) -> list[ApprovalRequest]:
        """Get all pending approvals."""
        import json

        conn = self._connection()
        now = time.time()
        with self._lock:
            cur = conn.execute(
                "SELECT id, agent_id, tool_name, capability, payload, reason, status, created_at, expires_at "
                "FROM approvals WHERE status = 'pending'"
            )
            rows = cur.fetchall()

        results = []
        for row in rows:
            req = ApprovalRequest(
                id=row[0],
                agent_id=row[1],
                tool_name=row[2],
                capability=row[3],
                payload=json.loads(row[4]),
                reason=row[5],
                status=row[6],
                created_at=row[7],
                expires_at=row[8],
            )
            if req.expires_at and now > req.expires_at:
                self._update_status(req.id, "expired")
                req.status = "expired"
            else:
                results.append(req)
        return results

    def _update_status(self, req_id: str, status: str, resolved_by: str | None = None) -> None:
        conn = self._connection()
        now = time.time()
        with self._lock:
            conn.execute(
                "UPDATE approvals SET status = ?, resolved_at = ?, resolved_by = ? WHERE id = ?",
                (status, now, resolved_by, req_id),
            )
            conn.commit()

    def approve(self, req_id: str, resolved_by: str | None = None) -> None:
        """Approve a request."""
        self._update_status(req_id, "approved", resolved_by)

    def reject(self, req_id: str, resolved_by: str | None = None) -> None:
        """Reject a request."""
        self._update_status(req_id, "rejected", resolved_by)

    def get_request(self, req_id: str) -> ApprovalRequest | None:
        import json

        conn = self._connection()
        with self._lock:
            cur = conn.execute(
                "SELECT id, agent_id, tool_name, capability, payload, reason, status, "
                "created_at, expires_at, resolved_at, resolved_by FROM approvals WHERE id = ?",
                (req_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return ApprovalRequest(
                id=row[0],
                agent_id=row[1],
                tool_name=row[2],
                capability=row[3],
                payload=json.loads(row[4]),
                reason=row[5],
                status=row[6],
                created_at=row[7],
                expires_at=row[8],
                resolved_at=row[9],
                resolved_by=row[10],
            )

    def has_approved_request(self, agent_id: str, tool_name: str, payload: dict[str, Any]) -> bool:
        """Check if there is an approved request for this exact payload."""
        import json
        
        target_payload_str = json.dumps(payload, sort_keys=True)
        
        conn = self._connection()
        with self._lock:
            cur = conn.execute(
                "SELECT payload FROM approvals WHERE agent_id = ? AND tool_name = ? AND status = 'approved'",
                (agent_id, tool_name)
            )
            rows = cur.fetchall()
            
        for row in rows:
            try:
                db_payload = json.loads(row[0])
                if json.dumps(db_payload, sort_keys=True) == target_payload_str:
                    return True
            except json.JSONDecodeError:
                continue
                
        return False
