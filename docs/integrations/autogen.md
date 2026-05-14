# AutoGen Integration

ShadowAudit wraps AutoGen tools or callables with deterministic gate enforcement.

## Installation

```bash
pip install shadowaudit
```

## Wrapping a tool

```python
from shadowaudit.framework.autogen import ShadowAuditAutoGenTool

def run_shell(command: str) -> str:
    return "ok"

safe_shell = ShadowAuditAutoGenTool(
    tool=run_shell,
    agent_id="autogen-agent",
    capability="shell.execute",
    policy_path="policies/shell.yaml",
)
```

## Using the tool

```python
safe_shell({"command": "ls -la"})
```
