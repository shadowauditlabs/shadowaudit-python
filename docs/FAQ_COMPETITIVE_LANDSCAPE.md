> **This is an internal sales asset.** Share with specific prospects who ask "why not Microsoft AGT?" or similar. Not linked from the public README intentionally — naming competitors in public materials is a defensive posture that ages badly. Update this doc as the competitive landscape changes.

# ShadowAudit vs. Microsoft Agent Governance Toolkit (AGT)

This document is an honest, technical comparison for architects and security teams evaluating runtime governance tools for AI agents.

## Comparison Table

| Dimension | Microsoft AGT | ShadowAudit |
|---|---|---|
| **License** | MIT | MIT (OSS SDK) |
| **Coverage** | All 10 OWASP Agentic risks | 3–5 of 10, focused on **tool-call execution** |
| **Vendor** | Microsoft | **Independent** |
| **Audit log** | Standard logging | **Hash-chained, Ed25519-signed, tamper-evident** |
| **Vertical taxonomies** | Generic | **Financial / fintech depth** (Stripe, Plaid) |
| **Air-gap deployment** | Possible but assembly required | **First-class — single `pip install`** |
| **EU AI Act evidence pack** | Compliance module exists | **Annex IV evidence-pack generator built-in** |
| **Hosted SaaS** | None | In development — contact for early access |
| **Solo-buyable for SMBs** | No | **Yes** |

## When to Use AGT Instead

Choose Microsoft AGT if:

- You need **horizontal coverage** across all 10 OWASP Agentic AI Top 10 risks, including model-level risks (prompt injection, model theft, overreliance) that ShadowAudit does not address.
- You are already in the **Microsoft ecosystem** (Azure, Entra ID, Sentinel) and want native integration.
- Your workloads are **not fintech-specific** — you need general-purpose agent governance across healthcare, retail, or industrial use cases.
- You need **multi-agent orchestration** governance at the framework level, not just per-tool call enforcement.

AGT is the right tool for breadth. It covers the full attack surface of agentic systems.

## When to Use ShadowAudit Instead

Choose ShadowAudit if:

- You need **auditor-defensible evidence**. A hash-chained, Ed25519-signed audit log with payload hashing is not "nice to have" — it is the difference between a conformity assessor accepting your evidence pack and rejecting it. ShadowAudit generates this by default.
- You operate in **financial services** and need taxonomy depth for Stripe, Plaid, ACH, wire transfers, and account modifications. Generic "payment" categories are insufficient for PCI-DSS scope reduction.
- You deploy in **air-gapped or regulated environments** where external API calls are prohibited. ShadowAudit is pure Python + SQLite. No cloud. No LLM calls. No API keys.
- You need **regulatory evidence packs** out of the box — EU AI Act Annex IV, NIST AI RMF, or internal governance reviews. The evidence pack generator produces structured JSON and HTML for regulatory submission.
- You are a **solo founder or SMB** who needs to buy governance tooling without an enterprise sales process.

ShadowAudit is the right tool for depth — specifically, the audit-defensibility and financial-vertical depth that regulated workloads require.

## When to Use Both

The tools are complementary, not competitive:

- **AGT for breadth** — deploy AGT as your horizontal governance layer. It covers model risks, prompt injection, supply chain, and agent escape that ShadowAudit does not.
- **ShadowAudit for depth** — deploy ShadowAudit as your per-tool enforcement and audit layer. It provides the cryptographic audit trail, financial taxonomies, and Annex IV evidence that AGT does not generate.

Example architecture:

```
Agent → AGT (horizontal risk scan) → ShadowAudit Gate (per-tool enforcement)
                                          ↓
                              Hash-chained, signed audit log
                                          ↓
                              EU AI Act Annex IV evidence pack
```

AGT tells you *what* risks exist. ShadowAudit tells you *what happened*, *when*, and *proves it* to an auditor.

## Honest Limitations of ShadowAudit

- **Not a model security tool**. ShadowAudit does not scan for prompt injection, jailbreaks, or model-level vulnerabilities. Use AGT or dedicated model security tools for that.
- **Not a general-purpose OWASP coverage tool**. We cover 3–5 of the 10 OWASP Agentic risks, focused on tool-call execution. The other risks are out of scope by design.
- **No hosted dashboard yet**. The Cloud tier is in development. For now, all reporting is local HTML/JSON.
- **No multi-agent orchestration**. ShadowAudit gates individual tool calls, not agent-to-agent communication patterns.

## Honest Limitations of AGT

- **No cryptographic audit chain**. AGT's logging is standard application logging. It does not provide tamper-evident, hash-chained, or signed audit entries.
- **No financial-vertical taxonomies**. AGT's risk categories are generic. You will need to build and maintain Stripe/Plaid/ACH-specific taxonomies yourself.
- **No EU AI Act Annex IV generator**. AGT has compliance modules, but not a built-in evidence pack generator for Annex IV submission.
- **Enterprise-only**. AGT is not available for solo purchase or SMB self-serve.

## Bottom Line

- **Use AGT** if you need horizontal OWASP coverage and are in the Microsoft ecosystem.
- **Use ShadowAudit** if you need auditor-defensible evidence, financial-vertical depth, or air-gap-pure deployment.
- **Use both** if you are a regulated enterprise running agentic workloads — AGT for breadth, ShadowAudit for the audit layer your conformity assessor will actually accept.
