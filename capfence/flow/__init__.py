"""Multi-agent flow tracing for cross-agent trust boundary analysis.

Tracks data flows between agents and annotates payloads with trust labels
so CapFence can evaluate cross-agent tool calls at the right trust level.
"""

from capfence.flow.tracer import FlowTracer, FlowEdge, TrustLevel

__all__ = ["FlowTracer", "FlowEdge", "TrustLevel"]
