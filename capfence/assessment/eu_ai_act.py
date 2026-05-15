"""EU AI Act Annex IV evidence pack generator.

Produces a structured evidence package for high-risk AI system
conformity assessment under EU AI Act Article 12 and Annex IV.

Usage:
    from capfence.assessment.eu_ai_act import generate_evidence_pack
    from capfence.assessment.scanner import scan_assessment

    data = scan_assessment(Path("./src"), taxonomy_path="financial")
    pack = generate_evidence_pack(data)
    pack.write_html(Path("annex_iv_evidence.html"))
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from capfence.assessment.scanner import AssessmentData
from capfence.assessment.owasp import get_coverage_summary


@dataclass
class EvidencePack:
    """Structured EU AI Act Annex IV evidence package."""

    system_name: str
    system_version: str
    generated_at: str
    risk_management: dict[str, Any] = field(default_factory=dict)
    data_governance: dict[str, Any] = field(default_factory=dict)
    technical_documentation: dict[str, Any] = field(default_factory=dict)
    record_keeping: dict[str, Any] = field(default_factory=dict)
    transparency: dict[str, Any] = field(default_factory=dict)
    human_oversight: dict[str, Any] = field(default_factory=dict)
    accuracy_robustness: dict[str, Any] = field(default_factory=dict)
    cybersecurity: dict[str, Any] = field(default_factory=dict)
    owasp_coverage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_name": self.system_name,
            "system_version": self.system_version,
            "generated_at": self.generated_at,
            "annex_iv_sections": {
                "1_risk_management": self.risk_management,
                "2_data_governance": self.data_governance,
                "3_technical_documentation": self.technical_documentation,
                "4_record_keeping": self.record_keeping,
                "5_transparency": self.transparency,
                "6_human_oversight": self.human_oversight,
                "7_accuracy_robustness": self.accuracy_robustness,
                "8_cybersecurity": self.cybersecurity,
            },
            "owasp_agentic_coverage": self.owasp_coverage,
        }

    def _validate_output_path(self, path: Path) -> Path:
        """Resolve and validate output path to prevent directory traversal."""
        resolved = path.resolve()
        # Reject paths containing parent-directory references
        if ".." in path.parts:
            raise ValueError(f"Output path cannot contain '..' components: {path}")
        return resolved

    def write_json(self, path: Path) -> None:
        safe_path = self._validate_output_path(path)
        safe_path.write_text(json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8")

    def write_html(self, path: Path) -> None:
        safe_path = self._validate_output_path(path)
        from capfence.assessment.reporter import _get_template_dir, _risk_color, _risk_bg
        import jinja2
        tpl_dir = _get_template_dir()
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(tpl_dir)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        env.filters["risk_color"] = _risk_color
        env.filters["risk_bg"] = _risk_bg
        try:
            template = env.get_template("report_eu_ai_act.html")
        except jinja2.TemplateNotFound:
            template = env.from_string(_FALLBACK_EU_TEMPLATE)
        html = template.render(**self.to_dict())
        safe_path.write_text(html, encoding="utf-8")


def generate_evidence_pack(
    data: AssessmentData,
    system_name: str = "CapFence-Governed Agent",
    system_version: str = "0.4.0",
) -> EvidencePack:
    """Generate an Annex IV evidence pack from assessment data."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    owasp = get_coverage_summary()

    pack = EvidencePack(
        system_name=system_name,
        system_version=system_version,
        generated_at=now,
        risk_management={
            "description": "Risk identification and analysis for AI agent tool calls.",
            "tool_count": data.total_tools,
            "ungated_tools": data.ungated_count,
            "critical_ungated": data.critical_ungated,
            "risk_score": data.risk_score,
            "risk_label": data.risk_label,
            "mitigation": "CapFence Gate provides deterministic fail-closed enforcement with taxonomy-based thresholds.",
            "residual_risk": "Low — all high-risk tool calls are intercepted and scored before execution.",
        },
        data_governance={
            "description": "Training data governance is outside CapFence scope. This section covers operational data.",
            "audit_log_integrity": "Hash-chained SQLite audit log with SHA-256 linkage. Tamper-evident.",
            "payload_handling": "Payloads are hashed (SHA-256) before storage. Raw payloads never stored in audit log.",
            "retention_policy": "Audit logs retained per customer policy. SQLite format supports long-term archival.",
        },
        technical_documentation={
            "description": "Technical documentation of the AI system and its governance layer.",
            "architecture": "CapFence sits between the agent and its tools. Gate evaluates every call before execution.",
            "components": [
                "Gate (rule-based evaluator)",
                "TaxonomyLoader (risk category configuration)",
                "Scorer (pluggable risk scoring)",
                "AuditLogger (append-only hash-chained log)",
                "AgentStateStore (behavioral K/V tracking)",
                "FailClosedFSM (deterministic state machine)",
            ],
            "version": system_version,
            "source": "https://github.com/capfencelabs/capfence",
        },
        record_keeping={
            "description": "Automatic recording of events for traceability.",
            "audit_log_format": "SQLite with hash-chained entries.",
            "recorded_fields": [
                "timestamp", "agent_id", "task_context", "risk_category",
                "decision", "risk_score", "threshold", "payload_hash", "reason", "latency_ms",
                "prev_hash", "entry_hash", "signature",
            ],
            "verification_command": "capfence verify --audit-log ./audit.db",
            "retention": "Customer-defined. SQLite supports indefinite retention.",
        },
        transparency={
            "description": "Transparency information for deployers and end-users.",
            "system_purpose": "Runtime governance layer for AI agent tool calls in regulated workloads.",
            "capabilities": "Deterministic fail-closed enforcement, tamper-evident audit logging, behavioral scoring.",
            "limitations": "Does not inspect LLM prompts. Does not validate tool outputs. Focused on tool-call interception.",
            "known_risks": "Prompt injection may bypass tool-call gating if the agent is manipulated to not call tools.",
        },
        human_oversight={
            "description": "Human oversight measures.",
            "measures": [
                "Gate decisions are logged and auditable.",
                "CI/CD integration (--fail-on-ungated) prevents deployment of ungated high-risk tools.",
                "Assessment reports provide human-readable risk breakdowns with remediation steps.",
            ],
            "intervention": "Administrators can adjust taxonomy thresholds, add risk keywords, or disable specific tools via taxonomy configuration.",
        },
        accuracy_robustness={
            "description": "Accuracy, robustness, and cybersecurity.",
            "accuracy": "Keyword and regex-based scoring is deterministic. Same payload always produces same score.",
            "robustness": "Fail-closed design: any error or anomaly results in a block, not a pass.",
            "cybersecurity": "OWASP Agentic Top 10 coverage matrix included. See separate cybersecurity section.",
        },
        cybersecurity={
            "description": "Cybersecurity measures.",
            "owasp_agentic_coverage": f"{owasp['coverage_percent']}% of OWASP Agentic AI Top 10 risks covered.",
            "covered_risks": owasp["covered"],
            "full_coverage": owasp["full"],
            "partial_coverage": owasp["partial"],
            "mitigations": [
                "Excessive Agency: taxonomy-based gate blocks unauthorized tool categories.",
                "Insecure Plugin Design: CapFenceTool wrapper enforces access controls and input scoring.",
                "Agent Escape: command execution taxonomy with strict thresholds blocks shell escapes.",
                "Denial of Service: velocity tracking (V metric) detects tool-call spikes.",
                "Sensitive Information Disclosure: payload hashing prevents raw data exposure in logs.",
            ],
        },
        owasp_coverage=owasp,
    )
    return pack


_FALLBACK_EU_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>EU AI Act Annex IV Evidence Pack — {{ system_name }}</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 40px; background: #f8f9fa; color: #1f2937; }
        h1 { font-size: 1.8rem; }
        h2 { font-size: 1.3rem; margin-top: 2rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
        .meta { color: #6b7280; margin-bottom: 2rem; }
        table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; }
        th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #f3f4f6; font-weight: 600; }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
    </style>
</head>
<body>
    <h1>EU AI Act Annex IV Evidence Pack</h1>
    <p class="meta">{{ system_name }} v{{ system_version }} &middot; Generated {{ generated_at }}</p>

    {% for section_name, section in annex_iv_sections.items() %}
    <h2>{{ section_name.replace('_', ' ').title() }}</h2>
    <table>
        {% for key, value in section.items() %}
        <tr>
            <th>{{ key.replace('_', ' ').title() }}</th>
            <td>
                {% if value is sequence and value is not string %}
                    <ul>
                    {% for item in value %}
                        <li>{{ item }}</li>
                    {% endfor %}
                    </ul>
                {% else %}
                    {{ value }}
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    {% endfor %}

    <h2>OWASP Agentic Coverage</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Coverage Percent</td><td>{{ owasp_agentic_coverage.coverage_percent }}%</td></tr>
        <tr><td>Full Coverage</td><td>{{ owasp_agentic_coverage.full }}</td></tr>
        <tr><td>Partial Coverage</td><td>{{ owasp_agentic_coverage.partial }}</td></tr>
        <tr><td>Planned</td><td>{{ owasp_agentic_coverage.planned }}</td></tr>
    </table>
</body>
</html>
"""
