# LlamaIndex Integration

CapFence wraps LlamaIndex tools with deterministic gate enforcement.

## Installation

```bash
pip install capfence
```

## Wrapping a tool

```python
from capfence.framework.llamaindex import CapFenceLlamaIndexTool

class QueryTool:
    name = "query_db"
    description = "Query the customer database"

    def call(self, query: str) -> dict:
        return {"rows": []}

safe_query = CapFenceLlamaIndexTool(
    tool=QueryTool(),
    agent_id="llama-agent",
    capability="database.read",
    policy_path="policies/db.yaml",
)
```

## Calling the tool

```python
safe_query.call({"query": "select 1"})
```
