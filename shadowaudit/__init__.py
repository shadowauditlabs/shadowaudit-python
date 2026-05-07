"""SHADOWAUDIT — Runtime governance for AI agents.

MIT licensed. Works offline. Rule-based gating with pluggable scoring.
"""

__version__ = "0.3.2"

from shadowaudit.core.gate import Gate
from shadowaudit.types import GateResult
from shadowaudit.core.fsm import FSMOutcome, FailClosedFSM
from shadowaudit.core.state import AgentStateStore
from shadowaudit.core.taxonomy import TaxonomyLoader, stripe_mapper
from shadowaudit.core.hash import compute_payload_hash
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.scorer import BaseScorer, KeywordScorer, AdaptiveScorer, load_scorer
from shadowaudit.cloud.client import CloudClient
from shadowaudit.check import scan_directory, scan_file, ToolFinding
from shadowaudit.assessment.scanner import scan_assessment, AssessmentData, ToolAssessment
from shadowaudit.assessment.reporter import generate_html_report
from shadowaudit.assessment.simulator import TraceSimulator
from shadowaudit.assessment.builder import TaxonomyBuilder
from shadowaudit.framework.crewai import ShadowAuditCrewAITool

__all__ = [
    "Gate",
    "GateResult",
    "FSMOutcome",
    "FailClosedFSM",
    "AgentStateStore",
    "TaxonomyLoader",
    "stripe_mapper",
    "compute_payload_hash",
    "AuditLogger",
    "BaseScorer",
    "KeywordScorer",
    "AdaptiveScorer",
    "load_scorer",
    "CloudClient",
    "scan_directory",
    "scan_file",
    "ToolFinding",
    "scan_assessment",
    "AssessmentData",
    "ToolAssessment",
    "generate_html_report",
    "TraceSimulator",
    "TaxonomyBuilder",
    "ShadowAuditCrewAITool",
]

