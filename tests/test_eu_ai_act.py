"""Tests for EU AI Act Annex IV evidence pack generator."""

from pathlib import Path

from capfence.assessment.eu_ai_act import generate_evidence_pack
from capfence.assessment.scanner import AssessmentData, ToolAssessment


class TestEvidencePack:
    def test_generate_from_empty_data(self):
        data = AssessmentData(path=Path("/tmp"), taxonomy_name="general", tools=[])
        pack = generate_evidence_pack(data, system_name="TestAgent", system_version="0.4.0")
        assert pack.system_name == "TestAgent"
        assert pack.system_version == "0.4.0"
        assert pack.risk_management["tool_count"] == 0
        assert pack.risk_management["risk_label"] == "SAFE"
        assert pack.generated_at

    def test_generate_with_tools(self):
        tools = [
            ToolAssessment("Shell", Path("/tmp"), 1, "langchain", "execute", False, 0.1),
            ToolAssessment("Read", Path("/tmp"), 2, "langchain", "read_only", True, 1.0),
        ]
        data = AssessmentData(path=Path("/tmp"), taxonomy_name="general", tools=tools)
        pack = generate_evidence_pack(data)
        assert pack.risk_management["tool_count"] == 2
        assert pack.risk_management["ungated_tools"] == 1
        assert pack.owasp_coverage["total"] == 10

    def test_write_json(self, tmp_path):
        data = AssessmentData(path=Path("/tmp"), taxonomy_name="general", tools=[])
        pack = generate_evidence_pack(data)
        out = tmp_path / "pack.json"
        pack.write_json(out)
        assert out.exists()
        content = out.read_text()
        assert "system_name" in content
        assert "annex_iv_sections" in content

    def test_write_html(self, tmp_path):
        data = AssessmentData(path=Path("/tmp"), taxonomy_name="general", tools=[])
        pack = generate_evidence_pack(data)
        out = tmp_path / "pack.html"
        pack.write_html(out)
        assert out.exists()
        content = out.read_text()
        assert "EU AI Act" in content
