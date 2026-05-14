# ShadowAudit

<p align="center">
  <strong>Deterministic runtime authorization for AI agent tool calls.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/v/shadowaudit?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/pyversions/shadowaudit" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/tests-passing-brightgreen" alt="Tests: passing">
</p>

ShadowAudit sits between AI agents and their tools. It evaluates every tool call against deterministic policy before execution, then allows it, blocks it, or requires approval.

It is closer to IAM, Open Policy Agent, API gateways, and admission controllers than prompt guardrails or moderation.

```text
Agent -> ShadowAudit -> Tool
          |
          +-- allow
          +-- deny
          +-- require approval
```

## Why This Exists

Agents increasingly call tools that can move money, edit databases, run shell commands, read files, modify permissions, and operate SaaS admin APIs.

Prompt instructions are not an execution boundary. ShadowAudit gives those tool calls an explicit runtime authorization layer:

- No LLM call in the gate path.
- Policy-as-code decisions.
- Default-deny behavior when policy does not match.
- Fail-closed handling for policy and audit failures.
- Local audit logs with hash-chain verification.
- Observe mode for safe rollout before enforcement.

## Install

```bash
pip install shadowaudit
```

## 60-Second Example

Create a policy:

```yaml
deny:
  - capability: shell.execute
    contains: "rm -rf"

require_approval:
  - capability: payments.transfer
    amount_gt: 1000

allow:
  - capability: shell.execute
  - capability: payments.transfer
    amount_lte: 1000
```

Evaluate a tool call before execution:

```python
from shadowaudit.core.gate import Gate

gate = Gate()

result = gate.evaluate(
    agent_id="ops-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path="policies/shell_agent.yaml",
    payload={"command": "rm -rf /var/lib/postgresql"},
)

if not result.passed:
    raise PermissionError(f"Blocked: {result.reason}")
```

The dangerous command never reaches the tool.

## Framework Integrations

ShadowAudit can wrap tools in:

- LangChain
- LangGraph
- CrewAI
- OpenAI Agents SDK
- MCP
- PydanticAI
- LlamaIndex
- AutoGen
- Direct Python runtimes

LangChain example:

```python
from shadowaudit import ShadowAuditTool
from langchain.tools import ShellTool

safe_shell = ShadowAuditTool(
    tool=ShellTool(),
    agent_id="ops-agent",
    capability="shell.execute",
    policy_path="policies/shell_agent.yaml",
)
```

## CLI Workflows

Scan for ungated tools:

```bash
shadowaudit check ./src --fail-on-ungated
```

Validate a policy:

```bash
shadowaudit check-policy policies/shell_agent.yaml
```

Replay a trace through policy:

```bash
shadowaudit simulate --trace-file traces/agent_trace.jsonl --compare
```

Verify audit-log integrity:

```bash
shadowaudit verify --audit-log audit.db
```

## Rollout Path

1. Start in observe mode and log decisions without blocking.
2. Review audit logs and tune policies.
3. Enforce policy for high-risk tools.
4. Add CI checks so new ungated tools cannot quietly ship.
5. Replay incidents and policy changes against saved traces.

## What ShadowAudit Is Not

ShadowAudit is a runtime authorization and audit layer. It does not replace:

- sandboxing for shell/code execution
- least-privilege credentials
- network egress controls
- prompt-injection defenses
- human review for genuinely ambiguous high-risk actions

Use it as the deterministic control point before tool execution.

## Why Not Prompt Guardrails?

Prompt guardrails are useful, but they do not enforce execution. A prompt can be bypassed, misinterpreted, or ignored under pressure. ShadowAudit adds a deterministic enforcement boundary that blocks tool calls before they execute and records a tamper-evident audit trail.

## Where It Sits In Your Stack

```
Agent framework -> ShadowAudit gate -> Tool/API/DB/Shell
```

ShadowAudit does not replace sandboxing, network egress controls, or least-privilege credentials. It complements them by enforcing runtime policy at the tool boundary.

## Project Status

ShadowAudit is beta infrastructure for agent tool governance. The repo includes:

- deterministic gate and policy engine
- local audit log with hash-chain verification
- approval workflows
- observe mode and bypass audit trails
- framework adapters
- MCP gateway and adapter
- static scanner and CI mode
- OWASP Agentic Top 10 and EU AI Act evidence reports
- typed Python package with ruff, mypy, and pytest coverage

Current local verification: run `pytest -q`.

## Documentation

- Docs: https://shadowaudit.dev/
- PyPI: https://pypi.org/project/shadowaudit/
- Repository: https://github.com/shadowauditlabs/shadowaudit-python

Useful starting points:

- [Quickstart](docs/getting-started/quickstart.md)
- [First policy](docs/getting-started/first-policy.md)
- [Recipes](docs/recipes/index.md)
- [Compatibility matrix](docs/integrations/compatibility.md)
- [Protect shell tools](docs/guides/protect-shell-tools.md)
- [Protect payment agents](docs/guides/protect-payment-agents.md)
- [Secure MCP servers](docs/guides/secure-mcp-servers.md)
- [Demo walkthrough](docs/examples/demo-walkthrough.md)
- [Demo cast](docs/examples/demo-cast.md)
- [Policy schema](docs/reference/policy-schema.md)

## Contributing

```bash
git clone https://github.com/shadowauditlabs/shadowaudit-python.git
cd shadowaudit-python
pip install -e ".[dev]"
pytest tests/ -q
```

Policy recipes, framework adapters, taxonomies, docs, and focused bug reports are welcome.

## License

MIT License

<p align="center">
  <sub>Built by <a href="https://github.com/shadowauditlabs">ShadowAudit Labs</a></sub>
</p>
