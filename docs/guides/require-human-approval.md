# Require Human Approval

Some actions are too consequential to allow or deny automatically. ShadowAudit's approval workflow pauses agent execution and routes the request to a human reviewer.

## How approval works

1. The agent calls a tool.
2. The gate evaluates the call and matches a `require_approval` rule.
3. The call is stored in the approval queue with full context.
4. The agent is notified the action is pending.
5. A human approves or rejects via CLI or API.
6. If approved, the tool executes. If rejected or expired, it does not.

## Policy configuration

```yaml
require_approval:
  - capability: payments.transfer
    amount_gt: 1000
  - capability: database.write
    environment: production
  - capability: filesystem.delete
  - capability: shell.execute
    contains: "systemctl"
```

## Inline override

When using the direct gate API, you can require approval for a call regardless of policy:

```python
result = gate.evaluate(
    agent_id="finance-agent",
    task_context="payments",
    risk_category="payment_initiation",
    capability="payments.transfer",
    payload={"amount": 5000},
    require_human_approval=True,
)
```

## Viewing pending approvals

```bash
shadowaudit pending-approvals
```

```
ID          Capability            Agent            Requested          Amount
a1b2c3d4    payments.transfer     finance-agent    2024-01-15 10:23   $2,500.00
e5f6g7h8    database.write        db-agent         2024-01-15 10:31   —
```

## Approving and rejecting

```bash
shadowaudit approve a1b2c3d4
shadowaudit reject e5f6g7h8
```

## Python API

```python
from shadowaudit.core.approvals import ApprovalManager

manager = ApprovalManager(db_path="shadowaudit_approvals.db")

# List pending
pending = manager.get_pending()
for request in pending:
    print(request.id, request.capability, request.agent_id)

# Approve
manager.approve("a1b2c3d4", resolved_by="alice@company.com")

# Reject
manager.reject("e5f6g7h8", resolved_by="bob@company.com")
```

## Approval expiration

Pending approvals expire after a configurable timeout. Expired approvals are automatically rejected:

```yaml
# policies/my_policy.yaml
approval_timeout_seconds: 3600  # 1 hour
```

After expiration, the agent's pending call fails with `approval_expired`.

## Audit trail

All approval actions are recorded:

```bash
shadowaudit logs --audit-log audit.db --json
```

The log includes who approved or rejected, when, and the original request context. This is tamper-evident via the hash chain.

## Related guides

- [Protect payment agents](protect-payment-agents.md)
- [Approval workflows example](../examples/approval-workflows.md)
