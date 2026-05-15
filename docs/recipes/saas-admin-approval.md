# Require Approval For SaaS Admin Changes

## Policy

```yaml
require_approval:
  - capability: saas.user.role_change
  - capability: saas.org.permission_change

deny:
  - capability: saas.user.disable_mfa

allow:
  - capability: saas.user.read
  - capability: saas.org.read
```

## Integration

```python
from capfence.core.gate import Gate

gate = Gate()

result = gate.evaluate(
    agent_id="admin-agent",
    task_context="saas_admin",
    risk_category="admin_change",
    capability="saas.user.role_change",
    policy_path="policies/saas.yaml",
    payload={"user_id": "u_123", "role": "owner"},
)
```

## Expected result

- Role or permission changes require approval.
- MFA disablement is blocked.
