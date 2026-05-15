# LangChain Integration

CapFence wraps any LangChain tool with a runtime gate. The wrapped tool is a drop-in replacement — it has the same interface and can be used anywhere the original tool is used.

## Installation

```bash
pip install "capfence[langchain]"
```

## Wrapping a tool

```python
from capfence import CapFenceTool
from langchain.tools import ShellTool

safe_shell = CapFenceTool(
    tool=ShellTool(),
    agent_id="my-agent",
    capability="shell.execute",
    policy_path="policies/shell.yaml"
)
```

## Using with an agent

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")
tools = [safe_shell]

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
executor.invoke({"input": "List the files in /tmp"})
```

## Wrapping multiple tools

```python
from capfence import CapFenceTool
from langchain.tools import ShellTool, FileManagementToolkit

shell = CapFenceTool(
    tool=ShellTool(),
    agent_id="ops-agent",
    capability="shell.execute",
    policy_path="policies/ops.yaml"
)

file_tools = [
    CapFenceTool(
        tool=t,
        agent_id="ops-agent",
        capability=f"filesystem.{t.name}",
        policy_path="policies/ops.yaml"
    )
    for t in FileManagementToolkit().get_tools()
]

tools = [shell] + file_tools
```

## Passing runtime context

```python
# Pass context on each invocation
safe_shell.run(
    "ls /tmp",
    policy_context={
        "environment": "production",
        "user_role": "engineer"
    }
)
```

## Handling blocked calls

Blocked calls raise `AgentActionBlocked`. LangChain's `AgentExecutor` catches tool exceptions and reports them to the agent:

```python
from capfence.exceptions import AgentActionBlocked

try:
    result = safe_shell.run("rm -rf /var/lib/postgresql")
except AgentActionBlocked as e:
    print(f"Blocked: {e.reason}")
```

## Scanning for ungated tools

```bash
capfence check ./src --framework langchain
```

This identifies LangChain tools in your codebase that are not wrapped with CapFence.

## Related integrations

- [LangGraph](langgraph.md)
- [Custom frameworks](custom-frameworks.md)
