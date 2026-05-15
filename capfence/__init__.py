"""CAPFENCE — Runtime governance for AI agents.

MIT licensed. Works offline. Rule-based gating with pluggable scoring.
"""

__version__ = "0.7.0"

from capfence.core.gate import Gate
from capfence.types import GateResult
from capfence.errors import (
    CapFenceError,
    AgentActionBlocked,
    ConfigurationError,
    PolicyLoadError,
    AuditError,
    TaxonomyError,
    GatewayError,
)
from capfence.core.fsm import FSMOutcome, FailClosedFSM
from capfence.core.state import AgentStateStore
from capfence.core.taxonomy import TaxonomyLoader, stripe_mapper
from capfence.core.hash import compute_payload_hash
from capfence.core.audit import AuditLogger
from capfence.core.chain import verify_chain, verify_chain_from_rows, ChainEntry
from capfence.core.keys import generate_keypair, load_keypair, ensure_keypair, sign_entry, verify_entry
from capfence.core.scorer import BaseScorer, KeywordScorer, RegexASTScorer, AdaptiveScorer, load_scorer
from capfence.cloud.client import CloudClient
from capfence.check import scan_directory, scan_file, ToolFinding
from capfence.assessment.scanner import scan_assessment, AssessmentData, ToolAssessment
from capfence.assessment.reporter import generate_html_report
from capfence.assessment.simulator import TraceSimulator
from capfence.assessment.builder import TaxonomyBuilder
from capfence.assessment.owasp import get_coverage_matrix, get_coverage_summary, generate_owasp_context
from capfence.assessment.eu_ai_act import generate_evidence_pack, EvidencePack
from capfence.framework.langchain import CapFenceTool
from capfence.framework.crewai import CapFenceCrewAITool
from capfence.framework.langgraph import CapFenceToolNode
from capfence.framework.openai_agents import CapFenceOpenAITool
from capfence.framework.pydanticai import CapFencePydanticTool
from capfence.framework.llamaindex import CapFenceLlamaIndexTool
from capfence.framework.autogen import CapFenceAutoGenTool
from capfence.mcp.gateway import MCPGatewayServer
from capfence.mcp.adapter import CapFenceMCPSession
from capfence.telemetry.client import TelemetryClient
from capfence.flow.tracer import FlowTracer, FlowEdge, TrustLevel
from capfence.core.gate import GATE_MODE_ENFORCE, GATE_MODE_OBSERVE

__all__ = [
    "__version__",
    "Gate",
    "GateResult",
    "CapFenceError",
    "AgentActionBlocked",
    "ConfigurationError",
    "PolicyLoadError",
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
    "CapFenceTool",
    "CapFenceCrewAITool",
    "CapFenceToolNode",
    "CapFenceOpenAITool",
    "CapFencePydanticTool",
    "CapFenceLlamaIndexTool",
    "CapFenceAutoGenTool",
    "MCPGatewayServer",
    "CapFenceMCPSession",
    "TelemetryClient",
    "FlowTracer",
    "FlowEdge",
    "TrustLevel",
    "GATE_MODE_ENFORCE",
    "GATE_MODE_OBSERVE",
]
