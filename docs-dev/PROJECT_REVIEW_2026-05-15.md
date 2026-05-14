# ShadowAudit Project Review

Date: 2026-05-15

Scope: local repository scan, README/docs/package metadata review, test/lint/typecheck verification, PyPI page, public website, and GitHub repository page.

## Fix Pass Status

Repo-side remediation started immediately after this review. Website content fixes for `shadowaudit.dev` were intentionally left out of scope.

Completed in this pass:

- Aligned local package version metadata to `0.6.1`.
- Updated repository URLs from the personal GitHub namespace to `shadowauditlabs`.
- Rewrote the GitHub README around runtime authorization, proof, rollout, limitations, and CLI workflows.
- Replaced the placeholder docs homepage with a real product/docs entrypoint.
- Implemented documented policy conditions: `contains`, `amount_lte`, `path_prefix`, and caller-depth comparisons.
- Added policy validation and `PolicyLoadError`.
- Added `shadowaudit check-policy`.
- Made policy load/validation failures fail closed during gate evaluation.
- Made audit write failures fail closed in enforce mode.
- Added regression tests for policy conditions, legacy bundled policy schema support, default-deny, policy errors, `check-policy`, and audit failure behavior.

Verification after fixes:

```bash
ruff check shadowaudit tests
mypy shadowaudit
PYTHONPATH=. .venv/bin/pytest -q
```

Results: ruff passed, mypy passed, bundled policy validation passed, and `261` tests passed.

## Executive Read

ShadowAudit is not just a small wrapper library. The real project scope is runtime authorization infrastructure for agent tool execution: policy-as-code gating, framework adapters, audit logging, replay/simulation, approval queues, MCP governance, taxonomies, compliance reports, static scanning, and trust-flow tracing.

The strongest idea is clear and worth building around:

> Agents should not execute sensitive tool calls unless a deterministic runtime policy authorizes them.

That is a much better category than "AI safety SDK" or "agent guardrails." The infrastructure analogy is correct: ShadowAudit is closer to an admission controller, API gateway, IAM policy point, or OPA-style runtime enforcement layer for agent tools.

Current honest verdict:

- The core concept is strong.
- The repo is broader than the README suggests.
- The implementation has credible foundations for an early OSS project.
- The product story is not yet sharp enough for a 1000-star trajectory.
- Some public-facing claims are inconsistent or stale, which hurts trust.
- The docs explain many parts, but the first-time user path is not yet strong enough.
- The "infrastructure necessity" version of this project needs fewer broad claims and more undeniable proof: real demos, real integrations, policy recipes, CI examples, benchmarks with caveats, and production-grade examples.

## Current Scope

Major components present in the repo:

- Core gate: deterministic allow, deny, approval, observe, bypass, async evaluation.
- Policy-as-code: YAML rules with capabilities, wildcard prefixes, numeric conditions, risk-level fallback.
- Taxonomies: general, financial, financial Plaid, crypto, healthcare, legal.
- Scoring: keyword scorer, regex/AST scorer, adaptive OSS placeholder, native scorer hook.
- Audit: SQLite audit log, SHA-256 hash chain, optional Ed25519 signing, verification commands.
- State: SQLite-backed agent decision history, velocity, recent tools, total amount tracking.
- Framework adapters: LangChain, LangGraph, CrewAI, OpenAI Agents SDK, MCP, direct Python API.
- MCP gateway: stdio proxy and in-process session wrapper.
- Static scanner: detects ungated tool classes/functions and CI failure modes.
- Assessment/reporting: HTML reports, OWASP Agentic Top 10 matrix, EU AI Act evidence pack.
- FlowTracer: multi-agent data-flow and trust propagation.
- CLI: check, assess, simulate, build-taxonomy, verify, owasp, eu-ai-act, tune, approvals, logs, trace, replay.
- Examples: framework demos, core concepts, fintech demo, MCP demo.
- Tests: 261 passing locally after this fix pass when run with `PYTHONPATH=.`.

## Verification Snapshot

Commands run:

```bash
ruff check shadowaudit tests
mypy shadowaudit
PYTHONPATH=. .venv/bin/pytest -q
PYTHONPATH=. .venv/bin/python tests/corpus/evaluate.py
```

Results:

- Ruff: passed.
- Mypy: passed on 44 source files.
- Pytest: 261 passed after the fix pass.
- Corpus evaluation: 130/130 correct on synthetic labelled traces.

Important caveat:

- Plain `pytest -q` failed in this shell because the package was not importable under the active Python command path. With `PYTHONPATH=.` and the repo venv, tests pass. This is environment friction, but for contributors it still matters. Add a documented `python -m pytest` / `PYTHONPATH=.` path or ensure editable install is the default onboarding path.

## Strengths

### 1. The category is excellent

"Runtime authorization for AI agents" is stronger than "guardrails." It implies a necessary control point, not a nice-to-have library. This is the core wedge.

### 2. Deterministic enforcement is the right contrast

The no-LLM-in-the-gate-path design is a real differentiator. Security buyers understand deterministic policy engines. Developers understand "block before execution." That message should dominate the README.

### 3. The project already has a lot of infrastructure-shaped pieces

Audit chain, replay, policy files, CI scanning, approvals, MCP gateway, and framework adapters make the project feel like operational infrastructure rather than a demo.

### 4. Offline-first is a real advantage

The zero cloud dependency story matters for fintech, healthcare, regulated enterprises, air-gapped deployments, and security-conscious developers.

### 5. Test suite and typing are better than many early OSS projects

261 tests, `py.typed`, mypy, ruff, CI matrix, and synthetic corpus are credible trust signals.

### 6. The compliance angle is useful if handled carefully

OWASP and EU AI Act reporting can pull in security/compliance users, but only if the claims stay precise. "Evidence generation" is credible; "compliance solved" would not be.

## Gaps And Risks

### P0: Public story is inconsistent

Initial finding: local version metadata lagged PyPI, some repo links still used the personal GitHub namespace, and the public website had stale test-count language. The repo-side version and link issues are now fixed. Website copy was intentionally left out of this pass.

Fix:

- Centralize version in one place.
- Update package URLs to `shadowauditlabs` and preferably `shadowaudit.dev`.
- Remove hardcoded test counts unless generated automatically.
- Make GitHub README, PyPI long description, docs homepage, and website agree.

### P0: Docs homepage is a placeholder

`docs/index.md` currently reads like a local development note, not documentation for a production-facing OSS project. Since GitHub/PyPI point users to docs, this is a high-impact fix.

Fix:

- Make docs home the real product entrypoint:
  - What ShadowAudit is.
  - The 5-minute quickstart.
  - Supported integrations.
  - Security model.
  - "What this does not do."
  - Links to policy recipes and demos.

### P0: README undersells the product

Yes, the GitHub README undersells ShadowAudit. It states the core idea, but it does not show enough proof. It mentions features, but does not make the reader feel: "I need this before shipping agents with tools."

What is missing:

- A concrete before/after example where an agent would have executed a bad action.
- A 60-second direct `Gate` example that runs without LangChain.
- A CLI demo: `shadowaudit check`, `shadowaudit simulate`, `shadowaudit verify`.
- A "Why not prompt guardrails?" section.
- A "Where it sits in your stack" section.
- A "What it protects / what it does not protect" section.
- A production rollout path: observe -> tune -> enforce -> audit.
- A realistic policy recipe table: shell, database, payments, MCP filesystem, SaaS admin.
- Clear maturity language: beta, production-ready for specific surfaces, not a complete security platform.

### P0: Some docs overclaim unsupported behavior

`docs/reference/policy-schema.md` documents fields that the current policy engine does not fully implement, including `contains`, `amount_lte`, `path_prefix`, `caller_depth_gt`, policy validation at gate initialization, `PolicyLoadError`, and `shadowaudit check-policy`.

Current code supports:

- `capability`
- wildcard suffix rules like `payments.*`
- `amount_gt`
- `amount_lt`
- direct context equality for unrecognized conditions
- risk level action mapping

Risk:

- This is exactly the kind of mismatch that causes infra/security users to lose trust.

Fix:

- Either implement the documented fields and CLI command, or cut the docs down to the exact current engine.
- Add tests for every policy schema field documented.

### P1: "Fail-closed" needs stricter semantics

The project promises fail-closed. In `Gate.evaluate()`, policy-load exceptions are logged and then evaluation continues. Audit logger failures mutate the reason but do not block an otherwise passed call. That may be acceptable in observe/dev mode, but it is not the strictest interpretation of fail-closed.

Fix:

- Define failure semantics explicitly:
  - Missing/invalid policy in enforce mode: block.
  - Audit write failure in enforce mode: block or configurable `audit_failure_action`.
  - Unknown capability with policy present: deny unless explicitly configured.
- Add tests named around the promise: `test_fail_closed_on_policy_error`, `test_fail_closed_on_audit_error`, `test_unknown_capability_denied_by_default`.

### P1: Scoring is useful but not yet infrastructure-grade by itself

The deterministic policy engine is the infrastructure piece. Keyword/regex/AST scoring is useful, but it is not enough to claim robust malicious intent detection. The benchmark docs are honest about synthetic limitations; keep that honesty visible.

Fix:

- Position scoring as an assistive risk signal, not the primary trust boundary.
- Make explicit capability policy the hero.
- Add policy-first examples where no scorer is needed to block high-risk actions.

### P1: Need production recipes, not only primitives

A strong OSS infrastructure project gives users copy-paste patterns:

- Block destructive shell commands.
- Require approval for production DB writes.
- Gate MCP filesystem access to allowed roots.
- Require approval for payments over threshold.
- Block SaaS admin role changes.
- Observe mode rollout with CI.
- Replay incident trace after policy change.

Fix:

- Create `recipes/` or `docs/recipes/`.
- Each recipe should include policy YAML, Python integration, CLI verification, expected output, and tests.

### P1: Adapters need compatibility contracts

Framework integrations are a growth lever, but users need to know exactly what versions and tool interfaces are supported.

Fix:

- Add integration compatibility matrix:
  - LangChain version range.
  - LangGraph version range.
  - CrewAI version range.
  - OpenAI Agents SDK assumptions.
  - MCP protocol limitations.
- Add tiny runnable examples for each adapter in CI where dependencies are available.

### P1: The demo story is underused

The fintech demo is a good starting point, but it should be a flagship narrative: "See ShadowAudit stop an agent from moving money."

Fix:

- Move a polished demo walkthrough into README and docs.
- Record a GIF or terminal cast.
- Add `make demo` or `just demo`.
- Add a hosted demo page on `shadowaudit.dev`.

### P2: OSS growth surface is weak

GitHub currently shows 4 stars and 0 forks. That is normal early, but the repo does not yet give visitors enough social proof or easy contribution paths.

Fix:

- Add "good first issue" tickets for policy fields, recipes, integrations, docs examples.
- Use GitHub Discussions with prompts:
  - "What agent framework should ShadowAudit support next?"
  - "Share your risky tool pattern."
  - "Policy recipes wanted."
- Add a contributor map:
  - taxonomies
  - integrations
  - policy recipes
  - examples
  - docs

## README Recommendation

The README should be reorganized around urgency and proof:

1. One-line category:
   "ShadowAudit is a deterministic runtime authorization layer for AI agent tool calls."

2. Immediate danger demo:
   Agent tries `rm -rf /var/lib/postgresql`; ShadowAudit blocks before execution.

3. 60-second install and direct gate example:
   No LangChain required. This proves the primitive.

4. Policy-as-code:
   Show allow, deny, require approval.

5. Framework integrations:
   Show compact cards/table, not long prose.

6. Audit/replay:
   Show `shadowaudit verify`, `shadowaudit replay`, and hash-chain proof.

7. Rollout path:
   Observe -> tune -> enforce -> audit.

8. What ShadowAudit is / is not:
   It is runtime authorization and audit infrastructure.
   It is not prompt injection prevention, a model evaluator, or a replacement for sandboxing.

9. Production recipes:
   Link to shell, database, payments, MCP, SaaS admin.

10. Status and trust:
    261 tests, typed package, CI matrix, beta status, known limitations.

## Website Recommendation

`shadowaudit.dev` has a stronger landing-page shape than the GitHub README, but it has stale claims and some wording that can sound premature.

Change:

- Replace "Battle-tested" unless there is public proof.
- Update stale website test-count/coverage language to a generated/current metric or remove it.
- Align supported Python/framework claims with package metadata.
- Replace "Every tool call is scored" with "Every tool call is evaluated against policy, with optional risk scoring."
- Add a real demo artifact and docs link to `shadowaudit.dev`, not only GitHub Pages.

## Product Focus To Become Infrastructure Necessity

The project becomes necessary when it is the default safety boundary before agent tool execution. To get there, focus on these pillars:

### Pillar 1: Policy-first authorization

Make the core behavior boring, explicit, and undeniable:

- default deny mode
- known capability registry
- schema validation
- policy tests
- policy diff simulation
- policy bundles for common agent tools

### Pillar 2: Operational rollout

Security tools get adopted when rollout is safe:

- observe mode
- audit logs
- tuning suggestions
- CI checks
- replay before policy changes
- clear error messages

### Pillar 3: Framework-native integrations

Be the easiest way to gate tools in:

- LangChain
- LangGraph
- CrewAI
- OpenAI Agents SDK
- MCP
- PydanticAI
- AutoGen
- LlamaIndex

### Pillar 4: Proof

Earn trust:

- real examples
- reproducible demos
- compatibility matrix
- public benchmarks with caveats
- threat model
- known limitations
- security policy

### Pillar 5: Community recipes

Stars come from developers seeing themselves in the project:

- "Protect shell tools"
- "Protect DB writes"
- "Protect payment agents"
- "Secure MCP filesystem"
- "Human approval for admin changes"
- "CI gate for agent tools"

## 1000-Star Plan

### First 7 days

- Fix version/URL/test-count/doc inconsistencies.
- Rewrite `docs/index.md`.
- Rewrite README around proof, demo, and rollout.
- Add "What ShadowAudit does not do."
- Add 5 production recipes.
- Open 10 high-quality good-first issues.
- Pin a GitHub Discussion asking for risky tool patterns.

### First 30 days

- Implement or correct the policy schema docs.
- Add `shadowaudit check-policy`.
- Add strict fail-closed policy/audit tests.
- Add PydanticAI or LlamaIndex adapter.
- Publish a polished fintech demo.
- Write a launch post: "AI agents need runtime authorization, not just guardrails."
- Submit to relevant communities: Hacker News, r/Python, r/LocalLLaMA, LangChain community, MCP community, OWASP/AppSec circles.

### First 90 days

- Add a capability registry and policy test runner.
- Add real-world trace examples from community contributors.
- Add Splunk/Datadog/OTel export or at least documented log shipping.
- Add Docker/sidecar deployment pattern for MCP gateway.
- Build a small policy cookbook.
- Recruit maintainers for integrations and taxonomies.

## Issue Backlog

Suggested GitHub issues:

1. Align version metadata with PyPI release.
2. Replace docs homepage placeholder with real landing documentation.
3. Sync README, PyPI long description, website, and docs.
4. Implement or remove unsupported policy schema fields.
5. Add `shadowaudit check-policy`.
6. Fail closed on policy load error in enforce mode.
7. Define and test audit-write failure behavior.
8. Add default-deny unknown capability mode.
9. Add production policy recipes.
10. Add integration compatibility matrix.
11. Add runnable CI smoke tests for each framework adapter.
12. Add PydanticAI adapter.
13. Add LlamaIndex adapter.
14. Add AutoGen adapter.
15. Add OpenTelemetry/log shipping guide.
16. Add hosted fintech demo walkthrough.
17. Add README terminal GIF or asciinema.
18. Add security model and limitations to README.
19. Add contributor guide for taxonomies.
20. Add benchmark summary with caveats to docs.

## Bottom Line

ShadowAudit has the bones of a serious infrastructure project. The name, concept, and current codebase are pointing in the right direction.

The main problem is not lack of scope. The main problem is trust compression: the project needs to make its strongest claims faster, prove them with runnable demos, and remove every inconsistency that makes a security-minded user pause.

If the next phase focuses on policy correctness, fail-closed semantics, docs honesty, production recipes, and launch storytelling, this can credibly move from "interesting agent safety package" to "default runtime authorization layer for agent tools."
