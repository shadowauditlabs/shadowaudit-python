# Protect Payments With Thresholds

## Policy

```yaml
deny:
  - capability: payments.transfer
    amount_gt: 50000

require_approval:
  - capability: payments.transfer
    amount_gt: 1000

allow:
  - capability: payments.transfer
    amount_lte: 1000
```

## Integration

```python
from shadowaudit.core.gate import Gate

gate = Gate()

result = gate.evaluate(
    agent_id="payments-agent",
    task_context="payments",
    risk_category="payment_initiation",
    capability="payments.transfer",
    policy_path="policies/payments.yaml",
    payload={"amount": 5000},
)
```

## Expected result

- Transfers over $50,000 are blocked.
- Transfers between $1,000 and $50,000 require approval.
- Transfers at or below $1,000 are allowed.
