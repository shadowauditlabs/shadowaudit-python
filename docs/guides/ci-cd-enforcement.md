# CI/CD Enforcement

ShadowAudit's static scanner can block CI/CD pipelines when ungated AI agent tools are detected. This prevents unenforced tools from reaching production.

## What the scanner checks

`shadowaudit check` parses Python files with the AST module and identifies:

- LangChain `BaseTool` subclasses not wrapped with `ShadowAuditTool`
- CrewAI `BaseTool` subclasses not wrapped
- OpenAI Agents SDK function tools not gated
- MCP tool definitions without a gateway

Cross-file detection is supported: a tool defined in `tools.py` and wrapped in `agent.py` is correctly detected as gated.

## GitHub Actions

```yaml
# .github/workflows/shadowaudit.yml
name: ShadowAudit Gate Check

on: [push, pull_request]

jobs:
  gate-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install ShadowAudit
        run: pip install shadowaudit

      - name: Check for ungated tools
        run: shadowaudit check ./src --fail-on-ungated

      - name: Generate HTML report (on failure)
        if: failure()
        run: shadowaudit check ./src -o report.html

      - name: Upload report
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: shadowaudit-report
          path: report.html
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No ungated high-risk tools found |
| `1` | Ungated high-risk tools found (`--fail-on-ungated` set) |
| `2` | Invalid arguments or path not found |

## Framework-specific checks

```bash
# Check only LangChain tools
shadowaudit check ./src --framework langchain

# Check only CrewAI tools
shadowaudit check ./src --framework crewai

# Check only OpenAI Agents SDK tools
shadowaudit check ./src --framework openai_agents
```

## Full risk assessment report

For a richer report with compliance mapping and remediation guidance:

```bash
shadowaudit assess ./src -o report.html
```

The assessment report includes:
- Executive summary
- Risk breakdown by tool and framework
- Compliance framework mapping (OWASP, EU AI Act)
- Remediation checklist

## Pre-commit hook

Add a pre-commit check so developers catch issues before pushing:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: shadowaudit-check
        name: ShadowAudit gate check
        entry: shadowaudit check --fail-on-ungated
        language: system
        types: [python]
```

## Related guides

- [Observe mode rollout](observe-mode-rollout.md)
- [Air-gapped deployments](air-gapped-deployments.md)
- [CLI reference](../reference/cli.md)
