# Threat Model

This threat model focuses on agent tool execution: the point where model output becomes an action against files, APIs, infrastructure, databases, or money movement systems.

## Assets

- Agent tool execution authority
- Policy files
- Approval decisions
- Audit logs
- Signing keys
- Production systems reachable by tools

## Trust boundaries

```text
LLM / Agent Planner → ShadowAudit Gate → Tool / API / Infrastructure
```

The agent planner is not treated as an authorization authority. ShadowAudit is the runtime authorization boundary.

## Threats

| Threat | Mitigation |
|---|---|
| Prompt injection causes a dangerous tool call | Policy is enforced after the model chooses the tool. |
| Agent attempts destructive shell command | Fail-closed deny rules block before execution. |
| Payment agent initiates high-value transfer | Threshold policy requires approval or denies. |
| Audit log is modified after an incident | Hash-chain verification detects tampering. |
| Enforcement service loses network access | Offline-first local policy evaluation continues. |
| Policy drift introduces risky permissions | CI scanning and replay simulation catch regressions. |

## Residual risks

ShadowAudit does not replace operating system sandboxing, secrets management, network segmentation, or least-privilege credentials. Use it as the runtime authorization layer for agent tools, alongside normal infrastructure controls.

