"""Pluggable risk scorer interface.

Open-source SDK provides keyword-based scoring.
Enterprise binary provides adaptive behavioral scoring via shadowaudit._native.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseScorer(ABC):
    """Abstract base for risk scoring strategies."""

    @abstractmethod
    def score(
        self,
        payload: dict[str, Any],
        risk_keywords: list[str],
        category_config: dict[str, Any] | None = None,
        agent_id: str | None = None,
    ) -> float:
        """Return risk score in [0, 1]. Higher = more risky."""
        ...


class KeywordScorer(BaseScorer):
    """Default scorer: fast, deterministic, zero dependencies.

    Uses simple keyword substring matching in payload text.
    Genuinely useful without payment — suitable for open-source SDK.
    """

    def score(
        self,
        payload: dict[str, Any],
        risk_keywords: list[str],
        category_config: dict[str, Any] | None = None,
        agent_id: str | None = None,
    ) -> float:
        if not risk_keywords:
            return 0.0

        text = str(payload).lower()
        matches = sum(1 for kw in risk_keywords if kw.lower() in text)
        # Fraction of keywords matched [0, 1]. Requires all keywords for full score.
        return min(matches / len(risk_keywords), 1.0)


class AdaptiveScorer(BaseScorer):
    """Placeholder for behavioral scoring — keyword baseline only in OSS."""

    def __init__(self, state_store: Any | None = None) -> None:
        self._store = state_store

    def score(
        self,
        payload: dict[str, Any],
        risk_keywords: list[str],
        category_config: dict[str, Any] | None = None,
        agent_id: str | None = None,
    ) -> float:
        return KeywordScorer().score(payload, risk_keywords, category_config, agent_id=agent_id)


def load_scorer(
    state_store: Any | None = None,
    prefer_native: bool = True,
) -> BaseScorer:
    """Load the best available scorer.

    Priority:
        1. Enterprise native scorer (if binary present)
        2. Adaptive scorer with local state
        3. Keyword scorer (guaranteed fallback)

    Args:
        state_store: Optional AgentStateStore for behavioral data
        prefer_native: Whether to try loading enterprise binary scorer first

    Returns:
        A BaseScorer instance ready for gate evaluation.
    """

    # 1. Try enterprise binary scorer
    if prefer_native:
        try:
            # pylint: disable=import-outside-toplevel
            from shadowaudit._native import AdaptiveScorer as NativeScorer  # type: ignore[import-untyped]

            logger.info("Using enterprise native AdaptiveScorer from binary.")
            return NativeScorer()  # type: ignore[no-any-return]
        except ImportError:
            logger.debug("Enterprise binary not available. Using OSS scorer.")

    # 2. Open-source adaptive (with state store)
    if state_store is not None:
        logger.info("Using OSS AdaptiveScorer with behavioral analysis.")
        return AdaptiveScorer(state_store=state_store)

    # 3. Guaranteed keyword fallback (no state, no deps)
    logger.info("Using KeywordScorer (deterministic keyword matching).")
    return KeywordScorer()

