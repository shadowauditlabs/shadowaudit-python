# ShadowAudit CLI Reference

## Installation

```bash
pip install shadowaudit
```

All commands are available via the `shadowaudit` entry point.

---

## `shadowaudit check`

Statically scan a Python codebase for ungated AI agent tools.

### Synopsis

```
shadowaudit check [OPTIONS] [PATH]
```

### Description

Parses Python files with the AST module, identifies tool classes and functions (LangChain `BaseTool`, CrewAI `BaseTool`, or function-based tools), and flags any that are **not** wrapped with a ShadowAudit adapter. Supports cross-file wrapper detection — a tool defined in `tools.py` and wrapped in `agent.py` is correctly detected as gated.

### Options

| Flag | Description |
|---|---|
| `PATH` | Directory or file to scan. Defaults to current directory `.` |
| `-o, --output PATH` | Write HTML report to file |
| `--framework TEXT` | Filter findings by framework (`langchain`, `crewai`, `openai_agents`, `mcp`) |
| `--exclude-dir TEXT` | Exclude directories (default: `venv`, `.venv`, `__pycache__`, `.git`) |
| `--fail-on-ungated` | Exit with non-zero code if high-risk ungated tools are found |

### Examples

```bash
# Scan current directory
shadowaudit check

# Scan specific path with HTML report
shadowaudit check ./src -o report.html

# CI/CD — block deploy if ungated tools exist
shadowaudit check ./src --fail-on-ungated

# Filter to LangChain tools only
shadowaudit check ./src --framework langchain
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Scan completed, no ungated high-risk tools (or `--fail-on-ungated` not set) |
| 1 | `--fail-on-ungated` set and ungated high-risk tools found |
| 2 | Invalid arguments or path not found |

---

## `shadowaudit assess`

Full risk assessment with taxonomy enrichment and compliance mapping.

### Synopsis

```
shadowaudit assess [OPTIONS] PATH
```

### Description

Runs the static scanner, enriches findings with taxonomy data (risk keywords, thresholds, compliance frameworks), and generates a professional HTML report with executive summary, risk breakdown, and remediation plan.

### Options

| Flag | Description |
|---|---|
| `PATH` | Directory to assess |
| `-o, --output PATH` | Output HTML report path |
| `-t, --taxonomy TEXT` | Taxonomy to use (`general`, `financial`, `legal`, `financial_plaid`) |
| `--compliance` | Include SOX/PCI-DSS/GDPR compliance mappings |

### Examples

```bash
# Basic assessment
shadowaudit assess ./src

# Financial taxonomy with compliance mappings
shadowaudit assess ./src --taxonomy financial --compliance -o assessment.html

# Plaid-specific fintech assessment
shadowaudit assess ./src --taxonomy financial_plaid
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Assessment completed successfully |
| 1 | Assessment failed (invalid path, parse errors, or internal error) |

---

## `shadowaudit simulate`

Replay agent execution traces through the ShadowAudit gate.

### Synopsis

```
shadowaudit simulate [OPTIONS]
```

### Description

Reads a JSONL trace file (one JSON object per line, each representing a tool call) and replays each call through the gate. Compares static vs. adaptive scoring side-by-side. Useful for regression testing and detecting behavioral drift.

### Options

| Flag | Description |
|---|---|
| `--trace-file PATH` | JSONL trace file to replay (required) |
| `-t, --taxonomy TEXT` | Taxonomy to use |
| `--compare` | Compare static vs. adaptive scoring results |
| `-o, --output PATH` | Write comparison report to file |

### Examples

```bash
# Replay traces with static scoring
shadowaudit simulate --trace-file traces.jsonl --taxonomy general

# Compare static vs. adaptive
shadowaudit simulate --trace-file traces.jsonl --taxonomy general --compare

# Save comparison report
shadowaudit simulate --trace-file traces.jsonl --compare -o comparison.html
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Simulation completed |
| 1 | Invalid trace file or internal error |

---

## `shadowaudit build-taxonomy`

Interactively build a custom risk taxonomy.

### Synopsis

```
shadowaudit build-taxonomy [OPTIONS]
```

### Description

Prompts for industry, payment methods, and compliance frameworks, then generates a tailored JSON taxonomy file. The generated taxonomy can be loaded via `--taxonomy` in other commands.

### Options

| Flag | Description |
|---|---|
| `-o, --output PATH` | Output JSON file path (default: `custom-taxonomy.json`) |

### Examples

```bash
# Interactive build
shadowaudit build-taxonomy

# Save to specific file
shadowaudit build-taxonomy -o my-taxonomy.json
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Taxonomy built successfully |
| 1 | Build cancelled or error |

---

## `shadowaudit verify`

Verify the integrity of a hash-chained audit log.

### Synopsis

```
shadowaudit verify [OPTIONS] AUDIT_LOG
```

### Description

Reads an SQLite audit log database and verifies the SHA-256 hash chain linking all entries. If Ed25519 signing is enabled, also verifies signatures. Reports any tampered, missing, or out-of-order entries.

### Arguments

| Argument | Description |
|---|---|
| `AUDIT_LOG` | Path to SQLite audit database (default: `audit.db`) |

### Examples

```bash
# Verify default audit.db
shadowaudit verify

# Verify specific database
shadowaudit verify /var/log/shadowaudit.db
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Chain valid, no tampering detected |
| 1 | Chain invalid — tampering or corruption detected |
| 2 | Database not found or unreadable |

---

## `shadowaudit owasp`

Generate an OWASP Agentic Top 10 coverage matrix.

### Synopsis

```
shadowaudit owasp [OPTIONS]
```

### Description

Maps ShadowAudit's controls to the OWASP Agentic AI Top 10 risks. Generates an HTML report showing which risks are fully covered, partially covered, or not applicable. Useful for security questionnaires and compliance documentation.

### Options

| Flag | Description |
|---|---|
| `-o, --output PATH` | Output HTML report path (default: `shadowaudit-owasp-report.html`) |

### Examples

```bash
# Generate coverage matrix
shadowaudit owasp

# Save to specific file
shadowaudit owasp -o owasp-coverage.html
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Report generated successfully |
| 1 | Report generation failed |

---

## `shadowaudit eu-ai-act`

Generate an EU AI Act Annex IV evidence pack.

### Synopsis

```
shadowaudit eu-ai-act [OPTIONS] PATH
```

### Description

Scans the codebase, assesses risk posture, and generates a structured evidence pack for EU AI Act Annex IV compliance. Produces both JSON (machine-readable) and HTML (human-readable) outputs covering risk management, cybersecurity, data governance, and technical documentation.

### Options

| Flag | Description |
|---|---|
| `PATH` | Directory to scan (default: `.`) |
| `-t, --taxonomy TEXT` | Taxonomy to use for risk assessment |
| `-o, --output PATH` | Output HTML report path |
| `--json-output PATH` | Output JSON evidence pack path |
| `--system-name TEXT` | System name for the evidence pack (default: `ShadowAudit System`) |

### Examples

```bash
# Generate evidence pack for current directory
shadowaudit eu-ai-act . --taxonomy general --system-name "MyAgent"

# Generate both HTML and JSON
shadowaudit eu-ai-act ./src --taxonomy financial --system-name "FintechAgent" -o evidence.html --json-output evidence.json
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Evidence pack generated successfully |
| 1 | Generation failed (invalid path, missing taxonomy, or internal error) |

---

## Global Options

All commands support:

| Flag | Description |
|---|---|
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

---

## Environment Variables

| Variable | Affected Command | Description |
|---|---|---|
| `SHADOWAUDIT_TELEMETRY` | All | Set to `1` to enable opt-in telemetry (hashed metadata only) |
| `SHADOWAUDIT_API_KEY` | `telemetry` | API key for telemetry endpoint (if not using default) |
