# Gate API Reference

`capfence.core.gate.Gate` is the core enforcement object. Framework adapters call it internally, and custom runtimes can call it directly.

## Constructor

```python
from capfence.core.audit import AuditLogger
from capfence.core.gate import Gate

gate = Gate(
    taxonomy_path="financial",
    audit_logger=AuditLogger(db_path="audit.db"),
    mode="enforce",
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `state_store` | `AgentStateStore \| None` | `None` | Optional agent state store. |
| `taxonomy_path` | `str \| None` | `None` | Built-in taxonomy name or taxonomy path. |
| `cloud_client` | `Any \| None` | `None` | Optional cloud client. |
| `audit_logger` | `AuditLogger \| None` | in-memory logger | Audit logger for decision records. |
| `scorer` | `BaseScorer \| None` | default scorer | Optional scoring implementation. |
| `mode` | `str` | `"enforce"` | `"enforce"` or `"observe"`. |
| `policy_loader` | `PolicyLoader \| None` | default loader | Optional policy loader. |
| `approval_manager` | `ApprovalManager \| None` | in-memory manager | Optional approval queue manager. |

Use `AuditLogger(db_path="audit.db")` when you want decisions persisted to disk.

## `gate.evaluate()`

```python
result = gate.evaluate(
    agent_id="my-agent",
    task_context="shell",
    risk_category="shell_execution",
    capability="shell.execute",
    payload={"command": "ls -la /tmp"},
    policy_path="policies/shell.yaml",
)
```

| Parameter | Type | Description |
|---|---|---|
| `agent_id` | `str` | Identifier for the calling agent. |
| `task_context` | `str` | Logical grouping label for audit, such as `"shell"`. |
| `risk_category` | `str \| None` | Risk taxonomy category. |
| `payload` | `dict` | Tool arguments. |
| `capability` | `str \| None` | Capability matched against policy rules. |
| `policy_path` | `str \| None` | Policy file used for this evaluation. |
| `policy_context` | `dict \| None` | Runtime metadata such as environment or role. |
| `require_human_approval` | `bool` | Force approval for this call. |

## `GateResult`

| Field | Type | Description |
|---|---|---|
| `passed` | `bool` | Whether the call is authorized to proceed. |
| `risk_score` | `float \| None` | Risk score from evaluation. |
| `threshold` | `float \| None` | Threshold used for the decision. |
| `risk_category` | `str \| None` | Evaluated risk category. |
| `reason` | `str \| None` | Explanation for the decision. |
| `latency_ms` | `int \| None` | Evaluation latency. |
| `metadata` | `dict` | Additional decision metadata, including policy details. |

CapFence’s current direct result model is pass/fail. Policy outcomes such as approval are represented through result metadata and approval queue state.

## `gate.evaluate_async()`

Async version of `evaluate()` with the same parameters:

```python
result = await gate.evaluate_async(
    agent_id="async-agent",
    task_context="api",
    risk_category="api_call",
    capability="api.call",
    payload={"url": "https://example.com"},
    policy_path="policies/api.yaml",
)
```

## Observe mode

```python
gate = Gate(mode="observe")
```

Observe mode records what would have happened, but returns a passing result so teams can tune policies before switching to fail-closed enforcement.

## Example

```python
from capfence.core.audit import AuditLogger
from capfence.core.gate import Gate

gate = Gate(audit_logger=AuditLogger(db_path="audit.db"))

payload = {"amount": 2500, "to_account": "external-bank"}

result = gate.evaluate(
    agent_id="prod-agent",
    task_context="payments",
    risk_category="financial_transaction",
    capability="payments.transfer",
    payload=payload,
    policy_path="policies/payments.yaml",
    policy_context={"environment": "production", "user_role": "analyst"},
)

if result.passed:
    execute_transfer(payload)
else:
    log.warning("Transfer blocked: %s", result.reason)
```

