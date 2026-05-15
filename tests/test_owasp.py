"""Tests for OWASP Agentic Top 10 coverage matrix."""

from capfence.assessment.owasp import (
    get_coverage_matrix,
    get_coverage_summary,
    generate_owasp_context,
)


class TestOWASPCoverage:
    def test_matrix_has_10_items(self):
        matrix = get_coverage_matrix()
        assert len(matrix) == 10

    def test_all_items_have_required_fields(self):
        for item in get_coverage_matrix():
            assert item.risk_id
            assert item.risk_name
            assert item.description
            assert item.coverage_level in ("full", "partial", "planned", "not_applicable")
            assert item.capfence_feature

    def test_summary_totals(self):
        summary = get_coverage_summary()
        assert summary["total"] == 10
        assert summary["full"] + summary["partial"] + summary["planned"] + summary["not_applicable"] == 10
        assert 0 <= summary["coverage_percent"] <= 100

    def test_generate_context(self):
        ctx = generate_owasp_context()
        assert "items" in ctx
        assert "summary" in ctx
        assert len(ctx["items"]) == 10
