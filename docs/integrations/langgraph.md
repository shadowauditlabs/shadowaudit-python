# LangGraph Integration

CapFence integrates with LangGraph by wrapping tools before they are passed to graph nodes. Enforcement applies at every tool invocation, including within loops and conditional branches.

## Installation

```bash
pip install "capfence[langchain]"
```

## Wrapping tools for a graph

```python
from capfence import CapFenceTool
from langchain.tools import ShellTool
from langgraph.prebuilt import create_react_agent

safe_shell = CapFenceTool(
    tool=ShellTool(),
    agent_id="graph-agent",
    capability="shell.execute",
    policy_path="policies/shell.yaml"
)

# Pass wrapped tools to the graph agent
graph = create_react_agent(model, tools=[safe_shell])
```

## Manual graph nodes

When defining graph nodes manually, gate tool calls within the node function:

```python
from capfence.core.gate import Gate
from langgraph.graph import StateGraph

gate = Gate()

def tool_node(state):
    command = state["command"]
    result = gate.evaluate(
        agent_id="graph-agent",
        task_context="shell",
        risk_category="shell_execution",
        capability="shell.execute",
        policy_path="policies/shell.yaml",
        payload={"command": command}
    )
    if not result.passed:
        return {"error": f"Blocked: {result.reason}"}
    # execute tool
    output = run_shell(command)
    return {"output": output}

builder = StateGraph(MyState)
builder.add_node("tool", tool_node)
```

## Multi-agent graphs

In graphs where one agent hands off to another, propagate the agent lineage:

```python
gate.evaluate(
    agent_id="executor-agent",
    task_context="database",
    risk_category="database_write",
    capability="database.write",
    policy_path="policies/database.yaml",
    payload={"query": sql}
)
```

Use FlowTracer when you need to track data movement across planner and executor agents.

## Related integrations

- [LangChain](langchain.md)
- [Custom frameworks](custom-frameworks.md)
