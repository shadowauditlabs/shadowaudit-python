"""Tests for AST scanner (check.py)."""

import ast
from pathlib import Path

from shadowaudit.check import (
    ToolFinding,
    _guess_category,
    _is_tool_classdef,
    _is_tool_functiondef,
    _find_tool_classes,
    _find_shadowaudit_wrappers,
    scan_file,
    scan_directory,
    compute_aggregate_score,
)


class TestGuessCategory:
    def test_shell_tool(self):
        cat, delta = _guess_category("ShellTool", "Execute shell commands")
        assert cat == "execute"
        assert delta == 0.1

    def test_payment_tool(self):
        cat, delta = _guess_category("StripePaymentTool")
        assert cat == "payment_initiation"
        assert delta == 0.3

    def test_delete_tool(self):
        cat, delta = _guess_category("DeleteAccount")
        assert cat == "delete"
        assert delta == 0.2

    def test_read_tool(self):
        cat, delta = _guess_category("GetBalance", "Check account balance")
        assert cat == "read_only"
        assert delta == 1.0

    def test_unknown_tool(self):
        cat, delta = _guess_category("MyWeirdTool")
        assert cat is None
        assert delta == 0.1  # default restrictive


class TestIsToolClassDef:
    def test_base_tool_subclass(self):
        code = "class MyTool(BaseTool): pass"
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_classdef(node)
        assert is_tool is True
        assert fw == "base_tool"

    def test_not_a_class(self):
        code = "x = 1"
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_classdef(node)
        assert is_tool is False

    def test_regular_class(self):
        code = "class MyClass(object): pass"
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_classdef(node)
        assert is_tool is False


class TestFindToolClasses:
    def test_finds_tools(self):
        code = """
class ShellTool(BaseTool):
    pass
class Helper:
    pass
class PaymentTool(BaseTool):
    pass
"""
        tree = ast.parse(code)
        tools = _find_tool_classes(tree)
        assert len(tools) == 2
        names = [t[0] for t in tools]
        assert "ShellTool" in names
        assert "PaymentTool" in names


class TestFindShadowAuditWrappers:
    def test_detects_wrapper(self):
        code = """
from shadowaudit.framework.langchain import ShadowAuditTool
safe_shell = ShadowAuditTool(tool=ShellTool(), agent_id="test")
"""
        tree = ast.parse(code)
        wrapped = _find_shadowaudit_wrappers(tree)
        assert "ShellTool" in wrapped

    def test_no_wrapper(self):
        code = "shell = ShellTool()"
        tree = ast.parse(code)
        wrapped = _find_shadowaudit_wrappers(tree)
        assert len(wrapped) == 0


class TestScanFile:
    def test_scan_mock_example(self, tmp_path):
        code = """
from langchain.tools import BaseTool

class ShellTool(BaseTool):
    name = "shell"
    description = "Run shell commands"
    
    def _run(self, cmd: str) -> str:
        return f"Executed: {cmd}"

class PaymentTool(BaseTool):
    name = "payment"
    description = "Process payments"
    
    def _run(self, amount: float) -> str:
        return f"Paid: {amount}"

# This one is wrapped
from shadowaudit.framework.langchain import ShadowAuditTool
safe_shell = ShadowAuditTool(tool=ShellTool(), agent_id="ops-1", risk_category="execute")
"""
        f = tmp_path / "test_tools.py"
        f.write_text(code)
        
        findings = scan_file(f)
        
        assert len(findings) == 2
        
        shell = next(f for f in findings if f.name == "ShellTool")
        assert shell.category == "execute"
        assert shell.is_wrapped is True  # ShadowAuditTool detected
        
        payment = next(f for f in findings if f.name == "PaymentTool")
        assert payment.category == "payment_initiation"
        assert payment.is_wrapped is False


class TestScanDirectory:
    def test_recursive_scan(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        
        f1 = src / "tools.py"
        f1.write_text("""
from langchain.tools import BaseTool

class DeleteTool(BaseTool):
    name = "delete"
    def _run(self, x: str) -> str: return f"Deleted: {x}"
""")
        
        sub = src / "utils"
        sub.mkdir()
        f2 = sub / "helpers.py"
        f2.write_text("""
from langchain.tools import BaseTool

class ReadTool(BaseTool):
    name = "read"
    def _run(self, x: str) -> str: return f"Read: {x}"
""")
        
        f3 = src / "readme.md"
        f3.write_text("# Tools")
        
        findings = scan_directory(src)
        
        names = [f.name for f in findings]
        assert "DeleteTool" in names
        assert "ReadTool" in names
        assert len(findings) == 2


class TestComputeAggregateScore:
    def test_empty(self):
        score, label = compute_aggregate_score([])
        assert score == 0
        assert label == "SAFE"

    def test_all_gated(self):
        findings = [
            ToolFinding("Tool1", Path("/tmp"), 1, is_wrapped=True, risk_delta=0.1),
            ToolFinding("Tool2", Path("/tmp"), 2, is_wrapped=True, risk_delta=0.3),
        ]
        score, label = compute_aggregate_score(findings)
        assert score == 0
        assert label == "SAFE"

    def test_high_risk_ungated(self):
        findings = [
            ToolFinding("Shell", Path("/tmp"), 1, is_wrapped=False, risk_delta=0.1),
            ToolFinding("Delete", Path("/tmp"), 2, is_wrapped=False, risk_delta=0.2),
            ToolFinding("Payment", Path("/tmp"), 3, is_wrapped=False, risk_delta=0.3),
        ]
        score, label = compute_aggregate_score(findings)
        assert score == 70  # 3/3 * 50 = 50 + min(2*10, 40) = 20
        assert label == "HIGH"


class TestIsToolFunctionDef:
    def test_simple_decorator(self):
        code = """
@tool
def my_func(x):
    pass
"""
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_functiondef(node)
        assert is_tool is True
        assert fw == "langchain"

    def test_not_a_function(self):
        code = "x = 1"
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_functiondef(node)
        assert is_tool is False

    def test_regular_function(self):
        code = "def normal(): pass"
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_functiondef(node)
        assert is_tool is False

    def test_capital_tool_decorator(self):
        code = """
@Tool
def my_func(x):
    pass
"""
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_functiondef(node)
        assert is_tool is True
        assert fw == "langchain"


class TestFindToolClassesWithDecorators:
    def test_mixed_class_and_decorated_function(self):
        code = """
class MyTool(BaseTool):
    pass

@tool
def my_decorated_func(x):
    pass

class RegularClass:
    pass
"""
        tree = ast.parse(code)
        tools = _find_tool_classes(tree)
        assert len(tools) == 2
        names = [t[0] for t in tools]
        assert "MyTool" in names
        assert "my_decorated_func" in names


class TestFrameworkDisambiguation:
    def test_langchain_full_import(self):
        code = "class MyTool(langchain.tools.BaseTool): pass"
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_classdef(node)
        assert is_tool is True
        assert fw == "langchain"

    def test_crewai_import(self):
        code = "class MyCrewTool(crewai.tools.BaseTool): pass"
        tree = ast.parse(code)
        node = tree.body[0]
        is_tool, fw = _is_tool_classdef(node)
        assert is_tool is True
        assert fw == "crewai"
