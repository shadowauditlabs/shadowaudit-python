"""SHADOWAUDIT — Runtime governance for AI agents.

MIT licensed. Works offline. Rule-based gating with pluggable scoring.
"""

__version__ = "0.6.0"

from shadowaudit.core.gate import Gate
from shadowaudit.types import GateResult
from shadowaudit.errors import (
    ShadowAuditError,
    AgentActionBlocked,
    ConfigurationError,
    AuditError,
    TaxonomyError,
    GatewayError,
)
from shadowaudit.core.fsm import FSMOutcome, FailClosedFSM
from shadowaudit.core.state import AgentStateStore
from shadowaudit.core.taxonomy import TaxonomyLoader, stripe_mapper
from shadowaudit.core.hash import compute_payload_hash
from shadowaudit.core.audit import AuditLogger
from shadowaudit.core.chain import verify_chain, verify_chain_from_rows, ChainEntry
from shadowaudit.core.keys import generate_keypair, load_keypair, ensure_keypair, sign_entry, verify_entry
from shadowaudit.core.scorer import BaseScorer, KeywordScorer, RegexASTScorer, AdaptiveScorer, load_scorer
from shadowaudit.cloud.client import CloudClient
from shadowaudit.check import scan_directory, scan_file, ToolFinding
from shadowaudit.assessment.scanner import scan_assessment, AssessmentData, ToolAssessment
from shadowaudit.assessment.reporter import generate_html_report
from shadowaudit.assessment.simulator import TraceSimulator
from shadowaudit.assessment.builder import TaxonomyBuilder
from shadowaudit.assessment.owasp import get_coverage_matrix, get_coverage_summary, generate_owasp_context
from shadowaudit.assessment.eu_ai_act import generate_evidence_pack, EvidencePack
from shadowaudit.framework.langchain import ShadowAuditTool
from shadowaudit.framework.crewai import ShadowAuditCrewAITool
from shadowaudit.framework.langgraph import ShadowAuditToolNode
from shadowaudit.framework.openai_agents import ShadowAuditOpenAITool
from shadowaudit.mcp.gateway import MCPGatewayServer
from shadowaudit.mcp.adapter import ShadowAuditMCPSession
from shadowaudit.telemetry.client import TelemetryClient
from shadowaudit.flow.tracer import FlowTracer, FlowEdge, TrustLevel
from shadowaudit.core.gate import GATE_MODE_ENFORCE, GATE_MODE_OBSERVE

__all__ = [
    "__version__",
    "Gate",
    "GateResult",
    "ShadowAuditError",
    "AgentActionBlocked",
    "ConfigurationError",
    "AuditError",
    "TaxonomyError",
    "GatewayError",
    "FSMOutcome",
    "FailClosedFSM",
    "AgentStateStore",
    "TaxonomyLoader",
    "stripe_mapper",
    "compute_payload_hash",
    "AuditLogger",
    "verify_chain",
    "verify_chain_from_rows",
    "ChainEntry",
    "generate_keypair",
    "load_keypair",
    "ensure_keypair",
    "sign_entry",
    "verify_entry",
    "BaseScorer",
    "KeywordScorer",
    "RegexASTScorer",
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
    "get_coverage_matrix",
    "get_coverage_summary",
    "generate_owasp_context",
    "generate_evidence_pack",
    "EvidencePack",
    "ShadowAuditTool",
    "ShadowAuditCrewAITool",
    "ShadowAuditToolNode",
    "ShadowAuditOpenAITool",
    "MCPGatewayServer",
    "ShadowAuditMCPSession",
    "TelemetryClient",
    "FlowTracer",
    "FlowEdge",
    "TrustLevel",
    "GATE_MODE_ENFORCE",
    "GATE_MODE_OBSERVE",
]

