# Installation

CapFence requires Python 3.9 or later.

## Install from PyPI

```bash
pip install capfence
```

## Install with optional framework extras

```bash
# LangChain / LangGraph support
pip install "capfence[langchain]"

# CrewAI support
pip install "capfence[crewai]"

# OpenAI Agents SDK support
pip install "capfence[openai-agents]"

# All integrations
pip install "capfence[all]"
```

## Verify the installation

```bash
capfence --version
```

## What gets installed

| Component | Purpose |
|---|---|
| `capfence` CLI | Scan, assess, audit, replay, approve |
| `capfence.core.gate` | Runtime gate for direct API use |
| `capfence.adapters.*` | Framework-specific wrappers |
| `capfence.mcp.gateway` | MCP governance gateway |
| Local SQLite audit database | Created on first run in `./audit.db` |

## Next steps

- [Quickstart](quickstart.md) — wrap your first tool in under 5 minutes
- [First policy](first-policy.md) — write a policy that blocks and allows
- [First blocked action](first-blocked-action.md) — see enforcement in action
