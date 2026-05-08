# ShadowAudit Code Review — Week 13

**Date:** 2026-05-08
**Scope:** Full codebase review through Week 13
**Focus:** Performance, Security, Quality, Gaps

---

## 1. core/chain.py (Hash Chain)

### Security
- **S1** Line 37: `_canonical_json` uses `default=str` which serializes arbitrary objects unpredictably. A malicious or buggy object could produce non-deterministic JSON, breaking hash integrity.
  - **Fix:** Remove `default=str` or restrict to known serializable types. Log/warn on non-serializable values.
- **S2** Line 116-133: `verify_chain_from_rows` does not validate that required keys exist in `row`. A malformed DB row raises `KeyError` instead of being reported as a verification error.
  - **Fix:** Use `.get()` with defaults and collect missing-key errors gracefully.

### Quality
- **Q1** Line 72-101: `verify_chain` does not detect duplicate `id` values or out-of-order entries. A chain with swapped entries but intact hashes would pass.
  - **Fix:** Verify `entry.id` is strictly increasing and unique.
- **Q2** Line 67-69: Empty chain returns `(True, [])`. This is ambiguous — is an empty log valid or suspicious?
  - **Fix:** Document behavior or add a flag `allow_empty`.

### Gaps
- **G1** No support for chain truncation or pruning. Audit logs grow unbounded.
- **G2** No tests for `verify_chain_from_rows` with malformed rows or missing keys.

---

## 2. core/keys.py (Ed25519 Key Management)

### Security — CRITICAL
- **S3** Line 74-76: Fallback key generation uses `os.urandom(32)` and derives public key via `hashlib.sha512(seed).digest()[:32]`. This is **not** Ed25519 and provides no cryptographic security. The comment admits this but no runtime warning is emitted.
  - **Fix:** Log a `WARNING` at module load and in `generate_keypair` when `_HAS_CRYPTOGRAPHY is False`.
- **S4** Line 127-130: Fallback signing uses HMAC-SHA256 (`hashlib.sha256(pub_bytes + message).digest()`). The prefix `b"FALLBACK:"` makes signatures distinguishable, enabling oracle attacks.
  - **Fix:** Use a constant-time comparison and do not expose whether fallback or real signature failed.
- **S5** Line 158-160: Fallback verification uses `==` for digest comparison (`sig_bytes[len(b"FALLBACK:"):] == expected`). This is **vulnerable to timing attacks**.
  - **Fix:** Use `hmac.compare_digest()` for constant-time comparison.
- **S6** Line 81-84: `write_text()` followed by `os.chmod()` creates a race window where the private key is world-readable.
  - **Fix:** Use `os.open()` with `O_CREAT | O_WRONLY` and mode `0o600` atomically, or `tempfile` with restricted permissions.
- **S7** Line 99-100: `read_text()` reads keys as strings then strips whitespace. No validation of base64 length or format.
  - **Fix:** Validate decoded byte lengths (32 bytes for Ed25519 private, 32 for public).

### Quality
- **Q3** No tests for the fallback path (cryptography not installed). The fallback is the default for OSS users — it must be tested.
- **Q4** Line 112-133: `sign_entry` accepts `private_key_b64` but does not validate it is non-empty before `b64decode`.

### Gaps
- **G3** No key rotation support.
- **G4** No memory-zeroing of key material after use (Python makes this hard, but at least avoid keeping keys in plain strings longer than necessary).

---

## 3. core/scorer.py (RegexASTScorer)

### Performance
- **P1** Line 81-92: `_compile_patterns` recompiles regex patterns on **every** `score()` call. For repeated evaluations with the same keywords, this is wasteful.
  - **Fix:** Add an LRU cache or instance-level cache keyed by `tuple(risk_keywords)`.
- **P2** Line 94-127: `_ast_risk_score` calls `ast.parse(text, mode="exec")` on every payload containing code triggers. This is CPU-intensive and blocks the caller.
  - **Fix:** Add a timeout or length limit (e.g., max 10KB) before parsing. Consider running in a subprocess for untrusted input.
- **P3** Line 50: `KeywordScorer` uses `str(payload).lower()`. For large nested dicts, `str()` can be expensive and non-deterministic across Python versions.
  - **Fix:** Use a deterministic, bounded serialization (e.g., canonical JSON of values only).

### Security
- **S8** Line 96-97: `ast.parse()` on untrusted input is generally safe against code execution, but can be exploited for CPU exhaustion via deeply nested ASTs (similar to XML billion laughs).
  - **Fix:** Limit input length before parsing (e.g., 4096 chars). Wrap in `sys.setrecursionlimit` guard.
- **S9** Line 64-76: `_DANGEROUS_AST_NAMES` is a class-level set but only checks exact names. It misses aliases (`import os as o; o.system(...)`).
  - **Fix:** Track import aliases via `ast.Import`/`ast.ImportFrom` mapping in the AST walk.

### Quality
- **Q5** Line 146: AST scan trigger `any(trigger in text for trigger in (...))` is overly broad. A payload containing "def " in a string literal will trigger AST parsing.
  - **Fix:** Use a quick regex heuristic or only parse when the payload type hints at code.
- **Q6** Line 167: `AdaptiveScorer` instantiates a new `RegexASTScorer()` on every `score()` call, losing any caching benefit.
  - **Fix:** Store a single `RegexASTScorer` instance as a class attribute.

### Gaps
- **G5** No tests for `RegexASTScorer` with malicious/edge-case payloads (deeply nested AST, Unicode, very large strings).
- **G6** No benchmark tests to catch scorer performance regressions.

---

## 4. assessment/owasp.py

### Quality
- **Q7** Lines 26-117: `_OWASP_COVERAGE` is a module-level mutable list. It can be accidentally mutated at runtime.
  - **Fix:** Use a tuple or return copies via `list(_OWASP_COVERAGE)`.
- **Q8** Line 152: `generate_owasp_context` exposes `i.__dict__` which includes all fields, even if the dataclass evolves to have internal fields.
  - **Fix:** Use `dataclasses.asdict(i)` for a clean, maintained serialization.

### Gaps
- **G7** No dynamic extension mechanism for coverage matrix. Users cannot add custom risks.
- **G8** No tests for `generate_owasp_context` or HTML rendering.

---

## 5. mcp/gateway.py

### Performance
- **P4** Line 189-223: `run()` is fully synchronous and blocks the main thread. Stdio proxying cannot handle concurrent messages.
  - **Fix:** Provide an async `arun()` variant using `anyio` or `asyncio` streams.
- **P5** Line 72-91: `_read_message` reads line-by-line with blocking I/O. Large `Content-Length` values will cause `stream.read(length)` to block indefinitely.
  - **Fix:** Enforce a max `Content-Length` (e.g., 10MB) and a read timeout.

### Security — CRITICAL
- **S10** Line 82: `length = int(headers.get("content-length", 0))`. No validation that length is non-negative or within bounds. A negative or huge value causes memory exhaustion or crashes.
  - **Fix:** `if not (0 < length <= MAX_MESSAGE_SIZE): return None`.
- **S11** Line 59-66: `_start_upstream` passes `self._upstream_command` directly to `subprocess.Popen`. While this is developer-controlled, if any element is derived from user input, it enables command injection.
  - **Fix:** Document that `upstream_command` must not contain user input. Add validation that each element is a non-empty string without shell metacharacters.
- **S12** Line 196-203: `_drain_stderr` runs in a daemon thread but accesses `self._proc` without holding `self._lock`. Race condition during shutdown.
  - **Fix:** Acquire `self._lock` when accessing `self._proc`.

### Quality
- **Q9** Line 130-137: `_forward_and_respond` writes to `stdin` and reads from `stdout` without synchronization. If multiple threads call this, messages interleave.
  - **Fix:** Acquire `self._lock` around the write-read pair.
- **Q10** Line 206-214: `run()` catches `KeyboardInterrupt` but not `BrokenPipeError` or `OSError` on stdio, causing unhandled exceptions.
  - **Fix:** Wrap the loop in a broad `except (OSError, BrokenPipeError)` handler.

### Gaps
- **G9** No health check or automatic restart for the upstream process.
- **G10** No tests for the full stdio proxy loop (only helper method unit tests exist in `test_mcp.py`).

---

## 6. mcp/adapter.py

### Security
- **S13** Line 59-61: `__getattr__` transparently passes through all attributes of the underlying session. This could expose dangerous methods (e.g., `exec`, `eval`) if the session has them.
  - **Fix:** Maintain an explicit allowlist of passthrough attributes, or at least denylist dangerous ones.

### Quality
- **Q11** Line 63-83: `call_tool` is `async` but `self._gate.evaluate()` is synchronous. If gate evaluation is slow (e.g., AST parsing), it blocks the event loop.
  - **Fix:** Run `evaluate` in `asyncio.get_running_loop().run_in_executor()`.

### Gaps
- **G11** No retry logic or circuit breaker for blocked calls.
- **G12** No tests for `call_tool` with actual async underlying sessions.

---

## 7. framework/langgraph.py

### Performance
- **P6** Line 74-110: `__call__` is synchronous. If `tool.invoke(arguments)` is blocking (e.g., network call), it blocks the LangGraph event loop.
  - **Fix:** Provide an async `acall` or `__call__` variant.

### Security
- **S14** Line 86-87: `tool_name` extraction uses `.get("name", ...)` chain. If `msg.tool_calls` contains unexpected shapes, it could raise `AttributeError` or `KeyError`.
  - **Fix:** Use defensive `.get()` at every level.

### Quality
- **Q12** Line 104-106: If `tool` is not found in `self._tools`, raises `AgentActionBlocked` with misleading message ("not found" is not a block reason).
  - **Fix:** Raise a distinct `ToolNotFoundError`.
- **Q13** Line 98-102: `AgentActionBlocked` is raised but not caught within the node, causing the LangGraph state machine to crash rather than gracefully handle the block.
  - **Fix:** Document that callers must catch this, or return a blocked-result dict instead of raising.

### Gaps
- **G13** No async support.
- **G14** No tests for `ShadowAuditToolNode` (not in `test_framework_langgraph.py` based on file list).

---

## 8. framework/openai_agents.py

### Security
- **S15** Line 66-70: `json.loads(input_json)` parses untrusted JSON without depth limits. Malicious input with extreme nesting could cause recursion errors or memory exhaustion.
  - **Fix:** Use `json.loads(input_json, parse_constant=lambda x: None)` and validate depth.

### Quality
- **Q14** Line 86-91: `on_invoke_tool` is `async` but the `elif hasattr(self._tool, "invoke")` branch calls `self._tool.invoke(arguments)` synchronously. This blocks the event loop.
  - **Fix:** Detect if `invoke` is a coroutine and `await` it, or run in executor.
- **Q15** Line 60-62: Metadata mirroring uses `getattr(tool, ...)` with defaults. If the tool lacks these attributes, downstream OpenAI Agents SDK may fail.
  - **Fix:** Validate required attributes at initialization and raise early.

### Gaps
- **G15** No tests for `ShadowAuditOpenAITool`.
- **G16** No support for streaming tool responses.

---

## 9. assessment/eu_ai_act.py

### Security
- **S16** Line 62-79: `write_html` and `write_json` accept any `Path`. No validation that the path is within an allowed directory, enabling path traversal if user input is passed.
  - **Fix:** Resolve and validate the path against a base directory, or at least reject paths containing `..`.

### Quality
- **Q16** Line 66-77: `write_html` imports `jinja2` inside the method. If Jinja2 is not installed, it falls back to inline template. This is fine but the fallback template `_FALLBACK_EU_TEMPLATE` lacks the `autoescape` guarantee of the file-based template.
  - **Fix:** Ensure the inline fallback also uses `MarkupSafe` escaping or construct it via Jinja2 `from_string` with autoescape enabled.

### Gaps
- **G17** No tests for `generate_evidence_pack`, `write_html`, or `write_json`.
- **G18** No validation that `system_version` follows semver or is sanitized for HTML/JSON injection.

---

## 10. telemetry/client.py

### Performance
- **P7** Line 126-136: `_worker` processes items one-by-one. No batching, leading to high overhead for high-throughput scenarios.
  - **Fix:** Implement batch draining (e.g., process up to N items or wait for timeout).
- **P8** Line 152-157: `_post_item` uses `urllib.request` via `run_in_executor`. This creates a new thread per request. For high volume, use `aiohttp` or `httpx`.
  - **Fix:** Migrate to `httpx.AsyncClient` for true async I/O.

### Security
- **S17** Line 54: `api_key` is stored as a plain instance attribute. Could be leaked in stack traces or logs.
  - **Fix:** Store in a private attribute and redact in `__repr__`.
- **S18** Line 141-150: `urllib.request` does not pin certificates or validate hostname beyond default SSL. No protection against MITM in hostile networks.
  - **Fix:** Document that users should deploy in trusted networks or provide cert pinning options.

### Quality
- **Q17** Line 70-75: `start()` can create multiple worker tasks if called rapidly. `self._worker_task is None or self._worker_task.done()` is not atomic.
  - **Fix:** Guard with a lock or use `asyncio.Lock`.
- **Q18** Line 77-88: `stop()` cancels the worker but does not drain the queue first. Items in flight are lost.
  - **Fix:** Drain queue before sending shutdown signal, or persist unsent items.

### Gaps
- **G19** No retry logic with exponential backoff.
- **G20** No tests for the async worker, `_post_item`, or network failure paths.

---

## 11. check.py (Two-Pass Scanner)

### Performance
- **P9** Line 286-302: `_collect_all_wrappers` and `scan_file` both read and parse every file. This is **2× file I/O and AST parsing**.
  - **Fix:** Cache parsed ASTs in `scan_directory` and reuse for both passes.
- **P10** Line 335-338: `path.rglob(pattern)` iterates all files, then filters with `any(part in exclude_dirs for part in pyfile.parts)`. For deep trees, this is slow.
  - **Fix:** Prune excluded directories at the `rglob` level or use `os.walk` with manual pruning.

### Security
- **S19** Line 56-76: `_guess_category` uses naive substring matching. A tool named `ready_payment` matches "read" → `read_only` instead of `payment_initiation`.
  - **Fix:** Use word-boundary regex matching or prioritize longer/more specific matches.
- **S20** Line 254-260: `scan_file` catches `SyntaxError` and `UnicodeDecodeError` but silently returns `[]`. A malformed file could hide dangerous tools.
  - **Fix:** Log a warning or yield a `ToolFinding` with `parse_error=True`.

### Quality
- **Q19** Line 200-236: `_find_shadowaudit_wrappers` only detects `ShadowAuditTool`. It misses `ShadowAuditCrewAITool`, `ShadowAuditOpenAITool`, `ShadowAuditMCPSession`, etc.
  - **Fix:** Maintain a registry of wrapper class names and scan for all of them.
- **Q20** Line 325-326: `exclude_dirs` is a set of strings, but `pyfile.parts` contains `Path` objects. The `in` check works via `__eq__` but is fragile.
  - **Fix:** Convert `pyfile.parts` to strings before comparison.

### Gaps
- **G21** No tests for cross-file wrapper detection (`global_wrapped`).
- **G22** No handling of permission errors (`PermissionError`) when reading files.

---

## 12. cli.py

### Security
- **S21** Line 44: `check` command uses `click.Path(exists=True)`. No validation that the path is not a symlink escaping the project root.
  - **Fix:** Resolve to absolute path and optionally enforce a base directory.
- **S22** Line 357-386: `eu_ai_act` command has `--json` mapped to parameter `j`. This is confusing and could lead to accidental overwrites.
  - **Fix:** Rename to `--json-output`.

### Quality
- **Q21** Line 182: `ctx["version"] = "0.3.0"` is hardcoded and inconsistent with the CLI version (`0.4.0` on line 37).
  - **Fix:** Use a single `__version__` constant.
- **Q22** Line 168-199: `assess` command duplicates report generation logic. The compliance branch and non-compliance branch share little code.
  - **Fix:** Extract a `_generate_report(data, template_name, output_path)` helper.

### Gaps
- **G23** No `--verbose` / `--quiet` global flags.
- **G24** `verify` command only supports SQLite. No support for other audit backends.
- **G25** No integration tests for CLI commands (only unit tests for underlying functions exist).

---

## 13. core/gate.py (Supporting File)

### Security
- **S23** Line 94: `taxonomy_entry["name"] = risk_category` **mutates the cached taxonomy dict** returned by `TaxonomyLoader.lookup()`. This poisons the cache for all subsequent evaluations.
  - **Fix:** Copy the dict before mutating: `taxonomy_entry = dict(taxonomy_entry)`.

### Performance
- **P11** Line 81-105: `evaluate()` performs multiple SQLite queries (K, V, record, audit) synchronously. In high-throughput scenarios this is a bottleneck.
  - **Fix:** Consider batching or async state store.

---

## 14. core/taxonomy.py (Supporting File)

### Security
- **S24** Line 35-54: `TaxonomyLoader.load()` caches at class level (`cls._cache`) but the cached object is a mutable dict. Callers can mutate shared state.
  - **Fix:** Return `copy.deepcopy(data)` from cache.
- **S25** Line 43-48: `open(path, "r")` without path validation. If `path` is user-controlled, this enables path traversal.
  - **Fix:** Resolve and validate against a base directory.

### Quality
- **Q23** Line 36: Cache key logic is flawed. `path is None` caches the default, but `path="general"` does not use the cache even if it was the previously loaded default.
  - **Fix:** Use a proper cache key: `(path or "__default__")`.

---

## 15. core/audit.py (Supporting File)

### Performance
- **P12** Line 247: `verify()` fetches up to 1,000,000 rows into memory. For large audit logs, this causes OOM.
  - **Fix:** Stream rows in batches (e.g., 10,000 at a time) and verify incrementally.

### Quality
- **Q24** Line 36-41: `_connection()` creates a new connection for every call when not using `:memory:`. No connection pooling or reuse.
  - **Fix:** Use a single persistent connection with `check_same_thread=False` and close it in `__del__` or context manager.

---

## 16. core/state.py (Supporting File)

### Performance
- **P13** Line 65-80: `record_decision` commits after every insert. For high throughput, this is slow.
  - **Fix:** Offer a batch mode or use WAL mode with deferred commits.
- **P14** Line 103-118: `compute_K` fetches all rows in the window and sums in Python. SQLite can do this via `AVG(passed)`.
  - **Fix:** Use `SELECT AVG(passed) ...`.

### Quality
- **Q25** Line 32-39: `_connection()` has the same connection-per-call issue as `audit.py`.

---

## Summary: Critical Fixes Required

| Priority | File | Issue | Fix |
|----------|------|-------|-----|
| **CRITICAL** | `core/keys.py` | Timing attack in fallback verify (S5) | Use `hmac.compare_digest` |
| **CRITICAL** | `core/keys.py` | Private key race condition (S6) | Atomic write with `os.open` |
| **CRITICAL** | `mcp/gateway.py` | Unbounded Content-Length (S10) | Enforce `MAX_MESSAGE_SIZE` |
| **CRITICAL** | `core/gate.py` | Cache poisoning via mutable dict (S23) | Copy taxonomy before mutation |
| **HIGH** | `core/keys.py` | No warning on fallback crypto (S3) | Log `WARNING` |
| **HIGH** | `check.py` | Double file I/O (P9) | Cache ASTs |
| **HIGH** | `telemetry/client.py` | Worker race condition (Q17) | Use `asyncio.Lock` |
| **HIGH** | `core/scorer.py` | Regex recompilation (P1) | Add LRU cache |
| **MEDIUM** | `framework/langgraph.py` | Blocking tool.invoke (P6) | Async variant |
| **MEDIUM** | `mcp/adapter.py` | Blocking gate in async path (Q11) | `run_in_executor` |
| **MEDIUM** | `core/chain.py` | Missing key validation (S2) | Use `.get()` |
| **MEDIUM** | `assessment/eu_ai_act.py` | Path traversal (S16) | Validate path |
| **MEDIUM** | `cli.py` | Hardcoded version (Q21) | Use `__version__` |

---

*Review compiled by automated analysis + manual inspection.*
