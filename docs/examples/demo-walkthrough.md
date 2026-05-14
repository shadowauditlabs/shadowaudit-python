# Demo Walkthrough

This demo highlights ShadowAudit's static scan, assessment, live gate decisions, trace simulation, and audit verification workflows using the bundled fintech demo project.

## Why this demo exists

Prompt guardrails are not enforcement. This demo shows a deterministic gate that blocks tool calls before execution and records a tamper-evident audit trail.

## Where it sits in your stack

```
Agent framework -> ShadowAudit gate -> Tool/API/DB/Shell
```

ShadowAudit does not replace sandboxing or least-privilege credentials. It complements them by enforcing runtime policy at the tool boundary.

## Rollout story (observe → enforce → audit)

1. Observe: scan the codebase and assess coverage.
2. Enforce: block and allow real tool calls with policy.
3. Audit: verify the hash chain and replay traces.

## Prerequisites

- Python 3.10+
- Local repo checkout
- Virtual environment with ShadowAudit installed (`pip install -e ".[dev]"`)

## Run the demo

```bash
chmod +x ./scripts/demo.sh
./scripts/demo.sh
```

## Optional: add a short overlay for the cast

If you share the demo cast, add a brief text overlay (or preface) that says:

"This is a deterministic gate between an agent and its tools. The demo shows scan, enforcement, simulation, and audit verification in under two minutes."

## Expected output (example)

```text
[DEMO] Running ShadowAudit demo from repo root
[DEMO] Deterministic runtime authorization for agent tool calls, enforced before execution.
[SCAN] 8 tool(s) found in shadowaudit-demo/src
  Gated: 6
  Ungated: 2
  High-risk ungated: 1

Assessment report written to: shadowaudit-demo/shadowaudit-assessment-report.html
[INFO] Assessment exited with status 2 (expected when critical ungated tools exist).
[GATE] passed=False reason=policy_deny
[GATE] passed=True reason=policy_allow
Replayed 50 tool call(s):
  Static rules blocked:     0
  Adaptive would block:     0
  Additional flagged:       0
[RECOMMENDATION] Static rules caught all issues. No adaptive gap detected.
[VERIFY] Audit chain: VALID
  No tampering detected.
[POLICY] VALID: policies/production_shell_policy.yaml
  Rules: 2
  Risk levels: 0
```

## Next steps

- Open `shadowaudit-demo/shadowaudit-assessment-report.html` to review findings.
- Try `shadowaudit check` on your own project.
