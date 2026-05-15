# AutoGen Integration

CapFence wraps AutoGen tools or callables with deterministic gate enforcement.

## Installation

```bash
pip install capfence
```

## Wrapping a tool

```python
from capfence.framework.autogen import CapFenceAutoGenTool

def run_shell(command: str) -> str:
    return "ok"

safe_shell = CapFenceAutoGenTool(
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
