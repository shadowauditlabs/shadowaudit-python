# Replay + Trace Engine

CapFence includes a deterministic Replay and Trace engine to ensure **explainability** and **auditability**.

## Features
- **Deterministic Replay**: Re-evaluate past execution traces to understand enforcement paths.
- **Trace Viewer**: Terminal UI to visualize execution flow, risk escalation, triggered policies, and enforcement decisions.
- **Structured JSON Traces**: Audit logs can be exported and replayed across environments.

## CLI Commands

### View a Trace
```bash
capfence trace <trace_id>
```
Output clearly shows:
- Tool invocation
- Capability mapping
- Risk evaluation
- Triggered rules
- Final decision

### Replay a Trace
```bash
capfence replay trace.jsonl
```
This is useful for debugging policy changes or reproducing an incident.
