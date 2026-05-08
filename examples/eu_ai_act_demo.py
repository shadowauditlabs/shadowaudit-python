"""Example: EU AI Act Annex IV evidence pack (Week 11).

Generates a compliance evidence pack for AI system conformity assessment.
"""

from pathlib import Path
from shadowaudit.assessment.scanner import scan_assessment
from shadowaudit.assessment.eu_ai_act import generate_evidence_pack


def main():
    # Scan the examples directory for tools
    data = scan_assessment(Path("./examples"), taxonomy_path="general")

    # Generate evidence pack
    pack = generate_evidence_pack(
        data=data,
        system_name="ShadowAudit Demo Agent",
        system_version="0.4.0",
    )

    print("EU AI Act Annex IV Evidence Pack")
    print("=" * 50)
    print(f"System:     {pack.system_name}")
    print(f"Version:    {pack.system_version}")
    print(f"Generated:  {pack.generated_at}")
    print()

    # Print risk management summary
    rm = pack.risk_management
    print("Risk Management:")
    print(f"  Tool count:       {rm.get('tool_count', 0)}")
    print(f"  Ungated tools:    {rm.get('ungated_tools', 0)}")
    print(f"  Critical ungated: {rm.get('critical_ungated', 0)}")
    print(f"  Risk score:       {rm.get('risk_score', 'N/A')}/100 ({rm.get('risk_label', 'N/A')})")

    # Print cybersecurity section
    cs = pack.cybersecurity
    print(f"\nCybersecurity:")
    print(f"  OWASP coverage: {cs.get('owasp_agentic_coverage', 'N/A')}")
    print(f"  Covered risks:  {cs.get('covered_risks', 0)}")
    print(f"  Full coverage:  {cs.get('full_coverage', 0)}")

    # Write outputs
    pack.write_json(Path("eu-ai-act-evidence.json"))
    pack.write_html(Path("eu-ai-act-evidence.html"))
    print(f"\nEvidence pack written to:")
    print(f"  JSON: eu-ai-act-evidence.json")
    print(f"  HTML: eu-ai-act-evidence.html")


if __name__ == "__main__":
    main()
