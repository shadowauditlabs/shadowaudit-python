# Protect Shell Tools

## Policy

```yaml
deny:
  - capability: shell.execute
    contains: "rm -rf"

allow:
  - capability: shell.execute
```

## Integration

```python
from capfence import CapFenceTool
from langchain.tools import ShellTool

safe_shell = CapFenceTool(
    tool=ShellTool(),
    agent_id="ops-agent",
    capability="shell.execute",
    policy_path="policies/shell.yaml",
)
```

## Expected result

- Destructive commands are blocked before execution.
- Safe commands run normally.
