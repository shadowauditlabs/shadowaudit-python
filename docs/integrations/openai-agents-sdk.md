# OpenAI Agents SDK Integration

CapFence gates function tools defined with the OpenAI Agents SDK by wrapping them before they are registered with an agent.

## Installation

```bash
pip install "capfence[openai-agents]"
```

## Wrapping a function tool

```python
from capfence import CapFenceTool
from agents import function_tool

@function_tool
def run_shell(command: str) -> str:
    """Execute a shell command."""
    import subprocess
    return subprocess.check_output(command, shell=True, text=True)

safe_shell = CapFenceTool(
    tool=run_shell,
    agent_id="ops-agent",
    capability="shell.execute",
    policy_path="policies/shell.yaml"
)
```

## Using with an agent

```python
from agents import Agent, Runner

agent = Agent(
    name="OpsAgent",
    instructions="You help manage infrastructure.",
    tools=[safe_shell]
)

result = Runner.run_sync(agent, "List files in /tmp")
```

## Wrapping multiple tools

```python
from capfence import CapFenceTool

tools = [
    CapFenceTool(
        tool=read_file,
        agent_id="ops-agent",
        capability="filesystem.read",
        policy_path="policies/ops.yaml"
    ),
    CapFenceTool(
        tool=write_file,
        agent_id="ops-agent",
        capability="filesystem.write",
        policy_path="policies/ops.yaml"
    ),
    CapFenceTool(
        tool=run_shell,
        agent_id="ops-agent",
        capability="shell.execute",
        policy_path="policies/ops.yaml"
    ),
]
```

## Scanning for ungated tools

```bash
capfence check ./src --framework openai_agents
```

## Related integrations

- [LangChain](langchain.md)
- [Custom frameworks](custom-frameworks.md)
