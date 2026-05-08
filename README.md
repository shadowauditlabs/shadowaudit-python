# ShadowAudit

<p align="center">
  <strong>Runtime governance for AI agents — deterministic fail-closed enforcement with auditor-defensible cryptographic audit logs.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/v/shadowaudit?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/pyversions/shadowaudit" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/tests-205%20passed-brightgreen" alt="Tests: 205 passed">
</p>

---

ShadowAudit sits between your agent and its tools. It evaluates every call **before execution** and blocks anything that exceeds your risk threshold. Three things differentiate it from horizontal governance toolkits like Microsoft AGT: **(1) auditor-defensible cryptographic audit logs** — every decision is hash-chained and optionally Ed25519-signed, producing evidence conformity assessors accept; **(2) financial-vertical taxonomy depth** — built-in Stripe, Plaid, and fintech-specific risk categories out of the box; **(3) air-gap-first deployment** — single `pip install`, zero external calls, works inside isolated VPCs and on-prem.

```
Agent → ShadowAudit Gate → Tool (allowed)
                         → Blocked (AgentActionBlocked raised)
```

## Why ShadowAudit?

| Problem | ShadowAudit's Answer |
|---|---|
| Agents execute arbitrary shell commands | Keyword + regex + AST risk scoring with configurable thresholds |
| No audit trail for agent decisions | **Hash-chained, tamper-evident** SQLite audit log with SHA-256 linkage and optional Ed25519 signing |
| Can't prove compliance to auditors | Professional HTML reports with SOX/PCI-DSS mappings + **EU AI Act Annex IV evidence pack generator** |
| Agent behavior drifts over time | Adaptive scoring with behavioral state tracking (K/V metrics) |
| CI/CD deploys unsafe agents | `--fail-on-ungated` flag blocks deployments |
| Legal team blocks cloud-dependent tools | Works fully offline — zero external calls |
| EU AI Act Annex IV evidence required | Built-in evidence pack generator (JSON + HTML) |

### vs Microsoft Agent Governance Toolkit (AGT)

> "AGT is the right horizontal governance toolkit. ShadowAudit is the auditor-defensible, financial-vertical, air-gap-ready layer for regulated workloads. Run both — AGT for breadth, ShadowAudit for the audit evidence your conformity assessor will actually accept."
>
> See [docs/POSITIONING.md](docs/POSITIONING.md) for a detailed, honest comparison.

| Dimension | Microsoft AGT | ShadowAudit |
|---|---|---|
| License | MIT | MIT (OSS SDK) |
| Coverage | All 10 OWASP Agentic risks | 3–5 of 10, focused on **tool-call execution** |
| Vendor | Microsoft | **Independent** |
| **Audit log** | Standard logging | **Hash-chained, Ed25519-signed, tamper-evident** |
| **Vertical taxonomies** | Generic | **Financial / fintech depth** (Stripe, Plaid) |
| **Air-gap deployment** | Possible but assembly required | **First-class — single pip install** |
| **EU AI Act evidence pack** | Compliance module exists | **Annex IV evidence-pack generator built-in** |
| **Solo-buyable for SMBs** | No | **Yes** |

*Hosted dashboard and managed cloud tier in development — contact for early access.*

## Quick Start

```bash
pip install shadowaudit
```

### CLI — 3 commands to get started

```bash
# 1. Scan your codebase for ungated AI agent tools
shadowaudit check ./src

# 2. Generate a risk assessment with compliance mappings
shadowaudit assess ./src --taxonomy financial --compliance

# 3. Verify your audit log hasn't been tampered with
shadowaudit verify audit.db
```

For the full CLI reference (all 7 commands with flags and examples), see [docs/CLI.md](docs/CLI.md).

### Python API — wrap any tool in 5 lines

```python
from shadowaudit import Gate

gate = Gate()
result = gate.evaluate(
    agent_id="agent-1",
    task_context="shell_tool",
    risk_category="execute",
    payload={"command": "rm -rf /"},
)
print(result.passed)        # False
print(result.risk_score)    # 0.11 (varies by payload)
print(result.reason)        # "drift_detected"
```

Framework adapters: LangChain (`ShadowAuditTool`), CrewAI (`ShadowAuditCrewAITool`), LangGraph (`ShadowAuditToolNode`), OpenAI Agents SDK (`ShadowAuditOpenAITool`), and MCP (`MCPGatewayServer` + `ShadowAuditMCPSession`). See `examples/` for runnable scripts for each.

See [`examples/`](examples/) for runnable scripts covering every framework adapter.

## Features

### Tamper-Evident Audit
Every gate decision is recorded in an append-only SQLite log. Entries are **hash-chained** via SHA-256 — modify any row and the chain breaks. Optional **Ed25519 signing** cryptographically proves authenticity. Verified with `shadowaudit verify`.

### Vertical Taxonomies
Built-in starter packs for general, financial, legal, and **Plaid** workloads. Each taxonomy defines risk keywords, threshold deltas, severity levels, and compliance framework mappings. Build custom taxonomies interactively with `shadowaudit build-taxonomy`.

### Framework Coverage
First-class adapters for **LangChain**, **CrewAI**, **LangGraph**, **OpenAI Agents SDK**, and **MCP** (gateway + in-process). Drop-in wrappers — same interface, automatic enforcement. Works with any tool that has `name`, `description`, and `run()`.

### Compliance Reporting
Generate professional HTML reports with executive summaries, risk breakdowns, and remediation plans. Built-in **OWASP Agentic Top 10 coverage matrix** (`shadowaudit owasp`) and **EU AI Act Annex IV evidence pack generator** (`shadowaudit eu-ai-act`) for regulatory submission.

### Offline-First
No cloud. No LLM calls. No API keys. SQLite-backed state and audit log. Single `pip install shadowaudit` deploys everything needed for runtime governance inside air-gapped VPCs and on-prem environments.

### CI/CD Integration
`shadowaudit check --fail-on-ungated` exits non-zero if high-risk tools are ungated. Drop into any pipeline to block unsafe deploys. Trace simulator replays agent execution logs through the gate for regression testing.

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                      ShadowAudit                           │
├───────────┬───────────┬───────────┬───────────┬───────────┤
│  CLI      │ LangChain │  CrewAI   │  Direct   │  MCP      │
│  (click)  │  Adapter  │  Adapter  │   Gate    │  Gateway  │
├───────────┴───────────┴───────────┴───────────┴───────────┤
│                    Core Gate Engine                        │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐ │
│ │  Scorer   │ │  Taxonomy │ │    FSM    │ │  Audit Log │ │
│ │ pluggable │ │   Loader  │ │ fail-closed│ │Hash-chained│ │
│ └───────────┘ └───────────┘ └───────────┘ │  + Ed25519 │ │
│ ┌───────────┐ ┌───────────┐               └────────────┘ │
│ │   State   │ │   Hash    │                              │
│ │  (SQLite) │ │ (SHA-256) │                              │
│ └───────────┘ └───────────┘                              │
├───────────────────────────────────────────────────────────┤
│                  Assessment & Reporting                    │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐ │
│ │  Scanner  │ │  Reporter │ │ Simulator │ │   Builder  │ │
│ │           │ │  (Jinja2) │ │           │ │            │ │
│ └───────────┘ └───────────┘ └───────────┘ └────────────┘ │
└───────────────────────────────────────────────────────────┘
```

### How a tool call is evaluated

1. **Agent calls a tool** → intercepted by the framework adapter or direct `Gate.evaluate()`
2. **Taxonomy lookup** → finds risk category config (keywords, threshold delta, severity)
3. **Scoring** → pluggable scorer computes risk score from payload content
4. **Threshold comparison** → score vs. taxonomy delta determines pass/fail
5. **FSM transition** → fail-closed state machine: anything not an explicit pass is a block
6. **Audit log** → decision recorded with timestamp, agent ID, payload hash, and reason

## Installation

```bash
# Base install — CLI + core gate (click, jinja2)
pip install shadowaudit

# With LangChain adapter
pip install shadowaudit[langchain]

# With CrewAI adapter (Python 3.10–3.12)
pip install shadowaudit[crewai]

# Development
pip install shadowaudit[dev]
```

**Requirements:** Python 3.10+

## Examples

See the [`examples/`](examples/) directory for runnable scripts:

| Example | Description |
|---|---|
| [`local_only.py`](examples/local_only.py) | Direct Gate usage — no framework dependencies |
| [`langchain_agent.py`](examples/langchain_agent.py) | LangChain agent with ShadowAudit-wrapped tools |
| [`hash_chain_demo.py`](examples/hash_chain_demo.py) | Hash-chained audit log with tamper detection |
| [`langgraph_demo.py`](examples/langgraph_demo.py) | LangGraph `ShadowAuditToolNode` integration |
| [`eu_ai_act_demo.py`](examples/eu_ai_act_demo.py) | EU AI Act Annex IV evidence pack generation |

Run all examples at once:

```bash
python examples/run_all_examples.py
```

For the full example index (12 scripts covering every v0.4.0 feature), see [`docs/FEATURES.md`](docs/FEATURES.md).

## Testing

Quick smoke test after installing:

```bash
shadowaudit --version && \
shadowaudit check . && \
shadowaudit owasp && \
python -c "from shadowaudit.core.gate import Gate; print(Gate().evaluate({'tool':'read'}).passed)"
```

For the full testing guide, see [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md).

## Project Status

ShadowAudit is **v0.4.0 — production-ready for audit-time scanning and assessment workflows; runtime gating is in early-adopter use.** APIs may evolve before v1.0.0; breaking changes require a major version bump and migration guide.

- ✅ Core gate + 5 framework adapters (LangChain, CrewAI, LangGraph, OpenAI Agents, MCP)
- ✅ Hash-chained, Ed25519-signed audit log with integrity verification
- ✅ Vertical taxonomies (general, financial, legal, Plaid) + interactive builder
- ✅ Compliance reporting (OWASP matrix, EU AI Act Annex IV evidence packs)
- ✅ Offline-first — zero external calls, air-gap ready

## Contributing

Bug reports and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and the PR process.

```bash
git clone https://github.com/AnshumanKumar14/shadowaudit-python.git
cd shadowaudit-python
pip install -e ".[dev,langchain]"
pytest tests/ -q
```

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built by <a href="https://github.com/AnshumanKumar14">Anshuman Kumar</a></sub>
</p>
