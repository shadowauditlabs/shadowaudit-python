"""Pluggable risk scorer interface.

Open-source SDK provides keyword-based scoring.
Enterprise binary provides adaptive behavioral scoring via capfence._native.
"""

from __future__ import annotations

import ast
import functools
import logging
import re
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


class RegexASTScorer(BaseScorer):
    """Hardened scorer: regex-aware patterns + AST-aware for Python shell payloads.

    Reduces false positives from KeywordScorer by requiring whole-word or
    structural matches. Detects dangerous Python AST patterns (exec, eval,
    subprocess, os.system) when payload contains code strings.
    """

    # Dangerous AST node types that indicate code execution
    _DANGEROUS_AST_NAMES: set[str] = {
        "exec",
        "eval",
        "compile",
        "__import__",
        "os.system",
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "open",
        "input",
    }

    def __init__(self, keyword_scorer: BaseScorer | None = None) -> None:
        self._fallback = keyword_scorer or KeywordScorer()

    @staticmethod
    @functools.lru_cache(maxsize=128)
    def _compile_patterns_cached(risk_keywords: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
        """Compile whole-word regex patterns from keywords (cached)."""
        patterns: list[re.Pattern[str]] = []
        for kw in risk_keywords:
            # Escape regex metacharacters, then wrap in word boundaries
            escaped = re.escape(kw.lower())
            try:
                patterns.append(re.compile(rf"\b{escaped}\b"))
            except re.error:
                # If the keyword itself is an invalid regex, fall back to literal
                patterns.append(re.compile(re.escape(kw.lower())))
        return tuple(patterns)

    def _compile_patterns(self, risk_keywords: list[str]) -> list[re.Pattern[str]]:
        """Compile whole-word regex patterns from keywords."""
        return list(self._compile_patterns_cached(tuple(risk_keywords)))

    _MAX_AST_PARSE_LENGTH = 4096

    def _ast_risk_score(self, text: str) -> float:
        """Parse text as Python AST and score dangerous constructs."""
        if len(text) > self._MAX_AST_PARSE_LENGTH:
            return 0.0
        try:
            tree = ast.parse(text, mode="exec")
        except SyntaxError:
            return 0.0
        except ValueError:
            return 0.0

        dangerous_nodes = 0
        total_nodes = 0
        for node in ast.walk(tree):
            total_nodes += 1
            if isinstance(node, ast.Call):
                func = node.func
                name: str | None = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    name = f"{func.value.id}.{func.attr}"
                if name and name in self._DANGEROUS_AST_NAMES:
                    dangerous_nodes += 1
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"os", "subprocess", "sys", "pty"}:
                        dangerous_nodes += 1
            elif isinstance(node, ast.ImportFrom):
                if node.module in {"os", "subprocess", "sys", "pty"}:
                    dangerous_nodes += 1

        if total_nodes == 0:
            return 0.0
        # Cap AST contribution at 0.5 so keyword matching still matters
        return min(dangerous_nodes / max(total_nodes, 1), 0.5)

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
        patterns = self._compile_patterns(risk_keywords)
        regex_matches = sum(1 for p in patterns if p.search(text))
        regex_score = min(regex_matches / len(risk_keywords), 1.0)

        # AST scan: only if payload looks like code (contains def/class/import/exec/eval)
        ast_score = 0.0
        if any(trigger in text for trigger in ("def ", "class ", "import ", "exec(", "eval(")):
            ast_score = self._ast_risk_score(str(payload))

        # Combine: regex is primary, AST adds up to 0.5 bonus
        combined = min(regex_score + ast_score, 1.0)
        return combined


class AdaptiveScorer(BaseScorer):
    """Placeholder for behavioral scoring — keyword baseline only in OSS."""

    _scorer_instance: RegexASTScorer | None = None

    def __init__(self, state_store: Any | None = None) -> None:
        self._store = state_store

    def score(
        self,
        payload: dict[str, Any],
        risk_keywords: list[str],
        category_config: dict[str, Any] | None = None,
        agent_id: str | None = None,
    ) -> float:
        if AdaptiveScorer._scorer_instance is None:
            AdaptiveScorer._scorer_instance = RegexASTScorer()
        return AdaptiveScorer._scorer_instance.score(payload, risk_keywords, category_config, agent_id=agent_id)


def load_scorer(
    state_store: Any | None = None,
    prefer_native: bool = True,
    use_hardened: bool = True,
) -> BaseScorer:
    """Load the best available scorer.

    Priority:
        1. Enterprise native scorer (if binary present)
        2. Adaptive scorer with local state (hardened regex+AST)
        3. RegexASTScorer (hardened, no state)
        4. Keyword scorer (guaranteed fallback)

    Args:
        state_store: Optional AgentStateStore for behavioral data
        prefer_native: Whether to try loading enterprise binary scorer first
        use_hardened: Whether to use RegexASTScorer instead of plain KeywordScorer

    Returns:
        A BaseScorer instance ready for gate evaluation.
    """

    # 1. Try enterprise binary scorer
    if prefer_native:
        try:
            # pylint: disable=import-outside-toplevel
            from capfence._native import AdaptiveScorer as NativeScorer  # noqa: PGH003

            logger.info("Using enterprise native AdaptiveScorer from binary.")
            return NativeScorer()  # type: ignore[no-any-return]
        except ImportError:
            logger.debug("Enterprise binary not available. Using OSS scorer.")

    # 2. Open-source adaptive (with state store, hardened)
    if state_store is not None:
        logger.info("Using OSS AdaptiveScorer with behavioral analysis.")
        return AdaptiveScorer(state_store=state_store)

    # 3. Hardened regex+AST scorer (no state)
    if use_hardened:
        logger.info("Using RegexASTScorer (hardened keyword + AST analysis).")
        return RegexASTScorer()

    # 4. Guaranteed keyword fallback (no state, no deps)
    logger.info("Using KeywordScorer (deterministic keyword matching).")
    return KeywordScorer()

