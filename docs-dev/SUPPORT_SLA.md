# CapFence Support SLA

**Effective:** May 2026

## Support Tiers

| Tier | Response Time | Channel | Hours |
|---|---|---|---|
| **OSS (Free)** | Best-effort | [GitHub Issues](https://github.com/capfencelabs/capfence/issues) | When available |
| **Cloud Starter ($99/mo)** | 2 business days | Email | Monday–Friday, 9am–6pm IST |
| **Cloud Team (Future)** | 1 business day | Email + Intercom | Monday–Friday, 9am–6pm IST |
| **Enterprise ($25K/yr)** | 4 business hours | Email + dedicated Slack channel | Monday–Friday, 9am–6pm IST. 24h response on weekends/holidays. |
| **Enterprise+ ($75K/yr)** | 1 business hour (P0/P1), 4 business hours (P2) | Phone + Slack | Monday–Friday, 24h coverage |

## Severity Definitions

| Level | Definition | Example |
|---|---|---|
| **P0 — Critical** | Production system down. Gate is blocking all calls or failing open. | All agent tool calls returning errors. |
| **P1 — High** | Major functionality broken. Specific tool category blocked incorrectly. | Payment tools blocked despite correct configuration. |
| **P2 — Medium** | Non-critical issue. Workaround available. | Report generation slow, cosmetic issues. |
| **P3 — Low** | Minor issue. Feature request. | Documentation clarification, taxonomy suggestions. |

## What's Covered

- CapFence SDK installation and configuration
- Gate evaluation and taxonomy questions
- Audit log verification and integrity checks
- Framework adapter integration (LangChain, CrewAI, LangGraph, OpenAI Agents)
- MCP gateway setup and troubleshooting
- Assessment report interpretation

## What's Not Covered

- Custom taxonomy development (available as a paid service)
- Integration with proprietary/internal agent frameworks
- General AI/ML consulting
- Security audits of customer codebases

## Contact

- **OSS:** Open an issue on [GitHub](https://github.com/capfencelabs/capfence/issues)
- **Cloud/Enterprise:** Email support@capfence.dev

---

*This SLA is reviewed quarterly. Response times are targets, not guarantees. Force majeure events (natural disasters, major internet outages) may affect response times.*
