"""Example: OWASP Agentic Top 10 coverage report (Week 8).

Generates an HTML report showing how CapFence maps to OWASP risks.
"""

from pathlib import Path
from capfence.assessment.owasp import generate_owasp_context


def main():
    ctx = generate_owasp_context()
    summary = ctx["summary"]

    print("OWASP Agentic Top 10 Coverage Matrix")
    print("=" * 50)
    print(f"Total risks:       {summary['total']}")
    print(f"Covered:           {summary['covered']}")
    print(f"Not covered:       {summary['not_covered']}")
    print(f"Full coverage:     {summary['full']}")
    print(f"Partial coverage:  {summary['partial']}")
    print(f"Coverage:          {summary['coverage_percent']}%")
    print()

    print(f"{'ID':<6} {'Risk':<35} {'Level':<12} {'Covered'}")
    print("-" * 65)
    for item in ctx["items"]:
        covered = "Yes" if item["covered"] else "No"
        level = item["coverage_level"]
        print(f"{item['risk_id']:<6} {item['risk_name']:<35} {level:<12} {covered}")

    # Generate HTML report
    from capfence.assessment.reporter import _get_template_dir, _risk_color, _risk_bg
    import jinja2

    tpl_dir = _get_template_dir()
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(tpl_dir)),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )
    env.filters["risk_color"] = _risk_color
    env.filters["risk_bg"] = _risk_bg

    template = env.get_template("report_owasp.html")
    html = template.render(**ctx)

    output = Path("capfence-owasp-report.html")
    output.write_text(html, encoding="utf-8")
    print(f"\nHTML report written to: {output}")


if __name__ == "__main__":
    main()
