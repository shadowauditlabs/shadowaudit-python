# Approval Workflows Example

Approval workflows let agents pause sensitive actions instead of executing them immediately.

## Policy

```yaml
# policies/approvals.yaml

deny:
  - capability: payments.transfer
    amount_gt: 50000

require_approval:
  - capability: payments.transfer
    amount_gt: 1000
  - capability: production.database.write

allow:
  - capability: payments.read
  - capability: database.read
```

## Review queue

```bash
shadowaudit pending-approvals
```

Approve or reject:

```bash
shadowaudit approve <request_id> --user alice@example.com
shadowaudit reject <request_id> --user alice@example.com
```

## Python API

```python
from shadowaudit.core.approvals import ApprovalManager

manager = ApprovalManager(db_path="shadowaudit_approvals.db")

request = manager.request_approval(
    agent_id="finance-agent",
    tool_name="payments.transfer",
    capability="payments.transfer",
    payload={"amount": 5000, "currency": "USD"},
    reason="amount_gt=1000",
)

manager.approve(request.id, resolved_by="alice@example.com")
```

## Audit value

Approval workflows preserve human accountability without removing agent autonomy. The request, reviewer, decision, and reason can be retained as governance evidence.

