"""ShadowAudit CLI entry point.

Commands:
    check           Scan codebase for ungated AI agent tools
    assess          Generate detailed HTML assessment report
    simulate        Replay agent traces through ShadowAudit gate
    build-taxonomy  Interactive taxonomy builder

Usage:
    shadowaudit check ./src
    shadowaudit check ./src --output report.html
    shadowaudit check ./src --framework=langchain --fail-on-ungated
    shadowaudit simulate --trace-file agent_trace.jsonl --compare
    shadowaudit build-taxonomy
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from shadowaudit.check import scan_directory, scan_file, compute_aggregate_score, ToolFinding
from shadowaudit.assessment.scanner import scan_assessment, AssessmentData
from shadowaudit.assessment.reporter import generate_html_report
from shadowaudit.assessment.simulator import TraceSimulator
from shadowaudit.assessment.builder import TaxonomyBuilder


@click.group()
@click.version_option(version="0.3.3", prog_name="shadowaudit")
def main() -> None:
    """ShadowAudit — fail-closed deterministic enforcement for AI agent tool calls."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--framework", "-f", type=str, default=None,
              help="Filter by framework (langchain, crewai, autogen)")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None,
              help="Write HTML report to file")
@click.option("--fail-on-ungated", is_flag=True,
              help="Exit with non-zero code if ungated high-risk tools found")
def check(
    path: Path,
    framework: str | None,
    output: Path | None,
    fail_on_ungated: bool,
) -> None:
    """Scan Python files for ungated AI agent tool classes."""
    if path.is_file():
        findings = scan_file(path)
    else:
        findings = scan_directory(path)

    if framework:
        framework_lower = framework.lower()
        findings = [f for f in findings if f.framework and f.framework.lower() == framework_lower]

    _print_findings(findings, path)

    if output:
        _write_html_report(findings, output, path)
        click.echo(f"\nReport written to: {output}")

    if fail_on_ungated:
        high_risk_ungated = [f for f in findings if not f.is_wrapped and f.risk_delta <= 0.2]
        if high_risk_ungated:
            click.echo(
                f"\nCI FAILED: {len(high_risk_ungated)} high-risk ungated tool(s) found.",
                err=True,
            )
            sys.exit(1)
        else:
            click.echo("\nAll high-risk tools are gated.")


def _print_findings(findings: list[ToolFinding], path: Path) -> None:
    """Print findings table to stdout."""
    if not findings:
        click.echo(f"[SCAN] No tool classes found in {path}")
        click.echo("[RISK SCORE] 0/100 (SAFE)")
        click.echo("\nNo agent tools detected.")
        return

    click.echo(f"[SCAN] {len(findings)} tool(s) found in {path}")
    click.echo()
    click.echo(f"{'Tool':<25} {'Framework':<12} {'Category':<20} {'Gated?':<8} {'Risk':<8} {'File'}")
    click.echo("-" * 100)

    for finding in findings:
        gated = "YES" if finding.is_wrapped else "NO"
        risk = finding.risk_level()
        category = finding.category or "unknown"
        fw = finding.framework or "-"
        rel = _rel_path(finding.file, path)
        click.echo(
            f"{finding.name:<25} {fw:<12} {category:<20} {gated:<8} {risk:<8} {rel}:{finding.line}"
        )

    score, label = compute_aggregate_score(findings)
    ungated = sum(1 for f in findings if not f.is_wrapped)
    gated_count = len(findings) - ungated
    high_risk = sum(1 for f in findings if not f.is_wrapped and f.risk_delta <= 0.2)

    click.echo()
    click.echo(f"[RISK SCORE] {score}/100 ({label})")
    click.echo(f"  Total tools:     {len(findings)}")
    click.echo(f"  Gated:           {gated_count}")
    click.echo(f"  Ungated:         {ungated}")
    if high_risk:
        click.echo(f"  High-risk ungated: {high_risk}")

    if ungated > 0:
        click.echo()
        click.echo("[RECOMMENDATION]")
        click.echo("  Wrap ungated tools with ShadowAuditTool.")

    click.echo()
    click.echo("[ASSESSMENT] Run shadowaudit assess for detailed HTML report.")


def _rel_path(file_path: Path, base_path: Path) -> str:
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return file_path.name


def _write_html_report(findings: list[ToolFinding], output: Path, path: Path) -> None:
    from shadowaudit.assessment.scanner import AssessmentData, enrich_finding
    tools = [enrich_finding(f, None) for f in findings]
    data = AssessmentData(path=path, taxonomy_name=None, tools=tools)
    generate_html_report(data, output_path=output)


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None,
              help="Write detailed HTML assessment report")
@click.option("--taxonomy", "-t", type=str, default=None,
              help="Taxonomy to use (general, financial, legal, or path)")
@click.option("--compliance", "-c", is_flag=True,
              help="Include SOX/PCI-DSS compliance mapping in report")
def assess(path: Path, output: Path | None, taxonomy: str | None, compliance: bool) -> None:
    """Generate detailed HTML assessment report with taxonomy enrichment."""
    click.echo(f"[ASSESS] Running assessment on {path}...")
    if taxonomy:
        click.echo(f"[ASSESS] Using taxonomy: {taxonomy}")

    data = scan_assessment(path, taxonomy_path=taxonomy)

    click.echo(f"\n[RESULT] Risk Score: {data.risk_score}/100 ({data.risk_label})")
    click.echo(f"  Total tools: {data.total_tools}")
    click.echo(f"  Gated: {data.gated_count}")
    click.echo(f"  Ungated: {data.ungated_count}")
    if data.critical_ungated > 0:
        click.echo(f"  Critical ungated: {data.critical_ungated}")
    click.echo(f"  Coverage: {data.coverage_percent}%")

    if compliance:
        report_path = output or Path("shadowaudit-compliance-report.html")
        from shadowaudit.assessment.reporter import _get_template_dir, _risk_color, _risk_bg
        tpl_dir = _get_template_dir()
        import jinja2
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(tpl_dir)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        env.filters["risk_color"] = _risk_color
        env.filters["risk_bg"] = _risk_bg
        try:
            template = env.get_template("report_compliance.html")
            ctx = data.to_dict()
            ctx["version"] = "0.3.0"
            ctx["compliance_mappings"] = _get_compliance_context(data)
            html = template.render(**ctx)
            report_path.write_text(html, encoding="utf-8")
        except jinja2.TemplateNotFound:
            generate_html_report(data, output_path=report_path)
    else:
        report_path = output or Path("shadowaudit-assessment-report.html")
        generate_html_report(data, output_path=report_path)

    click.echo(f"\nAssessment report written to: {report_path}")

    if data.critical_ungated > 0:
        click.echo("\nAssessment: CRITICAL ungated tools found.", err=True)
        sys.exit(2)
    elif data.ungated_count > 0:
        click.echo("\nAssessment: Ungated tools found.", err=True)
        sys.exit(1)


def _get_compliance_context(data: AssessmentData) -> dict[str, Any]:
    """Generate compliance context for template rendering."""
    return {
        "sox_302": "AgentStateStore tracks all decisions for corporate responsibility reporting.",
        "sox_404": "AuditLogger provides append-only decision log for internal control assessment.",
        "pci_dss_3_4": "Hash module ensures payload integrity, rendering sensitive data unreadable.",
        "pci_dss_10_2": "All gate decisions logged with timestamp, agent ID, and payload hash.",
        "pci_dss_6_5": "Gate prevents unauthorized tool execution, addressing common coding vulnerabilities.",
    }


@main.command()
@click.option("--trace-file", "-t", type=click.Path(exists=True, path_type=Path), required=True,
              help="Path to JSONL trace file")
@click.option("--taxonomy", type=str, default="general",
              help="Taxonomy to use for simulation")
@click.option("--compare", is_flag=True,
              help="Show static vs adaptive side-by-side comparison")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None,
              help="Write simulation report to JSON file")
def simulate(trace_file: Path, taxonomy: str, compare: bool, output: Path | None) -> None:
    """Replay agent execution traces through ShadowAudit gate."""
    click.echo(f"[SIMULATE] Replaying trace: {trace_file}")
    click.echo(f"[SIMULATE] Using taxonomy: {taxonomy}")

    sim = TraceSimulator(taxonomy_path=taxonomy)
    summary = sim.run(trace_file=trace_file, verbose=False)

    click.echo()
    click.echo(f"Replayed {summary.total_calls} tool call(s):")
    click.echo(f"  Static rules blocked:     {summary.static_blocked}")
    click.echo(f"  Adaptive would block:     {summary.adaptive_blocked}")
    click.echo(f"  Additional flagged:       {summary.adaptive_additional_blocks}")

    if compare:
        click.echo()
        click.echo(f"{'Call ID':<10} {'Tool':<25} {'Static':<10} {'Adaptive':<10} {'Gap':<10}")
        click.echo("-" * 65)
        for r in summary.results:
            static_status = "BLOCKED" if r.static_blocked else "OK"
            adaptive_status = "BLOCKED" if r.adaptive_blocked else "OK"
            gap = (
                "{:.2f}".format(r.adaptive_delta)
                if r.adaptive_delta is not None else "-"
            )
            click.echo(f"{r.call_id:<10} {r.tool_name:<25} {static_status:<10} {adaptive_status:<10} {gap:<10}")

    if summary.patterns:
        click.echo()
        click.echo("[PATTERNS DETECTED]")
        for p in summary.patterns:
            click.echo(f"  {p}")

    click.echo()
    click.echo(f"[RECOMMENDATION] {summary.recommendation}")

    if output:
        out = {
            "total_calls": summary.total_calls,
            "static_blocked": summary.static_blocked,
            "adaptive_blocked": summary.adaptive_blocked,
            "adaptive_additional_blocks": summary.adaptive_additional_blocks,
            "patterns": summary.patterns,
            "recommendation": summary.recommendation,
            "details": [
                {
                    "call_id": r.call_id,
                    "tool_name": r.tool_name,
                    "static_blocked": r.static_blocked,
                    "adaptive_blocked": r.adaptive_blocked,
                    "adaptive_delta": r.adaptive_delta,
                }
                for r in summary.results
            ],
        }
        output.write_text(json.dumps(out, indent=2), encoding="utf-8")
        click.echo(f"\nSimulation report written to: {output}")


@main.command(name="build-taxonomy")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None,
              help="Output path for generated taxonomy JSON")
def build_taxonomy(output: Path | None) -> None:
    """Interactive taxonomy builder."""
    builder = TaxonomyBuilder()
    taxonomy = builder.interactive_build()

    path = output or Path(f"custom_taxonomy_{taxonomy['domain']}.json")
    builder.save(taxonomy, path)
    click.echo(f"\nTaxonomy saved to: {path}")


if __name__ == "__main__":
    main()


