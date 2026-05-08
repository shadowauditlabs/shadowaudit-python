# Security Policy

## Supported Versions

Only the latest release in the 0.4.x line is actively supported with security patches. As the project is in alpha, earlier minor versions are not maintained.

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4.0 | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in ShadowAudit, please report it responsibly.

**Do not file a public GitHub issue.** Public issues for security bugs expose all users to the vulnerability before a fix is available.

Instead, email **security@shadowaudit.dev** with the following information:

- A clear description of the vulnerability and its impact
- Steps to reproduce, or a minimal proof of concept if possible
- The version(s) affected
- Any suggested mitigation or fix

You will receive an acknowledgment within **72 hours** of triage. We will keep you informed of our progress and coordinate disclosure once a fix is ready.

## Disclosure Policy

ShadowAudit follows a **90-day coordinated disclosure** standard:

1. We acknowledge receipt of the report within 72 hours.
2. We investigate and develop a fix.
3. We release a patched version and publish an advisory.
4. We publicly credit the reporter (with their consent) in the advisory and CHANGELOG.

If a fix is not ready within 90 days, we will work with the reporter to agree on an extension or an early public disclosure with mitigations.

## Scope

### In-scope

Vulnerabilities in ShadowAudit code that could lead to:

- **Gate bypass** — an agent tool call that should be blocked is allowed through
- **Audit log tampering** — modification, deletion, or forgery of audit entries without invalidating the hash chain or signature
- **License validation flaws** — circumvention of any licensing or entitlement checks (when applicable)
- **Path traversal** — unauthorized file system access via CLI or API inputs
- **Command injection** — execution of arbitrary commands via MCP gateway or scanner inputs
- **Information disclosure** — leakage of private keys, API tokens, or raw payload data through logs, telemetry, or error messages

### Out-of-scope

- Vulnerabilities in third-party dependencies (report to the respective project)
- Social engineering or physical attacks
- Attacks requiring write access to the host file system outside of ShadowAudit's intended deployment model
- Denial of service via resource exhaustion in the OSS SDK (the compiled enterprise tier addresses performance hardening)

## Security-related Configuration

- **Ed25519 signing**: Enable `sign_entries=True` in `AuditLogger` for cryptographic authenticity. Store the private key with `0o600` permissions.
- **Telemetry**: Disabled by default. When enabled, only hashed metadata is transmitted — no raw payloads leave the system.
- **MCP Gateway**: Run with least-privilege upstream commands. Validate that `upstream_command` does not contain user-controlled input.

## Past Advisories

Security fixes are documented in [CHANGELOG.md](CHANGELOG.md) under the "Security" or "Fixed" sections for each release.
