"""Multi-agent flow tracer for cross-agent trust boundary analysis.

In multi-agent systems, Agent A's output often becomes Agent B's tool call
input. If Agent A processed untrusted external content (user-supplied text,
web scraping, API responses from third parties), that untrusted data can
"flow" into Agent B's high-privilege actions without anyone noticing.

FlowTracer solves this by:

1. Recording each data flow (agent_id, output, destination_agent) with a
   trust label.
2. Propagating trust downward: if Agent A is UNTRUSTED, any output it
   produces that reaches Agent B is tagged UNTRUSTED, regardless of
   Agent B's own trust level.
3. Exposing the trust annotation to ShadowAudit's Gate so the gate can
   apply a stricter threshold for payloads that originated from untrusted
   agents.

Usage::

    tracer = FlowTracer()

    # Agent A reads from an external API (untrusted source)
    tracer.record_output(
        source_agent="agent-web-scraper",
        data={"page_content": "<html>..."},
        trust=TrustLevel.UNTRUSTED,
    )

    # Agent B receives Agent A's output as its tool payload
    payload = {"action": "summarise", "content": data["page_content"]}
    trust_annotation = tracer.annotate(
        receiving_agent="agent-summariser",
        source_agents=["agent-web-scraper"],
    )

    # Optionally surface the effective trust level to downstream consumers
    print(trust_annotation.effective_trust)  # TrustLevel.UNTRUSTED
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from shadowaudit.core.hash import compute_payload_hash


class TrustLevel(IntEnum):
    """Trust levels for agent outputs and data flows.

    Lower values are less trusted. Trust propagates downward:
    a flow from UNTRUSTED always produces an UNTRUSTED annotation
    regardless of the receiving agent's declared trust level.
    """
    SYSTEM = 3    # internal system agent under operator control
    INTERNAL = 2  # internal agent, limited scope
    EXTERNAL = 1  # agent that processed external data (API, file, web)
    UNTRUSTED = 0 # agent that processed user-supplied or third-party content


@dataclass
class FlowEdge:
    """A single data flow from a source agent to a destination agent."""
    edge_id: str
    source_agent: str
    destination_agent: str | None  # None = broadcast / no specific destination
    data_hash: str                  # SHA-256 of the data (not stored raw)
    trust: TrustLevel
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrustAnnotation:
    """Trust annotation for a payload about to be used in a tool call."""
    payload_agent: str
    source_agents: list[str]
    declared_trust: TrustLevel       # trust level of the receiving agent
    effective_trust: TrustLevel      # after propagation from source agents
    contaminated_by: list[str]       # source agents that degraded trust
    flow_edge_ids: list[str]         # edges that contributed to this payload


# Default cap on stored edges — prevents unbounded growth in long-running processes.
_DEFAULT_MAX_EDGES = 10_000


class FlowTracer:
    """Records and analyses data flows between agents in a multi-agent system.

    Not thread-safe — use one instance per thread or add external locking.

    Example — detect that a payment payload originated from untrusted content::

        tracer = FlowTracer()

        # Step 1: Scraper agent reads external page (untrusted)
        tracer.record_output(
            source_agent="scraper",
            data={"url": "https://example.com", "content": page_html},
            trust=TrustLevel.UNTRUSTED,
        )

        # Step 2: Parser agent extracts structured data from scraped content
        tracer.record_flow(
            source_agent="scraper",
            destination_agent="parser",
            data=parsed_data,
        )

        # Step 3: Check effective trust before a payment tool call
        annotation = tracer.annotate(
            receiving_agent="payment-agent",
            source_agents=["parser"],
        )

        print(annotation.effective_trust)  # TrustLevel.UNTRUSTED
        print(annotation.contaminated_by)  # ['scraper']
    """

    def __init__(self, max_edges: int = _DEFAULT_MAX_EDGES) -> None:
        self._edges: list[FlowEdge] = []
        self._max_edges = max_edges
        # agent_id → minimum trust level seen in its outputs
        self._agent_min_trust: dict[str, TrustLevel] = {}
        # Reverse index: agent_id → list of edge_ids produced by that agent (O(1) lookup)
        self._edges_by_agent: dict[str, list[str]] = {}

    @staticmethod
    def _make_edge_id(data: Any) -> str:
        # time.time_ns() ensures sub-microsecond uniqueness within the same process
        unique = {"data": str(data), "t_ns": time.time_ns()}
        return compute_payload_hash(unique)[:16]

    def _register_edge(self, edge: FlowEdge) -> None:
        """Append edge, update reverse index, and evict oldest if over cap."""
        if len(self._edges) >= self._max_edges:
            evicted = self._edges.pop(0)
            agent_edges = self._edges_by_agent.get(evicted.source_agent)
            if agent_edges and evicted.edge_id in agent_edges:
                agent_edges.remove(evicted.edge_id)
        self._edges.append(edge)
        self._edges_by_agent.setdefault(edge.source_agent, []).append(edge.edge_id)

    def _create_edge(
        self,
        source_agent: str,
        destination_agent: str | None,
        data: Any,
        trust: TrustLevel,
        metadata: dict[str, Any] | None,
    ) -> FlowEdge:
        return FlowEdge(
            edge_id=self._make_edge_id({"src": source_agent, "dst": destination_agent, "data": data}),
            source_agent=source_agent,
            destination_agent=destination_agent,
            data_hash=compute_payload_hash({"data": data}),
            trust=trust,
            timestamp=time.time(),
            metadata=metadata or {},
        )

    def record_output(
        self,
        source_agent: str,
        data: Any,
        trust: TrustLevel,
        metadata: dict[str, Any] | None = None,
    ) -> FlowEdge:
        """Record that source_agent produced data at the given trust level.

        Call this whenever an agent produces output that will feed into
        another agent or tool call.

        Args:
            source_agent: ID of the agent producing the data.
            data: The data produced (stored as a hash, not raw).
            trust: Trust level to assign to this output.
            metadata: Optional metadata (e.g., tool name, task context).

        Returns:
            The recorded FlowEdge.
        """
        edge = self._create_edge(source_agent, None, data, trust, metadata)
        self._register_edge(edge)
        current_min = self._agent_min_trust.get(source_agent, trust)
        self._agent_min_trust[source_agent] = min(current_min, trust)
        return edge

    def record_flow(
        self,
        source_agent: str,
        destination_agent: str,
        data: Any,
        trust: TrustLevel | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FlowEdge:
        """Record a data flow from source_agent to destination_agent.

        If trust is not specified, inherits the minimum trust level seen
        from source_agent's prior outputs.

        Args:
            source_agent: Agent that produced the data.
            destination_agent: Agent that will receive and process the data.
            data: The data being passed (stored as hash).
            trust: Trust level override. If None, uses source agent's min trust.
            metadata: Optional metadata.
        """
        resolved_trust = trust if trust is not None else self._agent_min_trust.get(
            source_agent, TrustLevel.INTERNAL
        )
        edge = self._create_edge(source_agent, destination_agent, data, resolved_trust, metadata)
        self._register_edge(edge)
        current_min = self._agent_min_trust.get(destination_agent, resolved_trust)
        self._agent_min_trust[destination_agent] = min(current_min, resolved_trust)
        return edge

    def annotate(
        self,
        receiving_agent: str,
        source_agents: list[str],
        declared_trust: TrustLevel = TrustLevel.INTERNAL,
    ) -> TrustAnnotation:
        """Compute the effective trust annotation for an agent's tool call.

        Checks whether any of the source_agents have produced UNTRUSTED or
        EXTERNAL outputs, and propagates the lowest trust level to the annotation.

        Args:
            receiving_agent: Agent making the tool call.
            source_agents: Agents whose outputs contributed to this payload.
            declared_trust: The nominal trust of the receiving agent.

        Returns:
            TrustAnnotation with effective_trust and contaminated_by fields.
        """
        effective = declared_trust
        contaminated_by: list[str] = []
        contributing_edges: list[str] = []

        for agent_id in source_agents:
            agent_trust = self._agent_min_trust.get(agent_id, declared_trust)
            if agent_trust < effective:
                effective = agent_trust
                contaminated_by.append(agent_id)
            # O(1) lookup via reverse index instead of scanning all edges
            contributing_edges.extend(self._edges_by_agent.get(agent_id, []))

        # Also consider the receiving agent's own trust history
        receiver_trust = self._agent_min_trust.get(receiving_agent, declared_trust)
        if receiver_trust < effective:
            effective = receiver_trust
            if receiving_agent not in contaminated_by:
                contaminated_by.append(receiving_agent)

        return TrustAnnotation(
            payload_agent=receiving_agent,
            source_agents=source_agents,
            declared_trust=declared_trust,
            effective_trust=effective,
            contaminated_by=contaminated_by,
            flow_edge_ids=list(set(contributing_edges)),
        )

    def get_agent_trust(self, agent_id: str) -> TrustLevel:
        """Return the current minimum trust level for an agent."""
        return self._agent_min_trust.get(agent_id, TrustLevel.INTERNAL)

    def flow_summary(self) -> dict[str, Any]:
        """Return a summary of all recorded flows for reporting."""
        agents = set()
        for e in self._edges:
            agents.add(e.source_agent)
            if e.destination_agent:
                agents.add(e.destination_agent)

        trust_distribution: dict[str, int] = {t.name: 0 for t in TrustLevel}
        for e in self._edges:
            trust_distribution[e.trust.name] += 1

        contaminated_agents = [
            a for a, t in self._agent_min_trust.items()
            if t < TrustLevel.INTERNAL
        ]

        return {
            "total_flows": len(self._edges),
            "agents": sorted(agents),
            "trust_distribution": trust_distribution,
            "contaminated_agents": contaminated_agents,
            "agent_trust_levels": {
                a: t.name for a, t in self._agent_min_trust.items()
            },
        }

    def reset(self) -> None:
        """Clear all recorded flows. Useful between test scenarios."""
        self._edges.clear()
        self._agent_min_trust.clear()
        self._edges_by_agent.clear()
