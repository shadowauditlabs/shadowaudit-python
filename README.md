# ShadowAudit

<p align="center">
  <strong>Runtime safety for AI agents — fail-closed gating on every tool call, before execution.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/v/shadowaudit?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/shadowaudit/"><img src="https://img.shields.io/pypi/pyversions/shadowaudit" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/tests-226%20passed-brightgreen" alt="Tests: 226 passed">
</p>

---

Your AI agent has tools that can do real damage — shell commands, payment APIs, database writes, MCP servers. ShadowAudit sits between the agent and its tools, scores every call against your risk taxonomy, and fail-closed blocks anything dangerous before execution. Deterministic. No LLM in the gate path. Works air-gapped. Hash-chained audit logs for when compliance or regulators ask.

```
Agent → ShadowAudit Gate → Tool (allowed)
                         → Blocked (AgentActionBlocked raised)
```

## Live integration example

For a full production-shaped fintech agent integration — sync + async + multi-agent FlowTracer + LangChain + LangGraph + all 6 taxonomies + OWASP + EU AI Act Annex IV — see:

→ [**shadowaudit-showcase**](https://github.com/AnshumanKumar14/shadowaudit-showcase)

Clone, `pip install -e ".[dev]"`, run `showcase`, and watch ShadowAudit gate a realistic payment agent in under a minute.

## Beyond the OSS

ShadowAudit is open-source and free today, with a deterministic local gate, hash-chained audit log, and full taxonomy and reporting stack.

A managed cloud tier (hosted dashboard, fleet telemetry, one-click compliance exports) and an air-gapped enterprise deployment (designed for sovereign banking and regulated workloads with cryptographic evidence kernels) are in development. If you have a specific need, [reach out](mailto:hello@shadowaudit.dev) — early-access conversations are open.

## Why ShadowAudit?

| Problem | ShadowAudit's Answer |
|---|---|
| Agents execute arbitrary shell commands, payment APIs, and database writes | Keyword + regex + AST risk scoring with configurable thresholds |
| Agent behavior drifts over time | Adaptive scoring with behavioral state tracking (K/V metrics) |
| CI/CD deploys unsafe agents | `--fail-on-ungated` flag blocks deployments |
| Legal team blocks cloud-dependent tools | Works fully offline — zero external calls |
| No audit trail for agent decisions | **Hash-chained, tamper-evident** SQLite audit log with SHA-256 linkage and optional Ed25519 signing |
| Can't prove compliance to auditors | Professional HTML reports with SOX/PCI-DSS mappings + **EU AI Act Annex IV evidence pack generator** |
| EU AI Act Annex IV evidence required | Built-in evidence pack generator (JSON + HTML) |

### For AI engineers and SREs

You have agents in production with tools that can do real damage. ShadowAudit gives you a single pip install that adds fail-closed safety to LangChain, CrewAI, LangGraph, OpenAI Agents, and MCP tool calls. Zero LLM calls in the gate path. Sub-millisecond. Works offline.

### For compliance and security leads

When regulators or auditors ask how your AI agents make decisions, ShadowAudit's hash-chained, optionally signed audit log produces evidence that survives forensic review. OWASP Agentic Top 10 coverage built in. EU AI Act Annex IV evidence pack generator available.


## Quick Start

```bash
pip install shadowaudit
```

### CLI — first commands to try

```bash
# 1. Scan your codebase for ungated AI agent tools
shadowaudit check ./src

# 2. Generate a risk assessment with compliance mappings
shadowaudit assess ./src --taxonomy financial --compliance

# 3. Verify your audit log hasn't been tampered with
shadowaudit verify audit.db

# 4. Analyse decisions and get threshold tuning suggestions
shadowaudit tune --audit-log audit.db
```

For the full CLI reference (all 8 commands with flags and examples), see [docs/CLI.md](docs/CLI.md).

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
Every gate decision is recorded in an append-only SQLite log. Entries are **hash-chained** via SHA-256 — modify any row and the chain breaks. Optional **Ed25519 signing** cryptographically proves authenticity. Verified with `shadowaudit verify`. See [`examples/tamper_demo.py`](examples/tamper_demo.py) for a live demonstration.

### Observe Mode & Bypass
Roll out enforcement gradually with `Gate(mode="observe")`: decisions are logged but never blocked, and `result.metadata["would_have_blocked"]` tells you what enforce mode would have done. For human-approved overrides, use the `bypass()` context manager — every bypass is recorded in the audit log with a mandatory reason string.

```python
# Shadow mode — log everything, block nothing
gate = Gate(mode="observe")
result = gate.evaluate(agent_id, task, category, payload)
print(result.metadata["would_have_blocked"])   # True if enforce would have blocked

# Bypass with immutable audit trail
with gate.bypass("agent-1", reason="approved by oncall #4521"):
    result = gate.evaluate("agent-1", task, category, payload)
```

Use `shadowaudit tune --audit-log audit.db` to analyse block rates per category and get threshold adjustment suggestions.

### Multi-Agent Trust Propagation
`FlowTracer` tracks how data moves between agents and propagates trust downward. If Agent A processes untrusted web content, any payload that flows from A into Agent B's tool call is automatically tagged `UNTRUSTED` — regardless of B's own trust level.

```python
from shadowaudit import FlowTracer, TrustLevel

tracer = FlowTracer()
tracer.record_output("web-scraper", scraped_data, trust=TrustLevel.UNTRUSTED)
tracer.record_flow("web-scraper", "summariser", parsed_data)

annotation = tracer.annotate(
    receiving_agent="payment-agent",
    source_agents=["summariser"],
    declared_trust=TrustLevel.SYSTEM,
)
print(annotation.effective_trust)   # TrustLevel.UNTRUSTED
print(annotation.contaminated_by)   # ['web-scraper']
```

### Vertical Taxonomies
Built-in starter packs across **6 domains**: general, financial (32 categories — Stripe, Plaid, wire transfers, KYC/AML), financial crypto (18 categories), healthcare (17 categories), legal, and open banking. Each taxonomy defines risk keywords, threshold deltas, severity levels, and compliance mappings. Build custom taxonomies interactively with `shadowaudit build-taxonomy`.

### Framework Coverage
First-class adapters for **LangChain**, **CrewAI**, **LangGraph**, **OpenAI Agents SDK**, and **MCP** (gateway + in-process). Drop-in wrappers — same interface, automatic enforcement. Works with any tool that has `name`, `description`, and `run()`.

### Compliance Reporting
Generate professional HTML reports with executive summaries, risk breakdowns, and remediation plans. Built-in **OWASP Agentic Top 10 coverage matrix** (`shadowaudit owasp`) and **EU AI Act Annex IV evidence pack generator** (`shadowaudit eu-ai-act`) for regulatory submission. For an honest account of what ShadowAudit catches and misses, see [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).

### Offline-First
No cloud. No LLM calls. No API keys. SQLite-backed state and audit log. Single `pip install shadowaudit` deploys everything needed for runtime governance inside air-gapped VPCs and on-prem environments.

### CI/CD Integration
`shadowaudit check --fail-on-ungated` exits non-zero if high-risk tools are ungated. Drop into any pipeline to block unsafe deploys. Trace simulator replays agent execution logs through the gate for regression testing. A labelled corpus of 130 traces (50 benign / 50 risky / 30 edge cases) in `tests/corpus/` lets you validate scoring changes before shipping.

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
5. **Mode / bypass check** → observe mode always passes; active `bypass()` overrides a block
6. **FSM transition** → fail-closed state machine: anything not an explicit pass is a block
7. **Audit log** → decision recorded with timestamp, agent ID, payload hash, and reason

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

See the [`examples/`](examples/) directory for runnable scripts and the [**shadowaudit-showcase**](https://github.com/AnshumanKumar14/shadowaudit-showcase) repo for interactive demos and real-world scenarios:

| Example | Description |
|---|---|
| [`local_only.py`](examples/local_only.py) | Direct Gate usage — no framework dependencies |
| [`langchain_agent.py`](examples/langchain_agent.py) | LangChain agent with ShadowAudit-wrapped tools |
| [`hash_chain_demo.py`](examples/hash_chain_demo.py) | Hash-chained audit log with tamper detection |
| [`tamper_demo.py`](examples/tamper_demo.py) | Live tamper-evidence demo: corrupt a row, watch the chain break |
| [`fintech_payment_agent.py`](examples/fintech_payment_agent.py) | Production-style payment agent with Gate enforcement and retry logic |
| [`langgraph_demo.py`](examples/langgraph_demo.py) | LangGraph `ShadowAuditToolNode` integration |
| [`eu_ai_act_demo.py`](examples/eu_ai_act_demo.py) | EU AI Act Annex IV evidence pack generation |

Run all examples at once:

```bash
python examples/run_all_examples.py
```

> The 7 examples above are the recommended starting points. The `examples/` directory contains 15 scripts total covering every v0.4.0 feature; see [`docs/FEATURES.md`](docs/FEATURES.md) for the full index.

## Testing

Quick smoke test after installing:

```bash
shadowaudit --version && shadowaudit check . && shadowaudit owasp && python -c "from shadowaudit.core.gate import Gate; print(Gate().evaluate({'tool':'read'}).passed)"
```

For the full testing guide, see [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md).

## Project Status

ShadowAudit is **v0.4.0 — production-ready for runtime gating and audit-time scanning workflows.** APIs may evolve before v1.0.0; breaking changes require a major version bump and a migration guide.

- ✅ Core gate + 5 framework adapters (LangChain, CrewAI, LangGraph, OpenAI Agents, MCP)
- ✅ Hash-chained, Ed25519-signed audit log with integrity verification
- ✅ Observe mode, bypass context manager, and threshold tuning CLI
- ✅ Multi-agent trust propagation via `FlowTracer`
- ✅ Vertical taxonomies (general, financial 32-cat, financial_crypto, healthcare, legal, Plaid) + interactive builder
- ✅ Labelled test corpus (130 traces) + scorer benchmark
- ✅ Compliance reporting (OWASP matrix, EU AI Act Annex IV evidence packs)
- ✅ Honest threat model — what ShadowAudit catches and what it doesn't ([docs/THREAT_MODEL.md](docs/THREAT_MODEL.md))
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
