# Protect Production DB Writes

## Policy

```yaml
deny:
  - capability: database.drop

require_approval:
  - capability: database.write
    environment: production

allow:
  - capability: database.read
  - capability: database.write
    environment: staging
```

## Integration

```python
from shadowaudit.core.gate import Gate

gate = Gate()

result = gate.evaluate(
    agent_id="db-agent",
    task_context="db",
    risk_category="database_write",
    capability="database.write",
    policy_path="policies/db.yaml",
    payload={"query": "update accounts set status='inactive'"},
    policy_context={"environment": "production"},
)
```

## Expected result

- Production writes require approval.
- Staging writes pass.
