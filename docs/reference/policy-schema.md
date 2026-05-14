# Policy Schema Reference

ShadowAudit policies are YAML files. This page documents every supported field.

## Top-level structure

```yaml
deny:          # list of deny rules
  - ...

require_approval:  # list of approval rules
  - ...

allow:         # list of allow rules
  - ...

risk_levels:   # map risk levels to decisions
  low:
    action: allow
  medium:
    action: warn
  high:
    action: require_approval
  critical:
    action: block

approval_timeout_seconds: 3600  # optional; default 3600
```

Bundled starter policies may also use the legacy `rules` format:

```yaml
version: "1.0"
policy_name: production_shell_policy
enforcement_mode: block

rules:
  - id: destructive_commands
    match_keywords:
      - "rm -rf"
    action: block
  - id: read_only_commands
    match_regex:
      - "^ls"
    action: allow
```

The legacy format is supported for backwards compatibility. New policies should prefer the capability-based `deny`, `require_approval`, and `allow` sections.

## Rule fields

Every rule in `deny`, `require_approval`, or `allow` supports:

| Field | Type | Required | Description |
|---|---|---|---|
| `capability` | string | Yes | Capability name to match. Exact match, or wildcard suffix such as `filesystem.*`. |
| `contains` | string | No | Match if payload string contains this substring |
| `amount_gt` | number | No | Match if extracted numeric value exceeds this |
| `amount_gte` | number | No | Match if extracted numeric value is greater than or equal to this |
| `amount_lt` | number | No | Match if extracted numeric value is below this |
| `amount_lte` | number | No | Match if extracted numeric value is at or below this |
| `path_prefix` | string | No | Match if payload path starts with this prefix |
| `environment` | string | No | Match if policy context `environment` equals this |
| `user_role` | string | No | Match if policy context `user_role` equals this |
| `tenant` | string | No | Match if policy context `tenant` equals this |
| `caller_depth_gt` | integer | No | Match if agent call chain depth exceeds this |
| `caller_depth_gte` | integer | No | Match if agent call chain depth is greater than or equal to this |
| `caller_depth_lt` | integer | No | Match if agent call chain depth is below this |
| `caller_depth_lte` | integer | No | Match if agent call chain depth is at or below this |

Legacy `rules` entries support `id`, `description`, `capability`, `match_keywords`, `match_regex`, `threshold`, and `action`.

## Numeric field extraction

Numeric comparisons evaluate against fields automatically extracted from the payload. ShadowAudit looks for keys named: `amount`, `total`, `value`, `price`, `cost`, `sum`, and `quantity`. The first found numeric value is used.

## Risk level mapping

```yaml
risk_levels:
  low:
    action: allow
  medium:
    action: warn       # log but allow
  high:
    action: require_approval
  critical:
    action: block      # alias for deny
```

Risk levels are assigned by the risk scorer based on keyword matching and pattern analysis of the payload. If `risk_levels` is not defined, risk level alone does not affect the decision.

## Approval timeout

```yaml
approval_timeout_seconds: 1800  # 30 minutes
```

If a `require_approval` decision is not actioned within this duration, the approval expires and the call is automatically rejected. Default is 3600 (1 hour).

## Example: multi-environment policy

```yaml
deny:
  - capability: database.drop
  - capability: filesystem.delete
    environment: production

require_approval:
  - capability: database.write
    environment: production
  - capability: payments.transfer
    amount_gt: 1000

allow:
  - capability: database.read
  - capability: database.write
    environment: staging
  - capability: filesystem.read
  - capability: payments.transfer
    amount_lte: 1000

approval_timeout_seconds: 1800
```

## Validation

ShadowAudit validates the policy file when it is loaded. A malformed policy raises `PolicyLoadError`. During gate evaluation, policy load or validation failures fail closed with a `policy_error_PolicyLoadError` decision.

```bash
# Validate a policy file
shadowaudit check-policy policies/my_policy.yaml
```
