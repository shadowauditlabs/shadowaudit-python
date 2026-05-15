"""Tests for Plaid taxonomy pack."""

from capfence.core.taxonomy import TaxonomyLoader


class TestPlaidTaxonomy:
    def test_loads(self):
        config = TaxonomyLoader.load("financial_plaid")
        assert config["domain"] == "financial_plaid"
        assert "plaid_auth" in config["categories"]
        assert "plaid_transfer" in config["categories"]

    def test_plaid_transfer_high_risk(self):
        config = TaxonomyLoader.load("financial_plaid")
        transfer = config["categories"]["plaid_transfer"]
        assert transfer["delta"] == 0.2
        assert "transfer" in transfer["risk_keywords"]

    def test_plaid_balance_low_risk(self):
        config = TaxonomyLoader.load("financial_plaid")
        balance = config["categories"]["plaid_balance"]
        assert balance["delta"] == 1.0
        assert "balance" in balance["risk_keywords"]
