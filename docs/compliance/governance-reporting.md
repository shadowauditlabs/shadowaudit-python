# Governance Reporting

ShadowAudit produces reports that help security, platform, and compliance teams understand how agent tool execution is controlled.

## Reports

| Report | Command | Purpose |
|---|---|---|
| Tool gating scan | `shadowaudit check ./src` | Find ungated agent tools. |
| Assessment report | `shadowaudit assess ./src` | Summarize risk and coverage. |
| OWASP matrix | `shadowaudit owasp` | Map controls to OWASP Agentic AI risks. |
| EU AI Act evidence | `shadowaudit eu-ai-act ./src` | Generate evidence documentation. |
| Audit verification | `shadowaudit verify --audit-log audit.db` | Prove audit chain integrity. |

## Operating model

Run reports in CI for drift detection, during release reviews for policy changes, and after incidents for forensic review.

## Evidence to retain

- policy files used at release time
- CI scan output
- replay reports for material incidents
- approval records for sensitive actions
- verified audit logs

