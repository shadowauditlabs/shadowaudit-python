# Installation

ShadowAudit requires Python 3.9 or later.

## Install from PyPI

```bash
pip install shadowaudit
```

## Install with optional framework extras

```bash
# LangChain / LangGraph support
pip install "shadowaudit[langchain]"

# CrewAI support
pip install "shadowaudit[crewai]"

# OpenAI Agents SDK support
pip install "shadowaudit[openai-agents]"

# All integrations
pip install "shadowaudit[all]"
```

## Verify the installation

```bash
shadowaudit --version
```

## What gets installed

| Component | Purpose |
|---|---|
| `shadowaudit` CLI | Scan, assess, audit, replay, approve |
| `shadowaudit.core.gate` | Runtime gate for direct API use |
| `shadowaudit.adapters.*` | Framework-specific wrappers |
| `shadowaudit.mcp.gateway` | MCP governance gateway |
| Local SQLite audit database | Created on first run in `./audit.db` |

## Next steps

- [Quickstart](quickstart.md) — wrap your first tool in under 5 minutes
- [First policy](first-policy.md) — write a policy that blocks and allows
- [First blocked action](first-blocked-action.md) — see enforcement in action
