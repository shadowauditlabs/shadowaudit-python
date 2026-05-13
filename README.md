# ShadowAudit

<p align="center">
  <strong>Deterministic, fail-closed runtime authorization for AI agents.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/v/shadowaudit?color=blue" alt="PyPI version"></a>
  <a href="https://img.shields.io/pypi/pyversions/shadowaudit"><img src="https://img.shields.io/pypi/pyversions/shadowaudit" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/tests-253%20passed-brightgreen" alt="Tests: 253 passed">
</p>

ShadowAudit sits between AI agents and their tools to enforce deterministic authorization before execution happens. It is runtime governance infrastructure: closer to IAM, Open Policy Agent, admission controllers, and API gateways than prompt guardrails or moderation.

Documentation: https://shadowauditlabs.github.io/shadowaudit-python/

```text
Agent → ShadowAudit → Tool
          │
          ├─ Allow
          ├─ Deny
          └─ Require approval
```

## What It Does

ShadowAudit enforces explicit, policy-as-code decisions at the point where tool execution actually happens. If a tool call is not authorized, it does not run.

Example: a finance agent can read invoices freely, but a `payments.transfer` call over `$1,000` is paused for approval, and a shell command like `rm -rf /var/lib/postgresql` is denied before it runs.

## Installation

```bash
pip install shadowaudit
```

## Quickstart

```python
from shadowaudit import ShadowAuditTool
from langchain.tools import ShellTool

safe_tool = ShadowAuditTool(
    tool=ShellTool(),
    agent_id="ops-agent",
    capability="shell.execute",
    policy_path="policies/production_shell_policy.yaml"
)
```

Example policy:

```yaml
deny:
  - capability: filesystem.delete
  - capability: shell.root_access

require_approval:
  - capability: payments.transfer
    amount_gt: 1000

allow:
  - capability: filesystem.read
```

Full walkthrough: docs/getting-started/quickstart.md

## Integrations

- LangChain
- LangGraph
- CrewAI
- OpenAI Agents SDK
- MCP
- Direct Python APIs

## Direct Gate API

Use the core gate directly when you want ShadowAudit inside your own runtime, framework adapter, MCP gateway, or infrastructure workflow.

```python
from shadowaudit.core.gate import Gate

gate = Gate()

result = gate.evaluate(
    agent_id="ops-agent-1",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path="policies/production_shell_policy.yaml",
    payload={"command": "rm -rf /var/lib/postgresql"}
)

if not result.passed:
    print("BLOCKED")
    print(f"Capability: shell.execute")
    print(f"Decision: denied")
    print(f"Reason: {result.reason}")
```

Reference: docs/reference/gate-api.md

## Features

- Deterministic, fail-closed runtime authorization
- Policy-as-code with explicit allow/deny/approval rules
- Offline-first enforcement with no LLM dependency in the gate path
- Tamper-evident audit log with replayable decisions
- Approval workflows for sensitive actions
- Observe mode for safe rollout
- CI checks for ungated tools

## Architecture and Concepts

- docs/concepts/runtime-authorization.md
- docs/concepts/audit-chain.md
- docs/architecture/enforcement-flow.md

## Examples

- docs/examples/fintech-agent.md
- examples/ (runnable demos)

```bash
python examples/core_concepts/run_all_examples.py
```

## Contributing

```bash
git clone https://github.com/AnshumanKumar14/shadowaudit-python.git

cd shadowaudit-python

pip install -e ".[dev]"

pytest tests/ -q
```

Bug reports, governance plugins, framework adapters, and policy contributions are welcome.

## License

MIT License

<p align="center">
  <sub>Built by <a href="https://github.com/AnshumanKumar14">Anshuman Kumar</a></sub>
</p>
