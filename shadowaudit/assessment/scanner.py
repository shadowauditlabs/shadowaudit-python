"""Assessment scanner — orchestrates static analysis into enriched findings.

Transforms raw AST tool discoveries into structured assessment data
with taxonomy enrichment, risk scoring, and coverage metrics.

Usage:
    from shadowaudit.assessment.scanner import scan_assessment
    from pathlib import Path
    data = scan_assessment(Path("./src"), taxonomy_path="financial")
    print(data.risk_score)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shadowaudit.check import scan_directory, scan_file, ToolFinding
from shadowaudit.core.taxonomy import TaxonomyLoader


def _compute_risk_metrics(tools: list[ToolAssessment]) -> tuple[int, str]:
    """Compute aggregate risk score from enriched tool assessments.

    Pure function: same inputs always produce same outputs.
    """
    if not tools:
        return 0, "SAFE"

    total = len(tools)
    ungated = sum(1 for t in tools if not t.is_wrapped)
    high_risk = sum(
        1 for t in tools if not t.is_wrapped and t.risk_delta <= 0.2
    )

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


@dataclass(frozen=True)
class ToolAssessment:
    """Enriched assessment of a single tool."""
    # From ToolFinding
    name: str
    file: Path
    line: int
    framework: str | None
    category: str | None
    is_wrapped: bool
    risk_delta: float
    
    # Enriched
    taxonomy_description: str = ""
    risk_keywords: list[str] = field(default_factory=list)
    remediation: str = ""
    
    @property
    def risk_level(self) -> str:
        """Return human-readable risk level."""
        if self.risk_delta <= 0.2:
            return "CRITICAL"
        elif self.risk_delta <= 0.4:
            return "HIGH"
        elif self.risk_delta < 1.0:
            return "MEDIUM"
        return "LOW"
    
    @property
    def needs_action(self) -> bool:
        """Whether this tool requires remediation."""
        return not self.is_wrapped and self.risk_delta < 1.0
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize for template rendering."""
        return {
            "name": self.name,
            "file": str(self.file),
            "line": self.line,
            "framework": self.framework or "unknown",
            "category": self.category or "unknown",
            "is_wrapped": self.is_wrapped,
            "risk_delta": self.risk_delta,
            "risk_level": self.risk_level,
            "taxonomy_description": self.taxonomy_description,
            "risk_keywords": self.risk_keywords,
            "remediation": self.remediation,
            "needs_action": self.needs_action,
        }


@dataclass
class AssessmentData:
    """Complete assessment result for a codebase."""
    # Scan metadata
    path: Path
    taxonomy_name: str | None
    total_files: int = 0
    
    # Tool findings
    tools: list[ToolAssessment] = field(default_factory=list)
    
    # Computed metrics (computed in __post_init__)
    risk_score: int = 0
    risk_label: str = "SAFE"
    total_tools: int = 0
    gated_count: int = 0
    ungated_count: int = 0
    critical_ungated: int = 0
    high_ungated: int = 0
    medium_ungated: int = 0
    low_ungated: int = 0
    safe_tools: int = 0
    
    # Coverage
    coverage_percent: float = 0.0
    
    # Categories summary
    categories: dict[str, dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Compute derived metrics after construction."""
        self.total_tools = len(self.tools)
        self.gated_count = sum(1 for t in self.tools if t.is_wrapped)
        self.ungated_count = self.total_tools - self.gated_count
        
        # Count by risk level among ungated
        self.critical_ungated = sum(1 for t in self.tools if t.needs_action and t.risk_level == "CRITICAL")
        self.high_ungated = sum(1 for t in self.tools if t.needs_action and t.risk_level == "HIGH")
        self.medium_ungated = sum(1 for t in self.tools if t.needs_action and t.risk_level == "MEDIUM")
        self.low_ungated = sum(1 for t in self.tools if t.needs_action and t.risk_level == "LOW")
        self.safe_tools = sum(1 for t in self.tools if t.risk_level == "LOW")
        
        # Coverage: gated tools / total risky tools (excluding LOW/safe)
        risky = [t for t in self.tools if t.risk_level != "LOW"]
        gated_risky = sum(1 for t in risky if t.is_wrapped)
        self.coverage_percent = (gated_risky / len(risky) * 100) if risky else 100.0
        
        # Risk score using pure function over enriched assessments
        self.risk_score, self.risk_label = _compute_risk_metrics(self.tools)
        
        # Category summary
        cat_counts: dict[str, dict[str, Any]] = {}
        for t in self.tools:
            cat = t.category or "unknown"
            if cat not in cat_counts:
                cat_counts[cat] = {"count": 0, "gated": 0, "ungated": 0, 
                                      "critical": 0, "high": 0, "delta": t.risk_delta}
            cat_counts[cat]["count"] += 1
            if t.is_wrapped:
                cat_counts[cat]["gated"] += 1
            else:
                cat_counts[cat]["ungated"] += 1
                if t.risk_level == "CRITICAL":
                    cat_counts[cat]["critical"] += 1
                elif t.risk_level == "HIGH":
                    cat_counts[cat]["high"] += 1
        self.categories = cat_counts
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize for template rendering."""
        return {
            "path": str(self.path),
            "path_name": self.path.name if self.path.is_file() else self.path.name + "/",
            "taxonomy_name": self.taxonomy_name or "default",
            "total_files": self.total_files,
            "risk_score": self.risk_score,
            "risk_label": self.risk_label,
            "total_tools": self.total_tools,
            "gated_count": self.gated_count,
            "ungated_count": self.ungated_count,
            "critical_ungated": self.critical_ungated,
            "high_ungated": self.high_ungated,
            "medium_ungated": self.medium_ungated,
            "low_ungated": self.low_ungated,
            "safe_tools": self.safe_tools,
            "coverage_percent": round(self.coverage_percent, 1),
            "tools": [t.to_dict() for t in self.tools],
            "categories": self.categories,
            "recommended_taxonomy": self._generate_recommended_taxonomy(),
            "implementation_plan": self._generate_implementation_plan(),
        }

    def _generate_recommended_taxonomy(self) -> dict[str, Any]:
        """Auto-generate taxonomy JSON for detected categories."""
        categories: dict[str, dict[str, Any]] = {}
        for tool in self.tools:
            cat = tool.category or "unknown"
            if cat == "unknown":
                continue
            if cat not in categories:
                categories[cat] = {
                    "delta": tool.risk_delta,
                    "risk_keywords": list(tool.risk_keywords) if tool.risk_keywords else [],
                    "description": tool.taxonomy_description or f"Auto-detected: {cat}",
                }
            else:
                for kw in tool.risk_keywords:
                    if kw not in categories[cat]["risk_keywords"]:
                        categories[cat]["risk_keywords"].append(kw)
        return categories

    def _generate_implementation_plan(self) -> list[dict[str, Any]]:
        """Generate step-by-step implementation plan for ungated tools."""
        steps: list[dict[str, Any]] = []
        step_num = 1
        for tool in self.tools:
            if tool.needs_action:
                steps.append({
                    "step": step_num,
                    "tool_name": tool.name,
                    "category": tool.category or "unknown",
                    "risk_level": tool.risk_level,
                    "code": (
                        f"from shadowaudit.framework.langchain import ShadowAuditTool\n"
                        f"{tool.name.lower()}_safe = ShadowAuditTool(\n"
                        f"    tool={tool.name}(),\n"
                        f'    agent_id="YOUR_AGENT_ID",\n'
                        f'    risk_category="{tool.category or "unknown"}"\n'
                        f")"
                    ),
                })
                step_num += 1
        return steps


def _count_py_files(path: Path) -> int:
    """Count Python files in a directory (recursively)."""
    if path.is_file() and path.suffix == ".py":
        return 1
    if path.is_dir():
        return sum(1 for f in path.rglob("*.py") if f.is_file())
    return 0


def enrich_finding(
    finding: ToolFinding,
    taxonomy_path: str | None,
) -> ToolAssessment:
    """Enrich a raw ToolFinding with taxonomy data.

    Public function — used by both scan_assessment and CLI check --output path.
    """
    description = ""
    keywords: list[str] = []
    
    if taxonomy_path and finding.category:
        try:
            config = TaxonomyLoader.lookup(finding.category, taxonomy_path=taxonomy_path)
            description = config.get("description", "")
            keywords = config.get("risk_keywords", [])
        except (KeyError, ValueError, FileNotFoundError):
            pass
    
    # Generate remediation text
    if finding.is_wrapped:
        remediation = "Protected by ShadowAuditTool"
    else:
        remediation = (
            f"Wrap with ShadowAuditTool: "
            f'ShadowAuditTool(tool={finding.name}(), agent_id="YOUR_AGENT_ID", '
            f'risk_category="{finding.category or "unknown"}")'
        )
    
    return ToolAssessment(
        name=finding.name,
        file=finding.file,
        line=finding.line,
        framework=finding.framework,
        category=finding.category,
        is_wrapped=finding.is_wrapped,
        risk_delta=finding.risk_delta,
        taxonomy_description=description,
        risk_keywords=keywords,
        remediation=remediation,
    )


def scan_assessment(
    path: Path,
    *,
    taxonomy_path: str | None = None,
    framework: str | None = None,
) -> AssessmentData:
    """Perform a complete assessment scan of a codebase.
    
    Args:
        path: Directory or Python file to scan
        taxonomy_path: Optional taxonomy name (e.g., "financial") or full path
        framework: Optional filter ("langchain", "crewai", "autogen")
        
    Returns:
        AssessmentData with enriched findings, metrics, and coverage
    """
    # Load taxonomy if specified
    taxonomy_name: str | None = None
    
    if taxonomy_path:
        try:
            TaxonomyLoader.load(taxonomy_path)
            taxonomy_name = taxonomy_path
        except (FileNotFoundError, ValueError, OSError):
            taxonomy_name = None
    
    # Perform raw scan
    if path.is_file():
        raw_findings = scan_file(path)
        total_files = 1
    else:
        raw_findings = scan_directory(path)
        total_files = _count_py_files(path)
    
    # Filter by framework
    if framework:
        fw_lower = framework.lower()
        raw_findings = [f for f in raw_findings 
                        if f.framework and f.framework.lower() == fw_lower]
    
    # Enrich with taxonomy data
    tools = [enrich_finding(f, taxonomy_name) for f in raw_findings]
    
    return AssessmentData(
        path=path,
        taxonomy_name=taxonomy_name,
        total_files=total_files,
        tools=tools,
    )
