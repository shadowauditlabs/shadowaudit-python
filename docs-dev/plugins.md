# Plugin Architecture

CapFence supports extensibility through a robust plugin system. You can extend core functionality with specialized modules.

## Supported Extension Points
- **Risk Evaluators**: Custom heuristics or ML models to score tool payloads.
- **Policy Evaluators**: New ways to write or fetch policies (e.g., OPA integration).
- **Capability Providers**: Dynamic discovery of capabilities.
- **Audit Sinks**: Forward audit logs to Datadog, Splunk, or S3.
- **Approval Providers**: Integrate with Slack, Jira, or PagerDuty for human-in-the-loop approvals.

## Example Layout

```
plugins/
    shell_guard/
    sql_risk_engine/
    pii_detector/
    mcp_governance/
```

## Registration

Use the explicit registry to load plugins:

```python
from capfence.core.plugins import default_registry

default_registry.register_risk_evaluator("pii_detector", PIIDetectorPlugin)
default_registry.register_audit_sink("splunk", SplunkSinkPlugin)
```
