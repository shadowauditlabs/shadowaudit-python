"""Assessment toolkit for ShadowAudit.

Orchestrates static analysis into professional deliverables:
- scanner.py: Enriches raw AST findings with taxonomy data
- reporter.py: Generates HTML reports via Jinja2 templates
- simulator.py: Replays agent traces through the gate (Month 2)
- builder.py: Interactive taxonomy builder (Month 2)
"""

from shadowaudit.assessment.scanner import scan_assessment, AssessmentData
from shadowaudit.assessment.reporter import generate_html_report

__all__ = [
    "scan_assessment",
    "AssessmentData",
    "generate_html_report",
]
