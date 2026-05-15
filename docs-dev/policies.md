# Policy-as-Code Engine

CapFence uses a deterministic YAML-based policy engine to enforce execution boundaries at runtime. Policies allow you to define `allow`, `deny`, and `require_approval` rules based on capabilities, contextual data, and evaluated risk levels.

## Features

- **Capability-Based Rules**: Map agent actions to granular permissions.
- **Contextual Conditions**: Base decisions on environment, tenant, or user role.
- **Risk-Level Actions**: Automatically map assessed risk (e.g., "high") to enforcement actions.
- **Composition**: Layer and merge policies dynamically.

## Example Policy

```yaml
deny:
  - capability: filesystem.delete
  - capability: shell.root_access

allow:
  - capability: filesystem.read

require_approval:
  - capability: payments.transfer
    amount_gt: 1000

risk_levels:
  low:
    action: allow
  medium:
    action: warn
  high:
    action: require_approval
  critical:
    action: block
```

## Runtime Context Injection

Policies dynamically evaluate runtime context:

```python
safe_tool.run(
    action,
    policy_context={
        "environment": "production",
        "user_role": "admin",
        "tenant": "enterprise"
    }
)
```
