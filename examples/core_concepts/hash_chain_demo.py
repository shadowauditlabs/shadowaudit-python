"""Example: Hash-chained audit log (Week 7a).

Demonstrates tamper-evident audit logging with SHA-256 chain linkage.
"""

from shadowaudit.core.gate import Gate
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.chain import verify_chain_from_rows


def main():
    # Create an audit logger with hash-chaining enabled
    audit = AuditLogger(db_path=":memory:", sign_entries=False)

    # Simulate some gate decisions
    gate = Gate(audit_logger=audit)

    # Decision 1: safe read — passes
    result1 = gate.evaluate(
        agent_id="agent-1",
        task_context="read_balance",
        risk_category="read_only",
        payload={"account_id": "123"},
    )
    print(f"Decision 1: {'PASS' if result1.passed else 'BLOCK'} (score={result1.risk_score:.2f})")

    # Decision 2: dangerous execute — blocked
    result2 = gate.evaluate(
        agent_id="agent-1",
        task_context="shell",
        risk_category="execute",
        payload={"command": "rm -rf /"},
    )
    print(f"Decision 2: {'PASS' if result2.passed else 'BLOCK'} (score={result2.risk_score:.2f})")

    # Verify the chain integrity
    rows = audit.get_events_chronological(limit=100)
    valid, errors = verify_chain_from_rows(rows)

    print(f"\nAudit chain verification: {'VALID' if valid else 'INVALID'}")
    if errors:
        for e in errors:
            print(f"  Error: {e}")
    else:
        print(f"  {len(rows)} entries, no tampering detected")

    # Demonstrate tamper detection by manually corrupting a row
    if rows:
        conn = audit._connection()
        conn.execute(
            "UPDATE audit_events SET decision = 'tampered' WHERE id = ?",
            (rows[0]["id"],),
        )
        conn.commit()

        rows_after = audit.get_events_chronological(limit=100)
        valid_after, errors_after = verify_chain_from_rows(rows_after)
        print(f"\nAfter tampering entry {rows[0]['id']}:")
        print(f"  Verification: {'VALID' if valid_after else 'INVALID'}")
        for e in errors_after:
            print(f"  Detected: {e}")


if __name__ == "__main__":
    main()
