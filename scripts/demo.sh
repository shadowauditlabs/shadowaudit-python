#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$repo_root"

export PYTHONPATH="$repo_root"

python_cmd="$repo_root/.venv/bin/python"
if [ ! -x "$python_cmd" ]; then
  python_cmd="python"
  if ! command -v "$python_cmd" >/dev/null 2>&1; then
    python_cmd="python3"
  fi
fi

printf "\n[DEMO] Running CapFence demo from repo root\n"
printf "[DEMO] Deterministic runtime authorization for agent tool calls, enforced before execution.\n"

printf "\n[STEP] Scan demo project for ungated tools\n"
"$python_cmd" -m capfence.cli check "capfence-demo/src"

printf "\n[STEP] Generate HTML assessment report\n"
set +e
"$python_cmd" -m capfence.cli assess "capfence-demo/src" --taxonomy financial \
  --output "capfence-demo/capfence-assessment-report.html"
assess_status=$?
set -e
if [ "$assess_status" -ne 0 ]; then
  printf "[INFO] Assessment exited with status %s (expected when critical ungated tools exist).\n" "$assess_status"
fi

printf "\n[STEP] Run a live Gate decision (block + allow)\n"
"$python_cmd" - <<'PY'
from capfence.core.audit import AuditLogger
from capfence.core.gate import Gate

audit_path = "capfence-demo/audit.db"
policy_path = "policies/production_shell_policy.yaml"

gate = Gate(audit_logger=AuditLogger(db_path=audit_path))

blocked = gate.evaluate(
    agent_id="demo-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path=policy_path,
    payload={"command": "rm -rf /tmp/cache"},
)
print(f"[GATE] passed={blocked.passed} reason={blocked.reason}")

allowed = gate.evaluate(
    agent_id="demo-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    policy_path=policy_path,
    payload={"command": "ls -la /tmp"},
)
print(f"[GATE] passed={allowed.passed} reason={allowed.reason}")
PY

printf "\n[STEP] Simulate trace replay\n"
"$python_cmd" -m capfence.cli simulate --trace-file "tests/corpus/benign_traces.jsonl" --taxonomy general

printf "\n[STEP] Verify audit log hash chain\n"
"$python_cmd" -m capfence.cli verify --audit-log "capfence-demo/audit.db"

printf "\n[STEP] Validate a sample policy file\n"
"$python_cmd" -m capfence.cli check-policy "policies/production_shell_policy.yaml"

printf "\n[DEMO] Done. Review the HTML report in capfence-demo/\n"
