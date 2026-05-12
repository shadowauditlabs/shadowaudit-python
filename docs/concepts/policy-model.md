# Policy Model

ShadowAudit policies are YAML files that define deterministic rules for what agents can and cannot do at runtime.

## Three decision types

Every rule produces one of three decisions:

| Decision | Effect |
|---|---|
| `allow` | The tool call proceeds immediately |
| `deny` | The tool call is blocked before execution; raises `AgentActionBlocked` |
| `require_approval` | The tool call is paused; a human must approve or reject it |

## Rule evaluation order

Rules are evaluated from top to bottom. The **first matching rule wins**. If no rule matches, the default is `deny` (fail-closed).

```yaml
deny:        # evaluated first
  - ...

require_approval:  # evaluated second
  - ...

allow:       # evaluated last
  - ...
```

## Capability matching

The primary matching field is `capability`. This is a dot-separated string you assign when wrapping a tool:

```python
ShadowAuditTool(
    tool=MyTool(),
    capability="payments.transfer",
    ...
)
```

Policies match on exact capability names:

```yaml
deny:
  - capability: payments.transfer
    amount_gt: 50000
```

## Payload conditions

Rules can include conditions evaluated against the tool's payload:

```yaml
require_approval:
  - capability: shell.execute
    contains: "systemctl"
```

ShadowAudit automatically extracts numeric fields (`amount`, `total`, `value`, `price`) from payloads to support threshold conditions like `amount_gt`.

## Risk-level mapping

Instead of naming capabilities explicitly, you can map assessed risk levels to decisions:

```yaml
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

The risk scorer evaluates the payload and assigns a level based on keyword matching and pattern analysis.

## Runtime context

Rules can match against runtime context injected at call time:

```python
safe_tool.run(action, policy_context={"environment": "production"})
```

```yaml
require_approval:
  - capability: database.write
    environment: production
```

## Policy composition

You can layer policies by pointing different agents at different policy files. There is no inheritance or import system — each gate loads exactly one policy file. Use filesystem conventions (e.g., `policies/prod/`, `policies/staging/`) to manage multiple environments.

## Related concepts

- [Runtime authorization](runtime-authorization.md)
- [Policy schema reference](../reference/policy-schema.md)
- [Fail-closed enforcement](fail-closed-enforcement.md)
