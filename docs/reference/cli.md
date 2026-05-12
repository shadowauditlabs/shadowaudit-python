# CLI Reference

All commands are available through the `shadowaudit` entry point after installation.

```bash
pip install shadowaudit
shadowaudit --version
```

---

## `shadowaudit check`

Scan Python files for ungated AI agent tools.

```bash
shadowaudit check [OPTIONS] PATH
```

Options:

| Flag | Description |
|---|---|
| `PATH` | File or directory to scan. Defaults to `.` |
| `-f, --framework TEXT` | Filter by framework, such as `langchain`, `crewai`, or `autogen`. |
| `-o, --output PATH` | Write an HTML report. |
| `--fail-on-ungated` | Exit non-zero if high-risk ungated tools are found. |
| `--strict` | Exit non-zero if any ungated tools are found. |
| `--report-json` | Print findings as JSON. |

Examples:

```bash
shadowaudit check ./src
shadowaudit check ./src --fail-on-ungated
shadowaudit check ./src --framework langchain --output report.html
```

---

## `shadowaudit assess`

Generate a detailed HTML assessment report with taxonomy enrichment.

```bash
shadowaudit assess [OPTIONS] PATH
```

Options:

| Flag | Description |
|---|---|
| `PATH` | Directory or file to assess. |
| `-o, --output PATH` | Write the HTML report to a specific path. |
| `-t, --taxonomy TEXT` | Taxonomy to use, such as `general`, `financial`, `legal`, or a taxonomy file path. |
| `-c, --compliance` | Include compliance mappings in the report. |

---

## `shadowaudit verify`

Verify the integrity of a hash-chained audit log.

```bash
shadowaudit verify --audit-log audit.db
```

Options:

| Flag | Description |
|---|---|
| `-a, --audit-log PATH` | SQLite audit log to verify. Required. |

Exit codes:

| Code | Meaning |
|---|---|
| `0` | Audit chain is valid. |
| `3` | Audit chain is invalid. |

---

## `shadowaudit logs`

View structured audit events.

```bash
shadowaudit logs [OPTIONS]
```

Options:

| Flag | Description |
|---|---|
| `-a, --audit-log PATH` | SQLite audit log. Defaults to `audit.db`. |
| `--agent TEXT` | Filter by agent ID. |
| `--limit INTEGER` | Number of events to show. Defaults to `50`. |
| `--json` | Print events as JSON. |

Examples:

```bash
shadowaudit logs --audit-log audit.db
shadowaudit logs --agent finance-agent --json
```

---

## `shadowaudit trace`

Show a detailed execution trace for an audit entry hash or payload hash.

```bash
shadowaudit trace TRACE_ID --audit-log audit.db
```

Options:

| Flag | Description |
|---|---|
| `TRACE_ID` | Entry hash or payload hash. |
| `-a, --audit-log PATH` | SQLite audit log. Defaults to `audit.db`. |

---

## `shadowaudit replay`

Replay a JSONL trace file for deterministic output.

```bash
shadowaudit replay trace.jsonl
```

Use `simulate` when you need taxonomy selection, comparison, or JSON output.

---

## `shadowaudit simulate`

Replay agent execution traces through the ShadowAudit simulator.

```bash
shadowaudit simulate --trace-file trace.jsonl --taxonomy financial --compare
```

Options:

| Flag | Description |
|---|---|
| `-t, --trace-file PATH` | JSONL trace file to replay. Required. |
| `--taxonomy TEXT` | Primary taxonomy to use. Defaults to `general`. |
| `-p, --taxonomy-pack TEXT` | Additional taxonomy pack. Can be used multiple times. |
| `--compare` | Show static and adaptive decisions side by side. |
| `-o, --output PATH` | Write simulation output as JSON. |

---

## `shadowaudit pending-approvals`

List pending approval requests.

```bash
shadowaudit pending-approvals --db-path shadowaudit_approvals.db
```

Options:

| Flag | Description |
|---|---|
| `-d, --db-path PATH` | Approval database. Defaults to `shadowaudit_approvals.db`. |

---

## `shadowaudit approve`

Approve a pending tool execution.

```bash
shadowaudit approve REQUEST_ID --user alice@example.com
```

Options:

| Flag | Description |
|---|---|
| `REQUEST_ID` | Approval request ID. |
| `-d, --db-path PATH` | Approval database. Defaults to `shadowaudit_approvals.db`. |
| `-u, --user TEXT` | User approving the request. Defaults to `cli_user`. |

---

## `shadowaudit reject`

Reject a pending tool execution.

```bash
shadowaudit reject REQUEST_ID --user alice@example.com
```

Options are the same as `approve`.

---

## `shadowaudit owasp`

Generate an OWASP Agentic Top 10 coverage matrix.

```bash
shadowaudit owasp --output owasp.html
```

---

## `shadowaudit eu-ai-act`

Generate an EU AI Act Annex IV evidence pack from a codebase assessment.

```bash
shadowaudit eu-ai-act ./src --output eu-ai-act.html --json-output eu-ai-act.json
```

Options:

| Flag | Description |
|---|---|
| `PATH` | Codebase path to assess. Required. |
| `-t, --taxonomy TEXT` | Taxonomy to use. Defaults to `general`. |
| `-o, --output PATH` | Write HTML evidence pack. |
| `--json-output PATH` | Write JSON evidence pack. |
| `--system-name TEXT` | System name for the evidence pack. |

---

## `shadowaudit tune`

Analyze recent audit decisions and suggest threshold adjustments.

```bash
shadowaudit tune --audit-log audit.db --window 200
```

Options:

| Flag | Description |
|---|---|
| `-a, --audit-log PATH` | SQLite audit log. Required. |
| `--agent-id TEXT` | Limit analysis to one agent. |
| `--window INTEGER` | Number of recent decisions to analyze. Defaults to `200`. |
| `--false-positive-budget FLOAT` | Acceptable false-positive rate. Defaults to `0.05`. |

