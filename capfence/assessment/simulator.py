"""Trace simulator — replays agent execution traces through CapFence gate.

Compares static rule-based blocking vs adaptive behavioral scoring
across a JSONL trace of agent tool calls.

Usage:
    from capfence.assessment.simulator import TraceSimulator

    sim = TraceSimulator()
    result = sim.run(trace_file=Path("./agent_trace.jsonl"))
    print(result.adaptive_additional_blocks)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from capfence.core.gate import Gate
from capfence.core.scorer import KeywordScorer, AdaptiveScorer
from capfence.core.state import AgentStateStore

logger = logging.getLogger(__name__)


@dataclass
class TraceReplayResult:
    """Result of replaying a single trace call."""
    call_id: str
    tool_name: str
    risk_category: str | None
    payload: dict[str, Any]
    static_blocked: bool
    static_score: float
    adaptive_blocked: bool
    adaptive_score: float
    adaptive_delta: float | None  # how much the adaptive score differed


@dataclass
class SimulationSummary:
    """Aggregated simulation results."""
    total_calls: int = 0
    static_blocked: int = 0
    adaptive_blocked: int = 0
    adaptive_additional_blocks: int = 0
    static_passed: int = 0
    adaptive_passed: int = 0
    results: list[TraceReplayResult] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    recommendation: str = ""


class TraceSimulator:
    """Replay agent tool call traces through CapFence gate variants.

    Compares static keyword rules against adaptive behavioral scoring
    to surface differences in blocking decisions.
    """

    def __init__(self, taxonomy_path: str | None = "general", taxonomy_paths: list[str] | None = None) -> None:
        self._taxonomy_path = taxonomy_path
        self._taxonomy_paths = taxonomy_paths

    def run(
        self,
        trace_file: Path,
        agent_id: str = "trace-replay",
        verbose: bool = False,
    ) -> SimulationSummary:
        """Replay a JSONL trace file.

        Each line in the trace file is a JSON object:
            {"call_id": "...", "tool_name": "...", "payload": {...}, "risk_category": "..."}
        """

        calls = self._load_trace(trace_file)
        summary = SimulationSummary(total_calls=len(calls))

        # Fresh isolated store per simulation — history never bleeds across runs
        store = AgentStateStore()

        # Two gate instances: static (keyword-only) and adaptive (behavioral)
        static_gate = Gate(
            taxonomy_path=self._taxonomy_path,
            scorer=KeywordScorer(),
        )
        adaptive_gate = Gate(
            taxonomy_path=self._taxonomy_path,
            scorer=AdaptiveScorer(state_store=store),
            state_store=store,
        )

        # Multi-pack gates if requested
        multi_static_gates: list[Gate] = []
        multi_adaptive_gates: list[Gate] = []
        if self._taxonomy_paths:
            for tp in self._taxonomy_paths:
                multi_static_gates.append(Gate(taxonomy_path=tp, scorer=KeywordScorer()))
                multi_adaptive_gates.append(
                    Gate(taxonomy_path=tp, scorer=AdaptiveScorer(state_store=store), state_store=store)
                )

        for call in calls:
            call_id = call.get("call_id", "unknown")
            tool_name = call.get("tool_name", "unknown")
            payload = call.get("payload", {})
            risk_category = call.get("risk_category")
            # Static evaluation
            static_result = static_gate.evaluate(
                agent_id=agent_id,
                task_context=tool_name,
                risk_category=risk_category,
                payload=payload,
            )
            static_blocked = not static_result.passed
            static_score = static_result.risk_score or 0.0

            # Adaptive evaluation
            adaptive_result = adaptive_gate.evaluate(
                agent_id=agent_id,
                task_context=tool_name,
                risk_category=risk_category,
                payload=payload,
            )
            adaptive_blocked = not adaptive_result.passed
            adaptive_score = adaptive_result.risk_score or 0.0
            adaptive_delta = adaptive_score - static_score if adaptive_score > static_score else None

            # Multi-pack evaluation: track if any pack blocks
            if multi_static_gates and multi_adaptive_gates:
                for sg in multi_static_gates:
                    sr = sg.evaluate(agent_id=agent_id, task_context=tool_name, risk_category=risk_category, payload=payload)
                    if not sr.passed:
                        static_blocked = True
                        break
                for ag in multi_adaptive_gates:
                    ar = ag.evaluate(agent_id=agent_id, task_context=tool_name, risk_category=risk_category, payload=payload)
                    if not ar.passed:
                        adaptive_blocked = True
                        break

            result = TraceReplayResult(
                call_id=call_id,
                tool_name=tool_name,
                risk_category=risk_category,
                payload=payload,
                static_blocked=static_blocked,
                static_score=static_score,
                adaptive_blocked=adaptive_blocked,
                adaptive_score=adaptive_score,
                adaptive_delta=adaptive_delta,
            )
            # Attach multi-pack flags as metadata (not in dataclass, so skip for now)
            summary.results.append(result)

            if static_blocked:
                summary.static_blocked += 1
            else:
                summary.static_passed += 1

            if adaptive_blocked:
                summary.adaptive_blocked += 1
                if not static_blocked:
                    summary.adaptive_additional_blocks += 1
            else:
                summary.adaptive_passed += 1

            # Pattern detection: behavioral anomalies the adaptive layer caught
            if adaptive_blocked and not static_blocked:
                # Determine why adaptive blocked it
                if "urgent" in str(payload).lower() or "ceo" in str(payload).lower():
                    summary.patterns.append(
                        f"Social engineering detected in call {call_id} ({tool_name}): "
                        "'urgent'/'CEO' keywords suggest policy circumvention"
                    )
                if "bypass" in str(payload).lower() or "override" in str(payload).lower():
                    summary.patterns.append(
                        f"Override attempt detected in call {call_id} ({tool_name}): "
                        "explicit bypass language in payload"
                    )
                if "offshore" in str(payload).lower():
                    summary.patterns.append(
                        f"Offshore destination flagged in call {call_id} ({tool_name}): "
                        "high-value transfer to external jurisdiction"
                    )
                # Check for tool repetition
                recent_tools = store.get_recent_tools(agent_id, window_seconds=300, limit=10)
                repeat_count = sum(1 for t in recent_tools if t == tool_name)
                if repeat_count >= 3:
                    summary.patterns.append(
                        f"Tool repetition anomaly: '{tool_name}' called {repeat_count}x in recent window at call {call_id}"
                    )
                # Check for amount accumulation
                amount = payload.get("amount") or payload.get("total") or payload.get("value")
                if amount is not None:
                    total_recent = store.get_total_amount(agent_id, window_seconds=300)
                    if total_recent > 100000:
                        summary.patterns.append(
                            f"Cumulative amount spike: ${total_recent:,.0f} in 5min window at call {call_id}"
                        )

            if verbose:
                logger.info(
                    "%s: %s static=%.2f/%s adaptive=%.2f/%s delta=%s",
                    call_id, tool_name,
                    static_score, "BLOCK" if static_blocked else "OK",
                    adaptive_score, "BLOCK" if adaptive_blocked else "OK",
                    f"{adaptive_delta:.2f}" if adaptive_delta else "-",
                )

        # Generate recommendation
        if summary.adaptive_additional_blocks > 0:
            summary.recommendation = (
                f"Adaptive intelligence would have blocked {summary.adaptive_additional_blocks} additional "
                f"call(s) ({summary.adaptive_additional_blocks / summary.total_calls * 100:.1f}%). "
                f"{len(summary.patterns)} behavioral pattern(s) detected that static rules missed. "
                f"Consider CapFence Enterprise for real-time adaptive enforcement."
            )
        else:
            summary.recommendation = "Static rules caught all issues. No adaptive gap detected."

        return summary

    def _load_trace(self, trace_file: Path) -> list[dict[str, Any]]:
        """Load JSONL trace file."""

        calls: list[dict[str, Any]] = []
        with trace_file.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    call = json.loads(line)
                    if "call_id" not in call:
                        call["call_id"] = f"line-{i}"
                    calls.append(call)
                except json.JSONDecodeError:
                    logger.warning("Skipping invalid JSON on line %d: %s", i, line[:80])
        return calls

