# Configuration Reference

CapFence is configured through constructor parameters and policy files. There is no required global configuration file.

## Gate configuration

```python
from capfence.core.audit import AuditLogger
from capfence.core.gate import Gate

gate = Gate(
    taxonomy_path="financial",
    audit_logger=AuditLogger(db_path="audit.db"),
    mode="enforce",
)
```

| Parameter | Description |
|---|---|
| `taxonomy_path` | Built-in taxonomy name or path to a taxonomy file. |
| `audit_logger` | Audit logger instance. Use `AuditLogger(db_path="audit.db")` for persistent logs. |
| `mode` | `"enforce"` blocks unauthorized calls. `"observe"` logs without blocking. |
| `approval_manager` | Optional approval queue manager. |
| `policy_loader` | Optional policy loader. |

## Adapter configuration

```python
from capfence import CapFenceTool
from capfence.core.audit import AuditLogger
from capfence.core.gate import Gate

gate = Gate(audit_logger=AuditLogger(db_path="audit.db"))

safe_tool = CapFenceTool(
    tool=my_tool,
    agent_id="my-agent",
    capability="shell.execute",
    policy_path="policies/shell.yaml",
    gate=gate,
)
```

Adapters add framework-specific wrapping around the same gate primitive.

## Policy file location

Policy files can live anywhere on disk. A common layout is:

```text
policies/
  production.yaml
  staging.yaml
  agents/
    finance-agent.yaml
    ops-agent.yaml
```

## Audit database location

By default, `AuditLogger()` uses an in-memory database. Configure a path for persistent audit logs:

```python
from capfence.core.audit import AuditLogger
from capfence.core.gate import Gate

gate = Gate(
    audit_logger=AuditLogger(db_path="/var/log/myapp/capfence.db")
)
```

## Approval timeout

Set approval timeout in the policy file:

```yaml
approval_timeout_seconds: 3600
```

## Logging

CapFence uses the standard Python `logging` module under the `capfence` logger name.

```python
import logging

logging.getLogger("capfence").setLevel(logging.WARNING)
```

