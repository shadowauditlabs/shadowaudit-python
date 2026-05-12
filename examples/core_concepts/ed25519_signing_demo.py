"""Example: Ed25519-signed audit entries (Week 7b).

Demonstrates cryptographic signing of audit log entries for authenticity.
"""

from shadowaudit.core.gate import Gate
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.keys import generate_keypair, load_keypair, verify_entry


def main():
    # Generate a new keypair (stored in ~/.shadowaudit/keys/)
    pub_b64, priv_b64 = generate_keypair()
    print("Generated Ed25519 keypair")
    print(f"  Public key:  {pub_b64[:20]}...")
    print(f"  Private key: {priv_b64[:20]}...")

    # Create an audit logger with signing enabled
    audit = AuditLogger(db_path=":memory:", sign_entries=True)
    gate = Gate(audit_logger=audit)

    # Make a decision — entry will be signed
    result = gate.evaluate(
        agent_id="agent-1",
        task_context="payment",
        risk_category="payment_initiation",
        payload={"amount": 100.0, "to": "vendor_123"},
    )
    print(f"\nDecision: {'PASS' if result.passed else 'BLOCK'}")

    # Retrieve the signed entry
    rows = audit.get_events_chronological(limit=1)
    if rows:
        entry = rows[0]
        print("\nAudit entry:")
        print(f"  ID:        {entry['id']}")
        print(f"  Decision:  {entry['decision']}")
        print(f"  Signature: {entry['signature'][:40]}..." if entry.get('signature') else "  Signature: None")

        # Verify the signature
        if entry.get('signature') and entry.get('entry_hash'):
            fields = {
                "agent_id": entry['agent_id'],
                "task_context": entry['task_context'],
                "risk_category": entry['risk_category'],
                "decision": entry['decision'],
                "risk_score": entry.get('risk_score'),
                "threshold": entry.get('threshold'),
                "payload_hash": entry.get('payload_hash'),
                "reason": entry.get('reason'),
                "latency_ms": entry.get('latency_ms'),
                "timestamp": entry['timestamp'],
            }
            is_valid = verify_entry(fields, entry['signature'], pub_b64)
            print(f"\nSignature verification: {'VALID' if is_valid else 'INVALID'}")

    # Load existing keypair
    loaded = load_keypair()
    if loaded:
        print(f"\nLoaded existing keypair: {loaded[0][:20]}...")


if __name__ == "__main__":
    main()
