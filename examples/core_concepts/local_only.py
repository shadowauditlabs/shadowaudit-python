"""Example: ShadowAudit gate without any external dependencies.

Runs 100% offline. Rule-based gating with SQLite state tracking.
Useful for CI/CD checks, local development, and offline environments.
"""

from shadowaudit import Gate


def main():
    # Default gate uses the 'general' taxonomy (read_only, write, delete, execute, etc.)
    general_gate = Gate()

    # Load a domain-specific taxonomy for financial operations
    financial_gate = Gate(taxonomy_path="financial")

    print("=== General taxonomy demo ===")
    payloads = [
        {"action": "view", "resource": "customer_profile"},    # read_only — passes
        {"action": "delete", "resource": "customer_record"},   # delete — blocks (delta 0.2, "delete" matched)
        {"action": "execute", "command": "rm -rf /"},           # execute — blocks (delta 0.1, "execute" matched)
    ]

    for payload in payloads:
        text = str(payload).lower()
        if "delete" in text or "remove" in text:
            category = "delete"
        elif any(k in text for k in ["execute", "run", "exec", "spawn"]):
            category = "execute"
        else:
            category = "read_only"

        result = general_gate.evaluate(
            agent_id="demo-agent",
            task_context="general_ops",
            risk_category=category,
            payload=payload,
        )

        status = "PASS" if result.passed else "BLOCK"
        print(f"[{status}] {category}: {payload}")
        print(f"  score={result.risk_score:.2f} threshold={result.threshold:.2f} latency={result.latency_ms}ms")

    print("\n=== Financial taxonomy demo ===")
    financial_payloads = [
        {"action": "transfer", "amount": 1000, "to": "account_123"},  # payment — blocks (delta 0.3)
        {"action": "withdraw", "amount": 50000, "from": "savings"},     # withdrawal — blocks (delta 0.2)
        {"action": "check_balance", "account": "checking"},             # balance — passes (delta 1.0)
    ]

    for payload in financial_payloads:
        text = str(payload).lower()
        if "transfer" in text or "disburse" in text or "pay" in text:
            category = "payment_initiation"
        elif "withdraw" in text:
            category = "withdrawal"
        else:
            category = "balance_inquiry"

        result = financial_gate.evaluate(
            agent_id="finance-bot",
            task_context="loan_processing",
            risk_category=category,
            payload=payload,
        )

        status = "PASS" if result.passed else "BLOCK"
        print(f"[{status}] {category}: {payload}")
        print(f"  score={result.risk_score:.2f} threshold={result.threshold:.2f} latency={result.latency_ms}ms")

    print("\n=== Audit trail ===")
    events = general_gate._audit.get_events(limit=10)
    print(f"Total audit events: {len(events)}")
    for ev in events[:3]:
        print(f"  [{ev['decision']}] {ev['task_context']} — {ev['reason']}")


if __name__ == "__main__":
    main()
