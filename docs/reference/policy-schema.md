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

## Rule fields

Every rule in `deny`, `require_approval`, or `allow` supports:

| Field | Type | Required | Description |
|---|---|---|---|
| `capability` | string | Yes | Capability name to match. Exact match. |
| `contains` | string | No | Match if payload string contains this substring |
| `amount_gt` | number | No | Match if extracted numeric value exceeds this |
| `amount_lte` | number | No | Match if extracted numeric value is at or below this |
| `path_prefix` | string | No | Match if payload path starts with this prefix |
| `environment` | string | No | Match if policy context `environment` equals this |
| `user_role` | string | No | Match if policy context `user_role` equals this |
| `tenant` | string | No | Match if policy context `tenant` equals this |
| `caller_depth_gt` | integer | No | Match if agent call chain depth exceeds this |

## Numeric field extraction

`amount_gt` and `amount_lte` evaluate against numeric fields automatically extracted from the payload. ShadowAudit looks for keys named: `amount`, `total`, `value`, `price`, `cost`, `sum`. The first found numeric value is used.

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

ShadowAudit validates the policy file at gate initialization. A malformed policy causes the gate to raise a `PolicyLoadError`, which results in a fail-closed block for all subsequent evaluations until the policy is fixed.

```bash
# Validate a policy file
shadowaudit check-policy policies/my_policy.yaml
```
