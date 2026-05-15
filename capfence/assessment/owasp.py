"""OWASP Agentic Top 10 coverage matrix.

Maps CapFence capabilities to the OWASP Agentic AI Top 10 risks.
Generates a coverage matrix and HTML report section.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OWASPCoverageItem:
    """Single OWASP risk coverage entry."""
    risk_id: str
    risk_name: str
    description: str
    covered: bool
    coverage_level: str  # "full", "partial", "planned", "not_applicable"
    capfence_feature: str
    notes: str = ""


# OWASP Agentic AI Top 10 (2025 draft) coverage mapping
_OWASP_COVERAGE: list[OWASPCoverageItem] = [
    OWASPCoverageItem(
        risk_id="AA01",
        risk_name="Prompt Injection",
        description="Direct and indirect prompt injection attacks that manipulate agent behavior.",
        covered=True,
        coverage_level="partial",
        capfence_feature="Gate evaluates payload content against risk keywords; blocks dangerous tool calls regardless of prompt origin.",
        notes="CapFence does not inspect LLM prompts — it intercepts tool calls. This mitigates the execution phase of prompt injection.",
    ),
    OWASPCoverageItem(
        risk_id="AA02",
        risk_name="Insecure Output Handling",
        description="Agent outputs used without validation, leading to XSS, SSRF, or injection.",
        covered=False,
        coverage_level="not_applicable",
        capfence_feature="N/A",
        notes="CapFence governs tool calls, not output rendering. Use traditional output encoding.",
    ),
    OWASPCoverageItem(
        risk_id="AA03",
        risk_name="Excessive Agency",
        description="Agent performs actions beyond intended scope (deletion, payment, privilege escalation).",
        covered=True,
        coverage_level="full",
        capfence_feature="Taxonomy-based gate with per-category thresholds. Blocks unauthorized tool categories entirely.",
        notes="Core value proposition. Every tool call is checked against taxonomy before execution.",
    ),
    OWASPCoverageItem(
        risk_id="AA04",
        risk_name="Overreliance",
        description="Users or systems trust agent outputs without verification.",
        covered=False,
        coverage_level="not_applicable",
        capfence_feature="N/A",
        notes="Human-in-the-loop and output verification are outside CapFence scope.",
    ),
    OWASPCoverageItem(
        risk_id="AA05",
        risk_name="Model Theft",
        description="Extraction of model weights, architecture, or training data.",
        covered=False,
        coverage_level="not_applicable",
        capfence_feature="N/A",
        notes="Model security is orthogonal to runtime tool-call governance.",
    ),
    OWASPCoverageItem(
        risk_id="AA06",
        risk_name="Sensitive Information Disclosure",
        description="Agent leaks PII, credentials, or proprietary data in outputs or logs.",
        covered=True,
        coverage_level="partial",
        capfence_feature="Payload hashing in audit log. No raw payloads stored. Compliance reports map to PCI-DSS / SOX.",
        notes="Audit log stores SHA-256 hashes, not raw data. Reduces exposure surface.",
    ),
    OWASPCoverageItem(
        risk_id="AA07",
        risk_name="Insecure Plugin Design",
        description="Agent plugins/tools lack access controls, input validation, or rate limiting.",
        covered=True,
        coverage_level="full",
        capfence_feature="CapFenceTool wrapper enforces access controls, input scoring, and rate/velocity tracking per agent_id.",
        notes="Drop-in wrapper for any tool. No plugin modification required.",
    ),
    OWASPCoverageItem(
        risk_id="AA08",
        risk_name="Denial of Service",
        description="Agent consumes excessive resources through loops, recursion, or tool spam.",
        covered=True,
        coverage_level="partial",
        capfence_feature="Velocity tracking (V metric) detects tool-call spikes. FSM fail-closed on anomaly.",
        notes="Behavioral velocity detection. Full rate-limiting requires upstream infrastructure.",
    ),
    OWASPCoverageItem(
        risk_id="AA09",
        risk_name="Supply Chain",
        description="Compromised dependencies, model weights, or training data.",
        covered=False,
        coverage_level="not_applicable",
        capfence_feature="N/A",
        notes="Use SCA tools (Snyk, Dependabot) for supply chain. CapFence is runtime.",
    ),
    OWASPCoverageItem(
        risk_id="AA10",
        risk_name="Agent Escape",
        description="Agent breaks out of sandbox, accesses host system, or escalates privileges.",
        covered=True,
        coverage_level="partial",
        capfence_feature="Command execution taxonomy with strict thresholds. Blocks shell escapes and dangerous system calls.",
        notes="Mitigates tool-call-based escape vectors. Sandbox hardening is still required.",
    ),
]


def get_coverage_matrix() -> list[OWASPCoverageItem]:
    """Return the full OWASP Agentic Top 10 coverage matrix."""
    return list(_OWASP_COVERAGE)


def get_coverage_summary() -> dict[str, Any]:
    """Return aggregated coverage statistics."""
    items = get_coverage_matrix()
    total = len(items)
    full = sum(1 for i in items if i.coverage_level == "full")
    partial = sum(1 for i in items if i.coverage_level == "partial")
    planned = sum(1 for i in items if i.coverage_level == "planned")
    not_applicable = sum(1 for i in items if i.coverage_level == "not_applicable")
    covered = sum(1 for i in items if i.covered)
    return {
        "total": total,
        "covered": covered,
        "not_covered": total - covered,
        "full": full,
        "partial": partial,
        "planned": planned,
        "not_applicable": not_applicable,
        "coverage_percent": round((covered / total) * 100, 1) if total else 0.0,
    }


def generate_owasp_context() -> dict[str, Any]:
    """Generate template context for OWASP coverage report."""
    items = get_coverage_matrix()
    summary = get_coverage_summary()
    return {
        "items": [i.__dict__ for i in items],
        "summary": summary,
    }
