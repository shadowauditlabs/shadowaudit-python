"""AST scanner for detecting ungated AI agent tools in Python code.

Walks Python source files to find tool class definitions (LangChain BaseTool,
CrewAI BaseTool, AutoGen Tool) and detects whether they are wrapped with
ShadowAuditTool enforcement.

Usage:
    from shadowaudit.check import scan_file, scan_directory
    findings = scan_directory(Path("./src"))
"""

import ast
from dataclasses import dataclass
from pathlib import Path



@dataclass(frozen=True)
class ToolFinding:
    """Represents a single tool discovery in a codebase."""
    name: str
    file: Path
    line: int
    framework: str | None = None
    category: str | None = None
    is_wrapped: bool = False
    risk_delta: float = 0.1
    description: str = ""
    
    def risk_level(self) -> str:
        """Return human-readable risk level based on delta."""
        if self.risk_delta <= 0.2:
            return "CRITICAL"
        elif self.risk_delta <= 0.4:
            return "HIGH"
        elif self.risk_delta < 1.0:
            return "MEDIUM"
        return "LOW"


# Priority-ordered category map: lower delta = higher priority (more restrictive)
_CATEGORY_MAP: list[tuple[str, float, list[str]]] = [
    ("permission_change", 0.1, ["permission", "grant", "revoke", "acl", "access", "role"]),
    ("execute", 0.1, ["shell", "execute", "exec", "command", "bash", "sh", "cmd", "terminal"]),
    ("data_export", 0.15, ["export", "download", "dump", "backup", "extract"]),
    ("delete", 0.2, ["delete", "remove", "destroy", "drop", "wipe", "erase", "purge"]),
    ("withdrawal", 0.2, ["withdraw", "cash_out", "drain", "debit"]),
    ("external_api", 0.2, ["external", "api_call", "third_party", "webhook", "outbound"]),
    ("payment_initiation", 0.3, ["transfer", "payment", "pay", "disburse", "wire", "send_money", "stripe", "refund", "payout"]),
    ("update", 0.3, ["update", "modify", "change", "edit", "patch"]),
    ("write", 0.4, ["write", "create", "insert", "post", "submit"]),
    ("read_only", 1.0, ["read", "get", "list", "view", "fetch", "search", "query", "find", "balance", "inquiry", "history"]),
]


def _guess_category(tool_name: str, description: str = "") -> tuple[str | None, float]:
    """Guess risk category from tool name and description.

    Priority-based: most restrictive (lowest delta) match wins.
    All keywords are evaluated; the category with the lowest delta
    among matching keyword sets is returned.

    Returns (category_name, delta) or (None, 0.1) for unknown.
    """
    text = (tool_name + " " + description).lower()

    matches: list[tuple[str, float]] = []
    for cat_name, delta, keywords in _CATEGORY_MAP:
        if any(kw in text for kw in keywords):
            matches.append((cat_name, delta))

    if not matches:
        return None, 0.1

    # Return lowest-delta (most restrictive) match
    return min(matches, key=lambda x: x[1])


def _extract_import_map(tree: ast.AST) -> dict[str, str]:
    """Extract a mapping of imported names to their full module paths.
    
    For 'from x.y import Z as W', returns {'W': 'x.y.Z'}
    For 'import x.y', returns {'x.y': 'x.y', 'x': 'x'}
    """
    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname or alias.name
                if module:
                    imports[name] = f"{module}.{alias.name}"
                else:
                    imports[name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                imports[name] = alias.name
    return imports


def _resolve_base_tool_framework(import_map: dict[str, str], name: str) -> str | None:
    """Resolve whether a bare BaseTool import is from langchain or crewai."""
    full_path = import_map.get(name, "").lower()
    if "crewai" in full_path:
        return "crewai"
    if "langchain" in full_path:
        return "langchain"
    return None


def _is_tool_classdef(node: ast.AST, import_map: dict[str, str] | None = None) -> tuple[bool, str | None]:
    """Check if an AST node is a BaseTool subclass definition.
    
    Returns (is_tool, framework_name).
    """
    if not isinstance(node, ast.ClassDef):
        return False, None
    
    imap = import_map or {}
    for base in node.bases:
        if isinstance(base, ast.Name):
            if base.id == "BaseTool":
                # Could be LangChain or CrewAI — resolve from imports
                resolved = _resolve_base_tool_framework(imap, base.id)
                return True, resolved or "base_tool"  # Generic if unresolvable
            if base.id in ("Tool", "FunctionTool"):
                return True, "autogen"
        elif isinstance(base, ast.Attribute):
            if base.attr == "BaseTool":
                # crewai.tools.BaseTool or crewai.BaseTool
                if isinstance(base.value, ast.Name) and base.value.id == "crewai":
                    return True, "crewai"
                if isinstance(base.value, ast.Attribute):
                    inner = base.value
                    if isinstance(inner.value, ast.Name) and inner.value.id == "crewai":
                        return True, "crewai"
                return True, "langchain"
    
    return False, None


def _is_tool_functiondef(node: ast.AST, import_map: dict[str, str] | None = None) -> tuple[bool, str | None]:
    """Check if an AST node is a function decorated with @tool.
    
    Returns (is_tool, framework_name).
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False, None
    
    imap = import_map or {}
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            if decorator.id in ("tool", "Tool"):
                if decorator.id in imap:
                    full_path = imap[decorator.id].lower()
                    if "crewai" in full_path:
                        return True, "crewai"
                return True, "langchain"  # @tool is LangChain convention
        elif isinstance(decorator, ast.Call):
            # @tool(...) with arguments
            if isinstance(decorator.func, ast.Name):
                if decorator.func.id in ("tool", "Tool"):
                    if decorator.func.id in imap:
                        full_path = imap[decorator.func.id].lower()
                        if "crewai" in full_path:
                            return True, "crewai"
                    return True, "langchain"
            elif isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ("tool", "Tool"):
                    if isinstance(decorator.func.value, ast.Name):
                        if decorator.func.value.id == "crewai":
                            return True, "crewai"
                    return True, "langchain"
    
    return False, None


def _find_tool_classes(tree: ast.AST) -> list[tuple[str, int, str | None]]:
    """Find all tool class definitions and decorated functions in an AST.
    
    Returns list of (name, line_number, framework_hint).
    """
    import_map = _extract_import_map(tree)
    tools: list[tuple[str, int, str | None]] = []
    
    for node in ast.walk(tree):
        is_tool, framework = _is_tool_classdef(node, import_map)
        if is_tool and isinstance(node, ast.ClassDef):
            tools.append((node.name, node.lineno, framework))
            continue
        
        is_decorated_tool, fw = _is_tool_functiondef(node, import_map)
        if is_decorated_tool and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tools.append((node.name, node.lineno, fw))
    
    return tools


def _find_shadowaudit_wrappers(tree: ast.AST) -> set[str]:
    """Find which tool classes are wrapped with ShadowAuditTool.
    
    Detects patterns like:
        safe_tool = ShadowAuditTool(tool=SomeTool(), ...)
        safe_tool = ShadowAuditTool(tool=SomeTool, ...)  # class reference
    
    Returns set of wrapped tool class names.
    """
    wrapped: set[str] = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            func_name = None
            
            # Direct: ShadowAuditTool(...)
            if isinstance(func, ast.Name) and func.id == "ShadowAuditTool":
                func_name = "ShadowAuditTool"
            # Imported: shadowaudit.framework.langchain.ShadowAuditTool(...)
            elif isinstance(func, ast.Attribute) and func.attr == "ShadowAuditTool":
                func_name = "ShadowAuditTool"
            
            if func_name and node.keywords:
                for kw in node.keywords:
                    if kw.arg == "tool":
                        # tool=SomeTool() — tool argument is a Call
                        if isinstance(kw.value, ast.Call):
                            if isinstance(kw.value.func, ast.Name):
                                wrapped.add(kw.value.func.id)
                            elif isinstance(kw.value.func, ast.Attribute):
                                wrapped.add(kw.value.func.attr)
                        # tool=SomeTool — tool argument is a Name (class reference)
                        elif isinstance(kw.value, ast.Name):
                            wrapped.add(kw.value.id)
    
    return wrapped


def scan_file(
    filepath: Path,
    *,
    global_wrapped: set[str] | None = None,
    _cached_tree: ast.AST | None = None,
) -> list[ToolFinding]:
    """Scan a single Python file for ungated tool classes.
    
    Args:
        filepath: Path to Python source file
        global_wrapped: Optional pre-computed set of wrapped tool names
                        from all files (enables cross-file detection).
        _cached_tree: Optional pre-parsed AST to avoid re-parsing.
        
    Returns:
        List of ToolFinding objects describing discovered tools
    """
    if _cached_tree is not None:
        tree = _cached_tree
    else:
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError:
            return []
        except UnicodeDecodeError:
            return []
        except PermissionError:
            return []
    
    tools = _find_tool_classes(tree)
    local_wrapped = _find_shadowaudit_wrappers(tree)
    
    # Merge local and global wrapped sets for cross-file detection
    wrapped = local_wrapped | (global_wrapped or set())
    
    findings: list[ToolFinding] = []
    for name, line, framework in tools:
        category, delta = _guess_category(name)
        is_wrapped = name in wrapped
        
        findings.append(ToolFinding(
            name=name,
            file=filepath,
            line=line,
            framework=framework,
            category=category,
            is_wrapped=is_wrapped,
            risk_delta=delta,
        ))
    
    return findings


def _collect_all_wrappers(
    pyfiles: list[Path],
    ast_cache: dict[Path, ast.AST] | None = None,
) -> set[str]:
    """Collect all ShadowAuditTool-wrapped class names across multiple files.
    
    First pass: parse every file and extract wrapper targets.
    Returns the union of all wrapped tool names.
    """
    all_wrapped: set[str] = set()
    for pyfile in pyfiles:
        tree = _parse_file_cached(pyfile, ast_cache)
        if tree is None:
            continue
        all_wrapped |= _find_shadowaudit_wrappers(tree)
    return all_wrapped


def _parse_file_cached(pyfile: Path, ast_cache: dict[Path, ast.AST] | None = None) -> ast.AST | None:
    """Parse a Python file, using cache if provided."""
    if ast_cache is not None and pyfile in ast_cache:
        return ast_cache[pyfile]
    try:
        source = pyfile.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(pyfile))
    except (SyntaxError, UnicodeDecodeError, PermissionError):
        return None
    if ast_cache is not None:
        ast_cache[pyfile] = tree
    return tree


def scan_directory(
    path: Path,
    *,
    pattern: str = "*.py",
    exclude_dirs: set[str] | None = None,
) -> list[ToolFinding]:
    """Recursively scan a directory for ungated AI agent tools.
    
    Uses a two-pass approach for cross-file wrapper detection:
    1. First pass: collect all ShadowAuditTool-wrapped class names
    2. Second pass: scan each file with the global wrapped set
    
    Args:
        path: Directory or file to scan
        pattern: Glob pattern for Python files (default: "*.py")
        exclude_dirs: Directory names to skip (default: {venv, .venv, .git, __pycache__, node_modules})
        
    Returns:
        List of ToolFinding objects for all discovered tools
    """
    if exclude_dirs is None:
        exclude_dirs = {"venv", ".venv", ".git", "__pycache__", "node_modules", ".pytest_cache", ".ruff_cache", "dist", "build"}
    
    findings: list[ToolFinding] = []
    
    if path.is_file() and path.suffix == ".py":
        findings.extend(scan_file(path))
    elif path.is_dir():
        # Collect all Python files first
        pyfiles: list[Path] = []
        for pyfile in path.rglob(pattern):
            if any(str(part) in exclude_dirs for part in pyfile.parts):
                continue
            pyfiles.append(pyfile)
        
        # Shared AST cache to avoid double-parsing
        ast_cache: dict[Path, ast.AST] = {}
        
        # Pass 1: collect all wrapped tool names across all files
        global_wrapped = _collect_all_wrappers(pyfiles, ast_cache=ast_cache)
        
        # Pass 2: scan each file with the global wrapped set (reuse cached ASTs)
        for pyfile in pyfiles:
            tree = _parse_file_cached(pyfile, ast_cache)
            if tree is not None:
                findings.extend(scan_file(pyfile, global_wrapped=global_wrapped, _cached_tree=tree))
    
    return findings


def compute_aggregate_score(findings: list[ToolFinding]) -> tuple[int, str]:
    """Compute aggregate risk score from findings.
    
    Returns (score_out_of_100, risk_label).
    """
    if not findings:
        return 0, "SAFE"
    
    total = len(findings)
    ungated = sum(1 for f in findings if not f.is_wrapped)
    high_risk = sum(1 for f in findings if not f.is_wrapped and f.risk_delta <= 0.2)
    
    # Score: base from ungated ratio, weighted heavily by high-risk ungated
    base_score = int((ungated / total) * 50)
    high_risk_bonus = min(high_risk * 10, 40)
    score = base_score + high_risk_bonus
    
    if score >= 70:
        return score, "HIGH"
    elif score >= 40:
        return score, "MEDIUM"
    elif score > 0:
        return score, "LOW"
    return 0, "SAFE"



