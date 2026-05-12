# ShadowAudit Security Policy

As a runtime authorization layer for AI agents, security is our primary focus. ShadowAudit is designed to operate in highly regulated, air-gapped, and zero-trust environments.

## Enterprise Trust Signals & Architecture Guarantees

- **Offline-First & Air-Gapped**: ShadowAudit has zero external network dependencies. It does not phone home, it does not send telemetry by default, and it does not rely on cloud-hosted LLMs for policy evaluation.
- **Deterministic Enforcement**: Risk scoring relies on regex boundary matching and AST parsing. Unlike LLM-based guardrails, execution decisions are reproducible and predictable.
- **Hash-Chained Audit Logging**: Every evaluation is recorded in a local SQLite database. The cryptographic hash chain prevents tampering, ensuring forensic replayability.
- **Fail-Closed Execution**: If a tool call cannot be evaluated or exceeds risk thresholds, ShadowAudit raises a hard exception, halting the execution path immediately.
- **Thread Safety**: Core components are designed for high-concurrency, asynchronous agent frameworks with average latency overhead under 1 millisecond.

## Supported Versions

We currently support the following versions for security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4.0 | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in ShadowAudit, please do NOT open a public issue.

Instead, please send an email to **[anshuman1405@outlook.com](mailto:anshuman1405@outlook.com)**.

We will acknowledge receipt of your vulnerability report within 48 hours and provide a timeline for remediation. We prioritize vulnerabilities that allow:
- Bypassing the runtime gate.
- Tampering with the hash-chained audit log.
- Causing a denial of service in the evaluation pipeline.

## Threat Model

Please see our [Architecture Documentation](docs/architecture.md) for details on our enforcement model and how we mitigate prompt injection, shell destruction, and unauthorized API usage.
