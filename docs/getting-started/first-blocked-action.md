# Your First Blocked Action

This walkthrough shows what enforcement looks like end-to-end: a policy blocks a dangerous tool call before it reaches the tool.

## Setup

Create `policies/demo.yaml`:

```yaml
deny:
  - capability: shell.execute
    contains: "rm -rf"

allow:
  - capability: shell.execute
```

## Code

```python
from capfence.core.gate import Gate

gate = Gate()

# This call is safe — it passes
result = gate.evaluate(
    agent_id="demo-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path="policies/demo.yaml",
    payload={"command": "ls -la /tmp"}
)
print(result.passed)   # True

# This call is dangerous — it is blocked before execution
result = gate.evaluate(
    agent_id="demo-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path="policies/demo.yaml",
    payload={"command": "rm -rf /var/lib/postgresql"}
)
print(result.passed)   # False
print(result.reason)   # destructive_command_detected
```

## What happens at the framework layer

With a LangChain wrapper, blocked calls raise an exception so the agent cannot proceed:

```python
from capfence import CapFenceTool
from langchain.tools import ShellTool

safe_shell = CapFenceTool(
    tool=ShellTool(),
    agent_id="demo-agent",
    capability="shell.execute",
    policy_path="policies/demo.yaml"
)

# This raises AgentActionBlocked — the shell never runs
safe_shell.run("rm -rf /var/lib/postgresql")
```

```
AgentActionBlocked: capability=shell.execute decision=denied reason=destructive_command_detected
```

## Checking the audit log

Both the allowed and denied decisions are recorded:

```bash
capfence logs
```

```
timestamp            agent_id      capability      decision  reason
2024-01-15 10:23:01  demo-agent    shell.execute   allow     —
2024-01-15 10:23:02  demo-agent    shell.execute   deny      destructive_command_detected
```

## Verifying log integrity

```bash
capfence verify --audit-log ./audit.db
✓ Audit chain intact. 2 entries verified.
```

## Next steps

- [Guides](../guides/protect-shell-tools.md) — protect real agent tools
- [Human approval workflows](../guides/require-human-approval.md) — pause for review instead of denying
- [Replay an incident](../guides/replay-an-incident.md) — re-evaluate a past decision
