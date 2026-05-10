# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Placeholder for upcoming features.

### Changed
- Placeholder for upcoming changes.

## [0.4.1] - 2026-05-10

### Changed
- README overhaul: hero section with three AGT differentiators, collapsed feature list into 6 categories, honest positioning docs.
- Added CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, docs/CLI.md, docs/FEATURES.md, docs/POSITIONING.md.
- Added GitHub issue templates and pull request template.

### Fixed
- Removed unused `pytest` import in `tests/test_mcp.py` (CI ruff failure).
- Added `mypy` `ignore_missing_imports` for `cryptography` and `shadowaudit._native` (CI mypy failure).
- Fixed README Python API example to match real `Gate.evaluate()` signature.
- Fixed ASCII architecture diagram alignment.

## [0.4.0] - 2026-05-08

### Added
- **Hash-chained, tamper-evident audit log** (`shadowaudit/core/chain.py`). Every audit entry links to the previous via SHA-256. Modifying any row invalidates the chain. Verified via `shadowaudit verify`.
- **Optional Ed25519 signing of audit entries** (`shadowaudit/core/keys.py`). Generate keypairs, sign each entry, and verify authenticity cryptographically. Falls back to HMAC-SHA256 when `cryptography` is not installed.
- **Hardened Regex+AST scorer** (`shadowaudit/core/scorer.py`). `RegexASTScorer` adds whole-word regex matching and Python AST analysis for dangerous constructs (`os.system`, `subprocess.call`, `eval`, `exec`).
- **OWASP Agentic Top 10 coverage matrix** (`shadowaudit/assessment/owasp.py`). Static mapping of ShadowAudit controls to OWASP Agentic AI Top 10 risks. Generate HTML reports via `shadowaudit owasp`.
- **MCP gateway server** (`shadowaudit/mcp/gateway.py`). Stdio proxy that intercepts MCP tool calls through the ShadowAudit Gate. JSON-RPC parsing with Content-Length protocol.
- **MCP in-process adapter** (`shadowaudit/mcp/adapter.py`). `ShadowAuditMCPSession` wraps an existing MCP client session with ShadowAudit gating for async tool calls.
- **LangGraph integration** (`shadowaudit/framework/langgraph.py`). `ShadowAuditToolNode` replaces LangGraph `ToolNode` with automatic gate enforcement on every tool invocation.
- **OpenAI Agents SDK integration** (`shadowaudit/framework/openai_agents.py`). `ShadowAuditOpenAITool` wraps OpenAI Agents SDK tools with deterministic gate evaluation.
- **EU AI Act Annex IV evidence pack generator** (`shadowaudit/assessment/eu_ai_act.py`). Generates structured JSON + HTML evidence packs for regulatory submission. Covers risk management, cybersecurity, data governance, and technical documentation.
- **Plaid taxonomy pack** (`shadowaudit/taxonomies/financial_plaid.json`). 10 Plaid-specific risk categories: auth, balance, transactions, identity, income, transfer, link token, item management, liabilities, investments.
- **Opt-in telemetry client** (`shadowaudit/telemetry/client.py`). Async fire-and-forget exporter for hashed metadata only. Disabled by default; enable via `SHADOWAUDIT_TELEMETRY=1`.
- **CLI commands**: `shadowaudit verify` (audit log integrity), `shadowaudit owasp` (coverage matrix), `shadowaudit eu-ai-act` (evidence pack generation).
- **9 new runnable examples** in `examples/` covering all v0.4.0 features, plus `examples/run_all_examples.py` test runner.
- **11 new test files** bringing total to 205 tests (1 skipped for optional `pytest-asyncio`).
- **Demo project** (`shadowaudit-demo/`) — realistic fintech agent with 8 tools, 2 intentionally ungated, for end-to-end scanner validation.

### Changed
- **README overhaul**: collapsed 14-item feature list into 6 grouped categories; added Testing section; updated Examples table with all 12 examples.
- **Architecture diagram**: updated audit-log box to "Hash-chained + Ed25519".
- **Project Status**: trimmed from 14 bullets to 6 grouped categories.
- **Cross-file wrapper detection**: two-pass scanner (`_collect_all_wrappers` then `scan_file`) correctly detects tools wrapped in a different file from their definition.
- **Taxonomy cache safety**: `TaxonomyLoader.load()` now returns `copy.deepcopy(data)` to prevent shared mutable state poisoning.
- **Scorer performance**: added `@functools.lru_cache` for regex pattern compilation in `RegexASTScorer`.

### Fixed
- **Timing attack vulnerability** in fallback signature verification: replaced `==` with `hmac.compare_digest` in `shadowaudit/core/keys.py`.
- **Private key race condition**: `generate_keypair()` now uses atomic `os.open()` with mode `0o600` instead of `write_text()` + `os.chmod()`.
- **Taxonomy cache poisoning**: `Gate.evaluate()` now deep-copies taxonomy entries before mutation.
- **MCP unbounded Content-Length**: enforced `MAX_MESSAGE_SIZE` (10MB) to prevent memory exhaustion.
- **MCP stderr thread race**: `_drain_stderr` now acquires `self._lock` when accessing `self._proc`.
- **Telemetry worker race**: `TelemetryClient.start()` now guarded by `asyncio.Lock` to prevent duplicate worker tasks.
- **EU AI Act path traversal**: `write_html()` and `write_json()` now reject paths containing `..` components.
- **CLI version consistency**: extracted `__version__` constant; fixed hardcoded `0.3.0` in assessment context.
- **Hash chain missing-key validation**: `verify_chain_from_rows()` now gracefully handles malformed DB rows instead of raising `KeyError`.

### Security
- See Fixed section above for security-related fixes.

## [0.3.3] - 2026-05-07

### Added
- `default="."` on `shadowaudit check` path argument so `shadowaudit check` works without explicit path.

### Fixed
- Cross-file wrapper detection: tools defined in one file and wrapped in another are now correctly detected as gated (two-pass scanning).

## [0.3.2] - 2026-05-07

### Fixed
- README version badge and PyPI description sync.
- CI workflow with release assets.

## [0.3.1] - 2026-05-07

### Added
- `shadowaudit check --output report.html` for HTML report generation from static scan.
- `--fail-on-ungated` flag for CI/CD integration.

### Fixed
- Scanner false positives on non-tool classes.

## [0.3.0] - 2026-05-07

### Added
- Initial PyPI release.
- Core Gate with keyword-based scoring and configurable thresholds.
- SQLite-backed audit log (append-only).
- LangChain and CrewAI adapters.
- Static scanner (`shadowaudit check`) for detecting ungated tool classes.
- Assessment reporter with Jinja2 HTML reports.
- Trace simulator (`shadowaudit simulate`) for replaying agent execution traces.
- Interactive taxonomy builder (`shadowaudit build-taxonomy`).
- Three starter taxonomies: general, financial, legal.
- Cloud client hook (legacy, not used in OSS path).

[Unreleased]: https://github.com/AnshumanKumar14/shadowaudit-python/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/AnshumanKumar14/shadowaudit-python/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/AnshumanKumar14/shadowaudit-python/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/AnshumanKumar14/shadowaudit-python/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/AnshumanKumar14/shadowaudit-python/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/AnshumanKumar14/shadowaudit-python/releases/tag/v0.3.0
