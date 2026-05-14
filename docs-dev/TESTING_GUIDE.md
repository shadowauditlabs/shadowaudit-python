# Testing ShadowAudit v0.4.0 — User Guide

This guide shows you how to test every feature in ShadowAudit v0.4.0, whether you installed from PyPI or cloned the repo.

---

## 1. Install ShadowAudit

### From PyPI (recommended for users)

```bash
pip install shadowaudit
```

### From source (for contributors)

```bash
git clone https://github.com/shadowauditlabs/shadowaudit-python.git
cd shadowaudit-python
pip install -e ".[dev]"
```

Verify installation:

```bash
shadowaudit --version
# Expected: 0.4.0
```

---

## 2. Run the Full Test Suite

If you cloned the repo, run the built-in tests:

```bash
python -m pytest tests/ -q
```

Expected output:

```
205 passed, 1 skipped
```

The 1 skipped test is for `pytest-asyncio` (optional dependency). Everything else should pass.

---

## 3. Run the Example Scripts

The `examples/` directory has runnable demos for every feature. If you cloned the repo:

```bash
# Run all examples at once
python examples/run_all_examples.py
```

Or run individual examples:

```bash
# Week 7a — Hash-chained audit log with tamper detection
python examples/hash_chain_demo.py

# Week 7b — Ed25519 signing and verification
python examples/ed25519_signing_demo.py

# Week 8 — OWASP Agentic Top 10 coverage report
python examples/owasp_report_demo.py

# Week 9 — MCP gateway and adapter
python examples/mcp_gateway_demo.py

# Week 10 — LangGraph integration
python examples/langgraph_demo.py

# Week 10 — OpenAI Agents SDK integration
python examples/openai_agents_demo.py

# Week 11 — EU AI Act evidence pack
python examples/eu_ai_act_demo.py

# Week 12 — Plaid taxonomy pack
python examples/plaid_taxonomy_demo.py

# Week 13 — Telemetry client (opt-in)
python examples/telemetry_demo.py
```

> **Note:** If you installed from PyPI (not cloned), copy the example files to your project first, or run them from the GitHub repo.

---

## 4. Test the CLI on Your Own Project

### 4.1 Static scan — find ungated tools

```bash
# Scan current directory
cd your-agent-project/
shadowaudit check .

# Scan specific path
shadowaudit check src/

# Generate HTML report
shadowaudit check . --output report.html
```

Expected: lists all tool classes/functions and flags any that are **not** wrapped with ShadowAudit.

### 4.2 Full assessment — risk score + taxonomy

```bash
shadowaudit assess . --taxonomy general --compliance
```

Generates `shadowaudit-compliance-report.html` with:
- Tool inventory
- Risk scores
- Compliance mappings (PCI-DSS, SOC-2, GDPR)

### 4.3 OWASP coverage matrix

```bash
shadowaudit owasp --output owasp-report.html
```

Generates an HTML report showing which of the OWASP Agentic AI Top 10 risks your project covers.

### 4.4 EU AI Act evidence pack

```bash
shadowaudit eu-ai-act . --taxonomy general --system-name "MyAgent" --output eu-ai-act-pack.html
```

Generates both `eu-ai-act-pack.html` and `eu-ai-act-pack.json` for regulatory submission.

### 4.5 Verify audit log integrity

```bash
shadowaudit verify audit.db
```

Checks the hash chain for tampering. Returns `VALID` or lists broken entries.

### 4.6 Simulate agent traces

```bash
shadowaudit simulate traces.jsonl --taxonomy general --compare
```

Replays a JSONL trace file through static vs. adaptive scoring and shows the difference.

---

## 5. Test Individual Features in Code

### 5.1 Core Gate — block dangerous commands

```python
from shadowaudit.core.gate import Gate

gate = Gate(taxonomy="general")

# Safe — allowed
result = gate.evaluate({"tool": "read_balance", "account": "123"})
print(result.passed)  # True

# Dangerous — blocked
result = gate.evaluate({"tool": "shell", "command": "rm -rf /"})
print(result.passed)   # False
print(result.reason)   # "drift_detected"
```

### 5.2 Hash chain — tamper-evident audit log

```python
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.chain import verify_chain_from_rows

logger = AuditLogger("audit.db")
logger.record(tool="pay", payload={"to": "alice", "amount": 100}, decision="pass")
logger.record(tool="pay", payload={"to": "bob", "amount": 200}, decision="pass")

# Verify integrity
rows = logger.get_events_chronological()
ok, errors = verify_chain_from_rows(rows)
print(ok)  # True
```

### 5.3 Ed25519 signing — cryptographically signed entries

```python
from shadowaudit.core.keys import generate_keypair, ensure_keypair
from shadowaudit.core.audit import AuditLogger

# One-time setup
pub, priv = generate_keypair()

# All future entries signed
logger = AuditLogger("signed-audit.db", sign_entries=True)
logger.record(tool="pay", payload={"amount": 999}, decision="block")

# Verify
ok, errors = logger.verify()
print(ok)  # True
```

### 5.4 LangChain wrapper

```python
from shadowaudit.framework.langchain import ShadowAuditTool
from langchain.tools import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    def _run(self, query: str):
        return f"Result: {query}"

# Wrap it
wrapped = ShadowAuditTool(MyTool(), agent_id="agent-1")
wrapped.run("safe query")  # Works
wrapped.run("rm -rf /")    # Raises AgentActionBlocked
```

### 5.5 LangGraph wrapper

```python
from shadowaudit.framework.langgraph import ShadowAuditToolNode

# Replace your ToolNode with this
node = ShadowAuditToolNode(
    tools=[read_tool, pay_tool],
    agent_id="langgraph-agent-1"
)

# In your graph: node(state) — blocks dangerous calls automatically
```

### 5.6 CrewAI wrapper

```python
from shadowaudit.framework.crewai import ShadowAuditCrewAITool
from crewai.tools import BaseTool

class PayTool(BaseTool):
    name = "pay"
    def _run(self, amount: int):
        return f"Paid {amount}"

wrapped = ShadowAuditCrewAITool(PayTool(), agent_id="crew-1")
wrapped.run("100")   # Works
wrapped.run("99999") # Blocked if over threshold
```

### 5.7 MCP Gateway

```python
from shadowaudit.mcp.gateway import MCPGatewayServer

# Proxy any MCP server through ShadowAudit
gateway = MCPGatewayServer(
    command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    agent_id="mcp-agent-1"
)
gateway.run()  # Blocks dangerous tool calls over stdio
```

### 5.8 MCP In-Process Adapter

```python
from shadowaudit.mcp.adapter import ShadowAuditMCPSession

# Wrap an existing MCP client session
session = ShadowAuditMCPSession(real_mcp_session, agent_id="mcp-agent-2")
result = await session.call_tool("read_file", {"path": "/etc/passwd"})
```

### 5.9 OpenAI Agents SDK wrapper

```python
from shadowaudit.framework.openai_agents import ShadowAuditOpenAITool

# Wrap an OpenAI Agents tool
read_tool = ShadowAuditOpenAITool(
    name="read_data",
    description="Read user data",
    risk_category="read_only",
    agent_id="openai-agent-1"
)

# The on_invoke_tool method is called by the Agents SDK
# ShadowAudit blocks dangerous inputs automatically
```

### 5.10 OWASP coverage check

```python
from shadowaudit.assessment.owasp import generate_owasp_context

ctx = generate_owasp_context()
print(f"Coverage: {ctx['coverage_percent']}%")
print(f"Covered: {ctx['covered_count']}/{ctx['total_count']}")
```

### 5.11 EU AI Act evidence pack

```python
from shadowaudit.assessment.eu_ai_act import generate_evidence_pack
from shadowaudit.assessment.scanner import scan_assessment

data = scan_assessment(".", taxonomy="general")
pack = generate_evidence_pack(data, system_name="MyAgent", version="1.0.0")

pack.write_json("evidence.json")
pack.write_html("evidence.html")
```

### 5.12 Plaid taxonomy

```python
from shadowaudit.core.taxonomy import TaxonomyLoader

tax = TaxonomyLoader.load("financial_plaid")
print(tax["categories"].keys())  # 10 Plaid-specific categories
```

### 5.13 Telemetry (opt-in)

```python
import os
from shadowaudit.telemetry.client import TelemetryClient

# Opt-in via environment variable
os.environ["SHADOWAUDIT_TELEMETRY"] = "1"

client = TelemetryClient(agent_id="agent-1")
client.start()

# Decisions are queued and sent async (hashed metadata only)
await client.send_decision(tool="pay", decision="pass")
await client.stop()
```

---

## 6. Test on the Demo Project

A realistic fintech agent is included for end-to-end testing:

```bash
cd shadowaudit-demo/

# Install demo dependencies
pip install -e ".[dev]"

# Run ShadowAudit scanner
shadowaudit check src/

# Run assessment
shadowaudit assess src/ --taxonomy financial --compliance

# Run demo tests
python -m pytest tests/
```

The demo has 8 tools, 2 intentionally ungated — perfect for validating the scanner.

---

## 7. Quick Reference — What to Test

| Feature | Test Command | Expected Result |
|---|---|---|
| Install | `shadowaudit --version` | `0.4.0` |
| Unit tests | `pytest tests/ -q` | `205 passed, 1 skipped` |
| Examples | `python examples/run_all_examples.py` | `9/9 passed` |
| Static scan | `shadowaudit check .` | Lists tools, flags ungated |
| Assessment | `shadowaudit assess .` | HTML report generated |
| OWASP | `shadowaudit owasp` | Coverage matrix HTML |
| EU AI Act | `shadowaudit eu-ai-act .` | Evidence pack JSON + HTML |
| Audit verify | `shadowaudit verify audit.db` | `VALID` or tamper details |
| Hash chain | `python examples/hash_chain_demo.py` | Tamper detected after edit |
| Ed25519 | `python examples/ed25519_signing_demo.py` | Signature valid |

---

## 8. Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: shadowaudit` | Install with `pip install -e .` from repo root, or set `PYTHONPATH=/path/to/repo` |
| `shadowaudit: command not found` | Ensure your Python scripts directory is on `PATH`, or use `python -m shadowaudit.cli` |
| `1 skipped` in tests | Install `pytest-asyncio` if you want to run async tests: `pip install pytest-asyncio` |
| FastAPI tests skipped | Install `fastapi` if testing Cloud API: `pip install fastapi` |
| Examples fail from PyPI install | Copy example files locally, or clone the repo |

---

## 9. One-Liner Smoke Test

Run this after installing to verify everything works:

```bash
shadowaudit --version && \
shadowaudit check . && \
shadowaudit owasp && \
python -c "from shadowaudit.core.gate import Gate; print(Gate().evaluate({'tool':'read'}).passed)"
```

If all four commands succeed, your ShadowAudit installation is healthy.
