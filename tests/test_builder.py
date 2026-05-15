"""Tests for TaxonomyBuilder."""

from capfence.assessment.builder import TaxonomyBuilder


class TestTaxonomyBuilder:
    def test_build_fintech(self):
        builder = TaxonomyBuilder()
        taxonomy = builder.build(
            industry="fintech",
            payment_methods=["stripe"],
            pii_access=True,
            transfer_initiation=True,
        )

        assert taxonomy["domain"] == "fintech"
        assert "categories" in taxonomy
        assert "stripe_payment_initiation" in taxonomy["categories"]
        assert "compliance_mapping" in taxonomy

    def test_build_retail_no_pii(self):
        builder = TaxonomyBuilder()
        taxonomy = builder.build(
            industry="retail",
            payment_methods=["square"],
            pii_access=False,
        )

        assert "pii_access" not in taxonomy["categories"]
        assert "square_payment" in taxonomy["categories"]

    def test_compliance_pci_dss(self):
        builder = TaxonomyBuilder()
        taxonomy = builder.build(
            industry="retail",
            compliance_required=["PCI-DSS"],
        )

        assert "PCI-DSS" in taxonomy["compliance_mapping"]
        assert "3.4" in taxonomy["compliance_mapping"]["PCI-DSS"]

    def test_compliance_sox(self):
        builder = TaxonomyBuilder()
        taxonomy = builder.build(
            industry="fintech",
            compliance_required=["SOX"],
        )

        assert "SOX" in taxonomy["compliance_mapping"]
        assert "302" in taxonomy["compliance_mapping"]["SOX"]

    def test_custom_payment_method(self):
        builder = TaxonomyBuilder()
        taxonomy = builder.build(
            industry="fintech",
            payment_methods=["custom_gateway"],
        )

        assert "custom_gateway_payment" in taxonomy["categories"]

    def test_save_roundtrip(self, tmp_path):
        builder = TaxonomyBuilder()
        taxonomy = builder.build(industry="legal")
        path = tmp_path / "test_taxonomy.json"
        result = builder.save(taxonomy, path)
        assert result.exists()
        assert result.read_text()
