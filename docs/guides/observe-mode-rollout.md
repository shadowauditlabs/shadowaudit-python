# Observe Mode Rollout

Deploying ShadowAudit in enforce mode immediately can surface policy gaps that block legitimate agent behavior. Observe mode lets you run ShadowAudit in production — logging all decisions — without blocking anything. You tune your policy on real traffic, then flip to enforce.

## The rollout pattern

1. **Observe**: Log all decisions. Block nothing. Understand your traffic.
2. **Tune**: Adjust policy rules based on what you see.
3. **Enforce**: Switch to full enforcement with confidence.

## Step 1: Observe mode

Create the gate in observe mode and pass it to the adapter:

```python
from shadowaudit import ShadowAuditTool
from shadowaudit.core.gate import Gate

safe_tool = ShadowAuditTool(
    tool=my_tool,
    agent_id="prod-agent",
    capability="shell.execute",
    policy_path="policies/shell.yaml",
    gate=Gate(mode="observe")
)
```

Or on the gate directly:

```python
gate = Gate(
    policy_path="policies/shell.yaml",
    mode="observe"
)
```

In observe mode:
- Every tool call is evaluated against policy.
- Every decision is logged to the audit database.
- No call is blocked, regardless of the decision.

## Step 2: Review what would have been blocked

```bash
shadowaudit logs --audit-log audit.db --json
```

Identify patterns:
- Are any denials legitimate calls your agent needs? Adjust the policy.
- Are any approvals actually safe to auto-allow? Move them to `allow`.
- Are there dangerous patterns not yet covered by `deny` rules? Add them.

## Step 3: Simulate policy changes

Export observed traffic and replay it against a revised policy:

```bash
shadowaudit simulate --trace-file audit.jsonl --taxonomy policies/shell_v2.yaml --compare
```

This shows you how your updated policy would have handled all real traffic from the observe period — before you deploy it.

## Step 4: Switch to enforce mode

Use an enforcing gate:

```python
safe_tool = ShadowAuditTool(
    tool=my_tool,
    agent_id="prod-agent",
    capability="shell.execute",
    policy_path="policies/shell_v2.yaml",
    gate=Gate(mode="enforce")
)
```

Monitor the first hours of enforcement using the audit log for any unexpected denials.

## Related guides

- [Replay an incident](replay-an-incident.md)
- [CI/CD enforcement](ci-cd-enforcement.md)
