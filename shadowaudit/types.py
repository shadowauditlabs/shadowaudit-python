"""Shared dataclasses for SHADOWAUDIT SDK."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GateResult:
    """Result of a gate evaluation."""
    passed: bool
    risk_score: float | None = None
    threshold: float | None = None
    risk_category: str | None = None
    reason: str | None = None
    latency_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)



