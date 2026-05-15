# Fail-Closed Enforcement

Fail-closed means that when CapFence cannot reach a decision — due to a policy error, missing configuration, or internal fault — it blocks the action rather than allowing it through.

## The default position

In a fail-open system, uncertainty means "allow." In a fail-closed system, uncertainty means "deny."

CapFence is fail-closed by default. If the gate raises an unhandled exception, the framework adapter catches it and blocks the tool call. The agent receives an error. The tool never runs.

```
policy error → gate exception → AgentActionBlocked raised → tool not invoked
```

## Why fail-closed matters for agents

AI agents can make hundreds of tool calls across a session. A single gap in enforcement — one call that slips through while the gate is misconfigured — can have real consequences: a deleted file, a transferred payment, a leaked secret.

Fail-closed guarantees that gaps in policy are visible as errors, not silent passes.

## What triggers a fail-closed block

- Policy file is missing or malformed
- Policy rule references an unknown condition field
- Gate raises an internal error during evaluation
- Audit log write fails (depending on configuration)

## Fail-closed in practice

```python
gate = Gate()

result = gate.evaluate(
    agent_id="agent-1",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path="policies/missing_file.yaml",
    payload={"command": "echo hello"}
)
# result.passed == False
# result.reason == "policy_load_error"
```

The tool is blocked. The error is logged. The agent is informed.

## Configuring strict mode

By default, CapFence blocks unmatched capabilities (no rule matches → deny). This is the strictest posture. You can explicitly add an allow-all fallback if needed, but this is not recommended for production:

```yaml
# Not recommended in production
allow:
  - capability: "*"
```

The correct approach is to enumerate capabilities your agent uses and write explicit rules for each one.

## Related concepts

- [Runtime authorization](runtime-authorization.md)
- [Policy model](policy-model.md)
- [Threat model](../architecture/threat-model.md)
