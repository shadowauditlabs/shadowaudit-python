# Audit Log Format

ShadowAudit stores runtime decisions in a local SQLite database. The current table is `audit_events`.

## Schema

```sql
CREATE TABLE audit_events (
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
);
```

## Decision values

The audit table stores direct gate outcomes as:

| Value | Meaning |
|---|---|
| `pass` | The gate allowed execution. |
| `fail` | The gate blocked execution. |

Policy and approval details may also appear in result metadata or the approval database.

## Hash chaining

Each row stores `prev_hash` and `entry_hash`. The entry hash is computed from the canonical event fields and the previous entry hash.

```text
entry_hash = SHA-256(canonical_event_fields + prev_hash)
```

If an old row is modified, deleted, or reordered, verification fails.

## Signatures

When `AuditLogger(sign_entries=True)` is used, audit entries are signed with Ed25519 and the signature is stored in the `signature` column.

## Querying directly

```python
import sqlite3

conn = sqlite3.connect("audit.db")
rows = conn.execute("""
    SELECT id, timestamp, agent_id, task_context, risk_category, decision, reason
    FROM audit_events
    ORDER BY timestamp DESC
    LIMIT 50
""").fetchall()
```

## CLI access

```bash
shadowaudit logs --audit-log audit.db --json
shadowaudit verify --audit-log audit.db
```

## Related concepts

- [Audit chain](../concepts/audit-chain.md)
- [Replayability](../concepts/replayability.md)
