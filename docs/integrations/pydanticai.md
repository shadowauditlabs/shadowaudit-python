# PydanticAI Integration

ShadowAudit wraps PydanticAI tools or callables with a deterministic gate check before execution.

## Installation

```bash
pip install shadowaudit
```

## Wrapping a tool

```python
from shadowaudit.framework.pydanticai import ShadowAuditPydanticTool

async def fetch_account(account_id: str) -> dict:
    return {"account_id": account_id, "status": "active"}

safe_fetch = ShadowAuditPydanticTool(
    tool=fetch_account,
    agent_id="pydantic-agent",
    capability="account.read",
    policy_path="policies/fintech.yaml",
)
```

## Async usage

```python
result = await safe_fetch.acall("acct_123")
```

## Handling blocked calls

Blocked calls raise `AgentActionBlocked`.
