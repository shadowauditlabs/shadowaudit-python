"""HTML report generator using Jinja2 templates.

Renders professional, shareable assessment reports from AssessmentData.

Usage:
    from shadowaudit.assessment.scanner import scan_assessment
    from shadowaudit.assessment.reporter import generate_html_report
    
    data = scan_assessment(Path("./src"))
    html = generate_html_report(data, output_path=Path("report.html"))
"""

from __future__ import annotations

from pathlib import Path

import jinja2

from shadowaudit.assessment.scanner import AssessmentData


def _get_template_dir() -> Path:
    """Return the directory containing Jinja2 templates."""
    return Path(__file__).parent / "templates"


# Module-level cached environment for performance
_jinja_env: jinja2.Environment | None = None

def _get_jinja_env() -> jinja2.Environment:
    """Return a cached Jinja2 environment with registered filters."""
    global _jinja_env
    if _jinja_env is None:
        tpl_dir = _get_template_dir()
        _jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(tpl_dir)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            cache_size=128,
        )
        _jinja_env.filters["risk_color"] = _risk_color
        _jinja_env.filters["risk_bg"] = _risk_bg
    return _jinja_env

def _risk_color(risk_label: str) -> str:
    """Return CSS color hex for a risk level."""
    return {
        "CRITICAL": "#7c2d12",  # dark red
        "HIGH": "#dc2626",      # red
        "MEDIUM": "#d97706",    # amber
        "LOW": "#059669",       # green
        "SAFE": "#2563eb",      # blue
    }.get(risk_label, "#6b7280")


def _risk_bg(risk_level: str) -> str:
    """Return CSS background color for a risk level."""
    return {
        "CRITICAL": "#fef2f2",
        "HIGH": "#fef2f2",
        "MEDIUM": "#fffbeb",
        "LOW": "#f0fdf4",
        "SAFE": "#eff6ff",
    }.get(risk_level, "#f9fafb")


def generate_html_report(
    data: AssessmentData,
    output_path: Path | None = None,
) -> str:
    """Generate an HTML assessment report.
    
    Args:
        data: AssessmentData from scan_assessment()
        output_path: Optional path to write the HTML file
        
    Returns:
        The HTML string (also written to output_path if provided)
    """
    env = _get_jinja_env()
    try:
        template = env.get_template("report.html")
    except jinja2.TemplateNotFound:
        # Fallback: use inline template if file missing
        template = env.from_string(_FALLBACK_TEMPLATE)
    
    # Prepare context
    context = data.to_dict()
    context["version"] = "0.3.0"
    context["has_findings"] = len(data.tools) > 0
    context["has_critical"] = data.critical_ungated > 0
    context["has_high"] = data.high_ungated > 0
    context["needs_action"] = data.ungated_count > 0
    
    html = template.render(**context)
    
    if output_path:
        output_path.write_text(html, encoding="utf-8")
    
    return html


# Fallback inline template if file is missing
_FALLBACK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ShadowAudit Report — {{ path_name }}</title>
    <style>body{font-family:system-ui,sans-serif;margin:40px;background:#f8f9fa;}</style>
</head>
<body><h1>ShadowAudit Report</h1><p>{{ path }}</p></body>
</html>
"""


