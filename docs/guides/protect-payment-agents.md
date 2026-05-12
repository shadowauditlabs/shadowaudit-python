# Protect Payment Agents

Payment operations carry direct financial risk. This guide shows how to apply ShadowAudit to payment agents: blocking large transfers, requiring approval for mid-range amounts, and providing a full audit trail for compliance.

## Payment policy

```yaml
# policies/payments_agent.yaml

deny:
  - capability: payments.transfer
    amount_gt: 50000
  - capability: payments.transfer
    environment: production
    user_role: unverified

require_approval:
  - capability: payments.transfer
    amount_gt: 1000
  - capability: payments.refund
    amount_gt: 500
  - capability: payments.batch_transfer

allow:
  - capability: payments.read
  - capability: payments.transfer
    amount_lte: 1000
  - capability: payments.refund
    amount_lte: 500
```

## Wrapping a payment tool

```python
from shadowaudit import ShadowAuditTool
from myapp.tools import PaymentsTool

safe_payments = ShadowAuditTool(
    tool=PaymentsTool(),
    agent_id="finance-agent",
    capability="payments.transfer",
    policy_path="policies/payments_agent.yaml"
)
```

For transfers with amounts, ShadowAudit automatically extracts numeric fields (`amount`, `total`, `value`) from the payload to evaluate threshold conditions.

## Passing runtime context

Enrich decisions with caller context:

```python
safe_payments.run(
    transfer_action,
    policy_context={
        "environment": "production",
        "user_role": "finance-analyst",
        "tenant": "acme-corp"
    }
)
```

## Handling approval-required transfers

When a transfer triggers `require_approval`, the action pauses. The agent receives a pending status. A human reviewer approves or rejects via the CLI:

```bash
# See pending approvals
shadowaudit pending-approvals

# Approve
shadowaudit approve <request_id>

# Reject
shadowaudit reject <request_id>
```

Or via the Python API:

```python
from shadowaudit.core.approvals import ApprovalManager

manager = ApprovalManager(db_path="shadowaudit_approvals.db")
pending = manager.get_pending()
manager.approve(pending[0].id, resolved_by="alice@company.com")
```

## Audit log for compliance

Every payment decision is recorded:

```bash
shadowaudit logs --audit-log audit.db --json
```

The hash-chained log provides tamper-evident evidence for SOX 404, PCI-DSS audit trails, and internal controls reviews.

## Related guides

- [Require human approval](require-human-approval.md) — detailed approval workflow setup
- [Replay an incident](replay-an-incident.md) — reproduce a payment decision for investigation
