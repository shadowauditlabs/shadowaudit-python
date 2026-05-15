"""Tests for built-in taxonomy starter packs."""


from capfence.core.taxonomy import TaxonomyLoader


class TestGeneralTaxonomy:
    def test_load_general(self):
        data = TaxonomyLoader.load("general")
        assert data["domain"] == "general"
        assert "categories" in data
        assert "read_only" in data["categories"]
        assert "execute" in data["categories"]

    def test_general_read_only_delta(self):
        data = TaxonomyLoader.load("general")
        assert data["categories"]["read_only"]["delta"] == 1.0

    def test_general_execute_risky(self):
        data = TaxonomyLoader.load("general")
        assert data["categories"]["execute"]["delta"] < 0.2


class TestFinancialTaxonomy:
    def test_load_financial(self):
        data = TaxonomyLoader.load("financial")
        assert data["domain"] == "financial"
        assert "payment_initiation" in data["categories"]

    def test_payment_low_delta(self):
        data = TaxonomyLoader.load("financial")
        assert data["categories"]["payment_initiation"]["delta"] == 0.3

    def test_withdrawal_keywords(self):
        data = TaxonomyLoader.load("financial")
        kw = data["categories"]["withdrawal"]["risk_keywords"]
        assert "withdraw" in kw
        assert "drain" in kw


class TestLegalTaxonomy:
    def test_load_legal(self):
        data = TaxonomyLoader.load("legal")
        assert data["domain"] == "legal"
        assert "privilege_waiver" in data["categories"]

    def test_privilege_waiver_very_low_delta(self):
        data = TaxonomyLoader.load("legal")
        assert data["categories"]["privilege_waiver"]["delta"] == 0.1

    def test_regulatory_filing(self):
        data = TaxonomyLoader.load("legal")
        entry = data["categories"]["regulatory_filing"]
        assert "sec" in entry["risk_keywords"]
        assert entry["delta"] == 0.2


class TestLookupIntegration:
    def test_lookup_known_category(self):
        TaxonomyLoader.reset_cache()
        entry = TaxonomyLoader.lookup("payment_initiation", taxonomy_path="financial")
        assert entry["delta"] == 0.3

    def test_lookup_unknown_returns_default(self):
        TaxonomyLoader.reset_cache()
        entry = TaxonomyLoader.lookup("nonexistent", taxonomy_path="general")
        assert entry["delta"] == 0.1  # default
        assert entry["risk_keywords"] == []
