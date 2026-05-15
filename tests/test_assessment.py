"""Tests for assessment module (scanner + reporter)."""

from pathlib import Path


from capfence.assessment.scanner import (
    ToolAssessment,
    AssessmentData,
    scan_assessment,
)
from capfence.assessment.reporter import generate_html_report


class TestToolAssessment:
    def test_risk_level_critical(self):
        t = ToolAssessment("Shell", Path("/tmp"), 1, None, None, False, 0.1)
        assert t.risk_level == "CRITICAL"
    
    def test_risk_level_high(self):
        t = ToolAssessment("Delete", Path("/tmp"), 1, None, None, False, 0.2)
        assert t.risk_level == "CRITICAL"
    
    def test_risk_level_high_write(self):
        t = ToolAssessment("Write", Path("/tmp"), 1, None, None, False, 0.4)
        assert t.risk_level == "HIGH"
    
    def test_risk_level_low(self):
        t = ToolAssessment("Read", Path("/tmp"), 1, None, None, False, 1.0)
        assert t.risk_level == "LOW"
    
    def test_needs_action_wrapped(self):
        t = ToolAssessment("Shell", Path("/tmp"), 1, None, None, True, 0.1)
        assert not t.needs_action
    
    def test_needs_action_ungated_critical(self):
        t = ToolAssessment("Shell", Path("/tmp"), 1, None, None, False, 0.1)
        assert t.needs_action
    
    def test_needs_action_ungated_safe(self):
        t = ToolAssessment("Read", Path("/tmp"), 1, None, None, False, 1.0)
        assert not t.needs_action  # LOW risk doesn't need action
    
    def test_to_dict(self):
        t = ToolAssessment(
            name="TestTool",
            file=Path("/tmp/test.py"),
            line=10,
            framework="langchain",
            category="execute",
            is_wrapped=False,
            risk_delta=0.1,
            taxonomy_description="Run commands",
            risk_keywords=["shell", "execute"],
            remediation="Wrap it",
        )
        d = t.to_dict()
        assert d["name"] == "TestTool"
        assert d["risk_level"] == "CRITICAL"
        assert d["needs_action"] is True


class TestAssessmentData:
    def test_empty(self):
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=[])
        assert data.risk_score == 0
        assert data.risk_label == "SAFE"
        assert data.total_tools == 0
        assert data.coverage_percent == 100.0
    
    def test_all_gated_safe(self):
        tools = [
            ToolAssessment("Read1", Path("/tmp"), 1, None, None, True, 1.0),
            ToolAssessment("Read2", Path("/tmp"), 2, None, None, True, 1.0),
        ]
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=tools)
        assert data.risk_score == 0
        assert data.risk_label == "SAFE"
        assert data.gated_count == 2
        assert data.coverage_percent == 100.0  # LOW risk, excluded from coverage
    
    def test_high_risk_ungated(self):
        tools = [
            ToolAssessment("Shell", Path("/tmp"), 1, None, None, False, 0.1),
            ToolAssessment("Delete", Path("/tmp"), 2, None, None, False, 0.2),
            ToolAssessment("Payment", Path("/tmp"), 3, None, None, False, 0.3),
        ]
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=tools)
        assert data.risk_label == "HIGH"
        assert data.ungated_count == 3
        assert data.critical_ungated == 2  # delta 0.1 and 0.2
        assert data.high_ungated == 1  # delta 0.3
        assert data.coverage_percent == 0.0
    
    def test_partial_coverage(self):
        tools = [
            ToolAssessment("Shell", Path("/tmp"), 1, None, None, False, 0.1),
            ToolAssessment("Delete", Path("/tmp"), 2, None, None, True, 0.2),
        ]
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=tools)
        assert data.coverage_percent == 50.0
    
    def test_categories_summary(self):
        tools = [
            ToolAssessment("Shell", Path("/tmp"), 1, "langchain", "execute", False, 0.1),
            ToolAssessment("Rm", Path("/tmp"), 2, "langchain", "execute", True, 0.1),
            ToolAssessment("Pay", Path("/tmp"), 3, "langchain", "payment", False, 0.3),
        ]
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=tools)
        assert "execute" in data.categories
        assert data.categories["execute"]["count"] == 2
        assert data.categories["execute"]["gated"] == 1
        assert data.categories["execute"]["ungated"] == 1
        assert data.categories["execute"]["critical"] == 1


class TestScanAssessment:
    def test_scan_empty_dir(self, tmp_path):
        data = scan_assessment(tmp_path)
        assert data.total_tools == 0
        assert data.risk_label == "SAFE"
    
    def test_scan_with_tools(self, tmp_path):
        f = tmp_path / "tools.py"
        f.write_text("""
from langchain.tools import BaseTool

class ShellTool(BaseTool):
    name = "shell"
    def _run(self, cmd): return cmd

class ReadTool(BaseTool):
    name = "read"
    def _run(self, q): return q
""")
        data = scan_assessment(tmp_path)
        assert data.total_tools == 2
        names = [t.name for t in data.tools]
        assert "ShellTool" in names
        assert "ReadTool" in names
    
    def test_scan_with_taxonomy(self, tmp_path):
        f = tmp_path / "tools.py"
        f.write_text("""
from langchain.tools import BaseTool

class PaymentTool(BaseTool):
    name = "payment"
    def _run(self, amt): return amt
""")
        data = scan_assessment(tmp_path, taxonomy_path="general")
        payment = next(t for t in data.tools if t.name == "PaymentTool")
        assert payment.category == "payment_initiation"
    
    def test_scan_framework_filter(self, tmp_path):
        f = tmp_path / "tools.py"
        # Import from langchain.tools resolves to "langchain" framework
        f.write_text("""
from langchain.tools import BaseTool

class MyTool(BaseTool):
    name = "my"
    def _run(self, x): return x
""")
        # Framework detection resolves to "langchain" from import path
        data = scan_assessment(tmp_path, framework="langchain")
        assert data.total_tools == 1
        
        data = scan_assessment(tmp_path, framework="crewai")
        assert data.total_tools == 0


class TestGenerateHtmlReport:
    def test_empty_report(self):
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=[])
        html = generate_html_report(data)
        assert "No AI Agent Tools Detected" in html
    
    def test_report_with_findings(self):
        tools = [
            ToolAssessment("Shell", Path("/tmp"), 1, None, None, False, 0.1),
            ToolAssessment("Read", Path("/tmp"), 2, None, None, True, 1.0),
        ]
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=tools)
        html = generate_html_report(data)
        assert "Shell" in html
        assert "Read" in html
        assert "CRITICAL" in html
    
    def test_report_writes_file(self, tmp_path):
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=[])
        output = tmp_path / "report.html"
        generate_html_report(data, output_path=output)
        assert output.exists()
        content = output.read_text()
        assert "CapFence" in content
    
    def test_report_includes_remediation(self):
        tools = [
            ToolAssessment("Shell", Path("/tmp"), 1, "langchain", "execute",
                          False, 0.1, remediation="Wrap with CapFenceTool"),
        ]
        data = AssessmentData(path=Path("/tmp"), taxonomy_name=None, tools=tools)
        html = generate_html_report(data)
        assert "Remediation" in html
        assert "CapFenceTool" in html
