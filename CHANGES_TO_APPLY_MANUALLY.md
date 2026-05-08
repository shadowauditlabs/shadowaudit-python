# Manual GitHub UI Changes

The following changes must be applied through the GitHub web interface. They cannot be committed as files in the repository.

## 1. Fix Repository Topic Typo

- **Current:** `secuirty` (typo)
- **Action:** Remove `secuirty`, add `security`
- **Location:** Repository Settings → Topics

## 2. Add Additional Topics

Add the following topics to improve discoverability:

- `agent-security`
- `auditing`
- `owasp`
- `eu-ai-act`
- `fintech`

**Location:** Repository Settings → Topics

## 3. Update Repository Description

Set the repository description to the v0.4.0 one-line tagline:

> Runtime governance for AI agents — deterministic fail-closed enforcement with auditor-defensible cryptographic audit logs.

**Location:** Repository Settings → Description

## 4. Create GitHub Release for v0.4.0

- **Current state:** Only v0.3.2 is tagged as a GitHub Release
- **Action:** Create a new Release for tag `v0.4.0`
- **Release notes:** Copy the v0.4.0 section from `CHANGELOG.md`
- **Title:** `ShadowAudit v0.4.0 — Hash chains, Ed25519, OWASP, MCP, LangGraph, OpenAI Agents, EU AI Act, Plaid`

**Location:** Releases → Draft a new release → Choose tag `v0.4.0`

## 5. Enable GitHub Discussions

Enable Discussions and create the following categories:

- **Announcements** (maintainers only)
- **Q&A**
- **Show and Tell**
- **Ideas**

**Location:** Repository Settings → Discussions → Enable

## 6. Pin an Issue

Create and pin the following issue (or convert an existing discussion):

**Title:** `Roadmap & v0.4.0 launch — share your use case`

**Body:**
```
ShadowAudit v0.4.0 is now live. If you're using it in production, a PoC, or evaluating it for compliance, we'd love to hear your use case.

Specifically helpful:
- What framework are you using? (LangChain, CrewAI, LangGraph, OpenAI Agents, MCP, custom)
- What vertical? (fintech, legal, healthcare, general)
- What's your biggest governance gap today?
- What would make you buy a hosted dashboard?

No marketing fluff — just real feedback we use to prioritize the roadmap.
```

**Location:** Issues → New Issue → Pin to top

## 7. (Optional) Set Social Preview Image

Upload a 1280×640px social preview image for the repository. This appears when the repo is shared on Twitter, LinkedIn, etc.

**Location:** Repository Settings → Social preview

---

After applying these changes, this file can be deleted.
