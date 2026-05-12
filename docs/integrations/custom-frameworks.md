# Custom Framework Integration

If you are using a framework without a built-in adapter, call the Gate API directly before executing a tool.

## Direct gate usage

```python
from shadowaudit.core.gate import Gate

gate = Gate()

payload = {"command": "ls /tmp"}

result = gate.evaluate(
    agent_id="my-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path="policies/my_policy.yaml",
    payload=payload,
)

if result.passed:
    output = run_tool(payload)
else:
    raise RuntimeError(f"Blocked: {result.reason}")
```

## Wrapper class

```python
from typing import Any

from shadowaudit.core.gate import Gate
from shadowaudit.errors import AgentActionBlocked

class GatedTool:
    def __init__(self, tool: Any, agent_id: str, capability: str, policy_path: str):
        self.tool = tool
        self.agent_id = agent_id
        self.capability = capability
        self.policy_path = policy_path
        self.gate = Gate()

    def run(self, payload: dict, policy_context: dict | None = None) -> Any:
        result = self.gate.evaluate(
            agent_id=self.agent_id,
            task_context=getattr(self.tool, "name", "tool"),
            risk_category="tool_execution",
            capability=self.capability,
            policy_path=self.policy_path,
            payload=payload,
            policy_context=policy_context,
        )

        if not result.passed:
            raise AgentActionBlocked(
                detail=f"{self.capability} blocked: {result.reason}",
                gate_result=result,
            )

        return self.tool.run(payload)
```

## Async support

```python
gate = Gate()

async def safe_tool_call(payload: dict) -> Any:
    result = await gate.evaluate_async(
        agent_id="async-agent",
        task_context="api",
        risk_category="api_call",
        capability="api.call",
        policy_path="policies/api.yaml",
        payload=payload,
    )
    if not result.passed:
        raise PermissionError(result.reason)
    return await my_async_tool(payload)
```

## Related reference

- [Gate API reference](../reference/gate-api.md)
- [Policy schema](../reference/policy-schema.md)
