# CrewAI Integration

CapFence wraps CrewAI tools with a runtime gate. The wrapped tool is used in place of the original wherever it would appear in a crew or task definition.

## Installation

```bash
pip install "capfence[crewai]"
```

## Wrapping a CrewAI tool

```python
from capfence import CapFenceTool
from crewai_tools import FileReadTool

safe_file = CapFenceTool(
    tool=FileReadTool(),
    agent_id="research-agent",
    capability="filesystem.read",
    policy_path="policies/research.yaml"
)
```

## Using with a crew

```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="Researcher",
    goal="Gather information from files",
    tools=[safe_file]
)

task = Task(
    description="Read and summarize /data/report.pdf",
    agent=researcher
)

crew = Crew(agents=[researcher], tasks=[task])
crew.kickoff()
```

## Wrapping custom tools

```python
from crewai.tools import BaseTool
from capfence import CapFenceTool

class MyDatabaseTool(BaseTool):
    name: str = "database_query"
    description: str = "Query the production database"

    def _run(self, query: str) -> str:
        # database logic
        ...

safe_db = CapFenceTool(
    tool=MyDatabaseTool(),
    agent_id="db-agent",
    capability="database.read",
    policy_path="policies/database.yaml"
)
```

## Policy example for CrewAI

```yaml
# policies/research.yaml
deny:
  - capability: filesystem.write
  - capability: filesystem.delete

allow:
  - capability: filesystem.read
  - capability: web.search
  - capability: web.fetch
```

## Scanning for ungated tools

```bash
capfence check ./src --framework crewai
```

## Related integrations

- [LangChain](langchain.md)
- [Custom frameworks](custom-frameworks.md)
