# ShadowAudit

ShadowAudit is a deterministic runtime authorization layer for AI agent tool calls.

It sits between an agent and its tools, evaluates each attempted tool call against policy, and blocks unauthorized actions before execution.

```text
Agent -> ShadowAudit -> Tool
          |
          +-- allow
          +-- deny
          +-- require approval
```

ShadowAudit is built for teams shipping agents that can touch shells, databases, payment APIs, filesystems, MCP servers, SaaS admin APIs, or other sensitive systems.

## Why it exists

Prompt guardrails and model instructions are useful, but they are not an execution boundary. ShadowAudit treats tool execution like infrastructure authorization: explicit policy, deterministic decisions, audit logs, replay, and fail-closed behavior.

## What it does

- Enforces policy-as-code before tool calls run.
- Supports allow, deny, default-deny, and approval-required decisions.
- Works offline with no LLM call in the gate path.
- Records decisions in a local SQLite audit log.
- Verifies audit integrity with a hash chain and optional signing.
- Supports observe mode for staged rollout.
- Scans Python projects for ungated agent tools.
- Replays traces through policy changes.
- Integrates with LangChain, LangGraph, CrewAI, OpenAI Agents SDK, MCP, and direct Python APIs.

## What it does not do

- It does not replace sandboxing for dangerous tools.
- It does not guarantee prompt-injection prevention.
- It does not prove that a model's reasoning is safe.
- It does not turn synthetic benchmark results into production detection guarantees.
- It does not remove the need for least-privilege credentials and network controls.

Use ShadowAudit as the runtime authorization and audit layer alongside those controls.

## Five-minute path

Install:

```bash
pip install shadowaudit
```

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

Evaluate a tool call:

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

## Common workflows

- Start with [Installation](getting-started/installation.md).
- Run the [Quickstart](getting-started/quickstart.md).
- Write [your first policy](getting-started/first-policy.md).
- See [your first blocked action](getting-started/first-blocked-action.md).
- Use [recipes](recipes/index.md) for copy-paste policy patterns.
- Roll out safely with [observe mode](guides/observe-mode-rollout.md).
- Protect [shell tools](guides/protect-shell-tools.md), [payment agents](guides/protect-payment-agents.md), and [MCP servers](guides/secure-mcp-servers.md).
- Use [CI/CD enforcement](guides/ci-cd-enforcement.md) to catch ungated tools.
- Replay an incident with [trace replay](guides/replay-an-incident.md).
- Check the [compatibility matrix](integrations/compatibility.md) before wiring adapters.
- Run the [demo walkthrough](examples/demo-walkthrough.md).
- Record or play the [demo cast](examples/demo-cast.md).

## Trust model

ShadowAudit is strongest when you define explicit capabilities and policies. Risk scoring can help with suspicious payloads, but the primary control should be policy-first authorization: what capability is being requested, under what context, and whether that action is allowed.

For architecture details, see:

- [Runtime authorization](concepts/runtime-authorization.md)
- [Policy model](concepts/policy-model.md)
- [Fail-closed enforcement](concepts/fail-closed-enforcement.md)
- [Audit chain](concepts/audit-chain.md)
- [Threat model](architecture/threat-model.md)
