# Quickstart

ShadowAudit sits between your AI agent and its tools. It evaluates every tool call against a policy before execution happens.

## 1. Install

```bash
pip install shadowaudit
```

## 2. Write a policy

Create `policies/my_policy.yaml`:

```yaml
deny:
  - capability: filesystem.delete
  - capability: shell.root_access

require_approval:
  - capability: payments.transfer
    amount_gt: 1000

allow:
  - capability: filesystem.read
  - capability: shell.execute
```

## 3. Wrap your tool

### LangChain

```python
from shadowaudit import ShadowAuditTool
from langchain.tools import ShellTool

safe_shell = ShadowAuditTool(
    tool=ShellTool(),
    agent_id="my-agent",
    capability="shell.execute",
    policy_path="policies/my_policy.yaml"
)
```

### Direct Gate API

```python
from shadowaudit.core.gate import Gate

gate = Gate()

result = gate.evaluate(
    agent_id="my-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path="policies/my_policy.yaml",
    payload={"command": "ls -la /tmp"}
)

if result.passed:
    # execute the tool
    pass
else:
    print(f"Blocked: {result.reason}")
```

## 4. Run your agent

Your agent runs normally. ShadowAudit intercepts each tool call:

- **Allowed** calls pass through to the tool.
- **Denied** calls raise `AgentActionBlocked` before the tool runs.
- **Approval-required** calls pause and enter the approval queue.

Every decision is recorded in the local audit log at `./audit.db`.

## 5. Check the audit log

```bash
shadowaudit logs
```

## 6. Verify log integrity

```bash
shadowaudit verify --audit-log ./audit.db
```

## Next steps

- [First policy](first-policy.md) — full policy syntax walkthrough
- [First blocked action](first-blocked-action.md) — observe a denial end-to-end
- [Guides](../guides/protect-shell-tools.md) — real-world protection patterns
