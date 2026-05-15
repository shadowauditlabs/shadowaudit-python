# Database Write Gating

This example shows how to let an agent read from a database while gating writes, deletes, and schema changes.

## Policy

```yaml
# policies/database_agent.yaml

deny:
  - capability: database.drop_table
  - capability: database.delete
    environment: production

require_approval:
  - capability: database.write
    environment: production
  - capability: database.migration

allow:
  - capability: database.read
  - capability: database.write
    environment: staging
```

## Wrapped tools

```python
from capfence import CapFenceTool

safe_query = CapFenceTool(
    tool=ReadOnlyQueryTool(),
    agent_id="analytics-agent",
    capability="database.read",
    policy_path="policies/database_agent.yaml",
)

safe_write = CapFenceTool(
    tool=DatabaseWriteTool(),
    agent_id="analytics-agent",
    capability="database.write",
    policy_path="policies/database_agent.yaml",
)
```

## Runtime behavior

```text
SELECT * FROM invoices LIMIT 10
→ allowed

UPDATE invoices SET status = 'paid' WHERE id = 'inv_123'
→ requires approval in production

DROP TABLE invoices
→ denied before execution
```

## Why this matters

Database tools are often exposed to agents as general-purpose query interfaces. CapFence makes the execution boundary explicit: reads can be allowed, writes can require approval, and destructive actions can be denied deterministically.

