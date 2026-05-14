# LlamaIndex Integration

ShadowAudit wraps LlamaIndex tools with deterministic gate enforcement.

## Installation

```bash
pip install shadowaudit
```

## Wrapping a tool

```python
from shadowaudit.framework.llamaindex import ShadowAuditLlamaIndexTool

class QueryTool:
    name = "query_db"
    description = "Query the customer database"

    def call(self, query: str) -> dict:
        return {"rows": []}

safe_query = ShadowAuditLlamaIndexTool(
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
