# ShadowAudit

**Runtime governance for AI agents — deterministic fail-closed enforcement.**

ShadowAudit wraps any AI agent tool and blocks dangerous calls before they execute. Keyword-based scoring, zero LLM calls, zero cloud dependencies, works fully offline.

## Quick Start

```bash
pip install shadowaudit
```

```bash
# Scan a codebase for ungated AI agent tools
shadowaudit check ./src

# Generate a professional HTML assessment report
shadowaudit check ./src -o report.html

# Block CI/CD deploys if high-risk tools are ungated
shadowaudit check ./src --fail-on-ungated

# Replay agent traces through the safety gate
shadowaudit simulate --trace-file agent_trace.jsonl --compare

# Build a custom risk taxonomy
shadowaudit build-taxonomy
```

## Python API

```python
from shadowaudit import Gate, ShadowAuditTool

# Wrap any LangChain tool with runtime enforcement
safe_tool = ShadowAuditTool(
    tool=ShellTool(),
    agent_id="ops-agent-1",
    risk_category="execute",
)

# Or use the gate directly
gate = Gate()
result = gate.evaluate(
    agent_id="agent-1",
    task_context="shell_tool",
    risk_category="execute",
    payload={"command": "ls -la"},
)
print(result.passed)  # True or False
```

## Features

- **Deterministic fail-closed** — any evaluation that is not an explicit pass is a hard block
- **Zero dependencies** — SQLite-backed state, no Redis, no cloud, no API keys
- **Framework-agnostic** — LangChain and CrewAI adapters included
- **Pre-built taxonomies** — general, financial, and legal risk categories with tuned thresholds
- **CI/CD integration** — `--fail-on-ungated` blocks deploys with unsafe tools
- **Professional reports** — Jinja2 HTML reports with executive summaries and remediation plans
- **Trace simulator** — replay agent execution traces to compare static vs adaptive scoring

## License

MIT — see [LICENSE](LICENSE) file.

## Links

- Documentation: https://docs.shadowaudit.io
- Repository: https://github.com/shadowaudit/shadowaudit-python
