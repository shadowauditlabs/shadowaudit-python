# Enforcement Flow

CapFence enforces policy at the final boundary before a tool executes.

```mermaid
graph LR
    A[Agent] --> B[Tool Request]
    B --> C[CapFence Gate]
    C --> D[Capability Mapping]
    D --> E[Policy Evaluation]
    E --> F{Decision}
    F -->|Allow| G[Execute Tool]
    F -->|Require Approval| H[Approval Queue]
    F -->|Deny| I[Blocked Response]
    F -.-> J[(Audit Log)]
```

## Steps

1. The agent attempts to call a tool.
2. CapFence maps the request to a capability.
3. The gate evaluates policy-as-code.
4. The decision is returned before execution.
5. The decision is recorded for audit and replay.

## Decision types

| Decision | Runtime behavior |
|---|---|
| Allow | The tool executes. |
| Require approval | Execution pauses until a reviewer approves. |
| Deny | The tool does not execute. |

The enforcement path does not require an LLM call.

