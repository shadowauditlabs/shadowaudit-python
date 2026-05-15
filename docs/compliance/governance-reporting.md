# Governance Reporting

CapFence produces reports that help security, platform, and compliance teams understand how agent tool execution is controlled.

## Reports

| Report | Command | Purpose |
|---|---|---|
| Tool gating scan | `capfence check ./src` | Find ungated agent tools. |
| Assessment report | `capfence assess ./src` | Summarize risk and coverage. |
| OWASP matrix | `capfence owasp` | Map controls to OWASP Agentic AI risks. |
| EU AI Act evidence | `capfence eu-ai-act ./src` | Generate evidence documentation. |
| Audit verification | `capfence verify --audit-log audit.db` | Prove audit chain integrity. |

## Operating model

Run reports in CI for drift detection, during release reviews for policy changes, and after incidents for forensic review.

## Evidence to retain

- policy files used at release time
- CI scan output
- replay reports for material incidents
- approval records for sensitive actions
- verified audit logs

