# Human Approval Workflows

ShadowAudit supports approval-based runtime governance. You can define policies that require a human-in-the-loop for high-risk actions.

## Features
- **Approval Queues**: Pending actions wait for authorization.
- **Approval Persistence**: Stored reliably in an SQLite ledger.
- **Approval Audit Logs**: Complete traceability of who approved what and when.
- **Expiration**: Approvals timeout if not actioned.

## API Usage

```python
safe_tool.run(
    action,
    require_human_approval=True
)
```

Or via Policy:
```yaml
require_approval:
  - capability: production.database.write
```

## CLI Commands

```bash
# View pending approvals
shadowaudit pending-approvals

# Approve a request
shadowaudit approve <request_id>

# Reject a request
shadowaudit reject <request_id>
```
