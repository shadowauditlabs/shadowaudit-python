"""Tests for pluggable scorer interface."""

import pytest

from capfence.core.scorer import (
    BaseScorer,
    KeywordScorer,
    AdaptiveScorer,
    load_scorer,
)
from capfence.core.state import AgentStateStore


class TestKeywordScorer:
    def test_empty_keywords(self):
        s = KeywordScorer()
        assert s.score({"action": "delete"}, []) == 0.0

    def test_single_match(self):
        s = KeywordScorer()
        score = s.score({"action": "delete record"}, ["delete", "drop"])
        assert score > 0.0
        assert score <= 1.0

    def test_no_match_zero(self):
        s = KeywordScorer()
        assert s.score({"action": "view"}, ["delete", "drop"]) == 0.0

    def test_multiple_matches_capped(self):
        s = KeywordScorer()
        score = s.score({"action": "delete drop remove purge destroy"}, ["delete", "drop", "remove"])
        assert score <= 1.0
        assert score > 0.5

    def test_case_insensitive(self):
        s = KeywordScorer()
        low = s.score({"action": "DELETE"}, ["delete"])
        assert low > 0.0


class TestAdaptiveScorer:
    def test_fallback_to_keyword_without_state(self):
        s = AdaptiveScorer(state_store=None)
        score = s.score({"action": "delete"}, ["delete"])
        assert score > 0.0

    def test_state_weighting(self):
        store = AgentStateStore()
        store.record_decision("__adaptive__", True)
        store.record_decision("__adaptive__", True)
        s = AdaptiveScorer(state_store=store)
        base = KeywordScorer().score({"action": "delete"}, ["delete"])
        adaptive = s.score({"action": "delete"}, ["delete"])
        assert adaptive >= base
        assert adaptive <= 1.0

    def test_degraded_no_crash(self):
        s = AdaptiveScorer(state_store="invalid")
        score = s.score({"action": "delete"}, ["delete"])
        assert score > 0.0


class TestLoadScorer:
    def test_loads_hardened_by_default(self):
        s = load_scorer(prefer_native=False)
        from capfence.core.scorer import RegexASTScorer
        assert isinstance(s, RegexASTScorer)

    def test_loads_keyword_when_hardened_disabled(self):
        s = load_scorer(prefer_native=False, use_hardened=False)
        assert isinstance(s, KeywordScorer)

    def test_loads_adaptive_with_state(self):
        store = AgentStateStore()
        s = load_scorer(state_store=store, prefer_native=False)
        assert isinstance(s, AdaptiveScorer)

    def test_abstract_base_not_instantiable(self):
        with pytest.raises(TypeError):
            BaseScorer()

    def test_enterprise_binary_not_present(self):
        s = load_scorer(prefer_native=True, state_store=None)
        from capfence.core.scorer import RegexASTScorer
        assert isinstance(s, RegexASTScorer)
