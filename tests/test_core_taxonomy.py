"""Tests for taxonomy loader."""

import json

from shadowaudit.core.taxonomy import TaxonomyLoader


class TestTaxonomyLoader:
    def test_builtin_general(self):
        TaxonomyLoader.reset_cache()
        data = TaxonomyLoader.load()
        assert "categories" in data
        assert "read_only" in data["categories"]
        assert "execute" in data["categories"]

    def test_lookup_known(self):
        TaxonomyLoader.reset_cache()
        entry = TaxonomyLoader.lookup("read_only")
        assert entry["delta"] == 1.0
        assert "read" in entry["risk_keywords"]

    def test_lookup_unknown_default(self):
        entry = TaxonomyLoader.lookup("nonexistent")
        assert entry["delta"] == 0.1
        assert entry["risk_keywords"] == []

    def test_lookup_none_default(self):
        entry = TaxonomyLoader.lookup(None)
        assert entry["delta"] == 0.1

    def test_custom_taxonomy_file(self, tmp_path):
        taxonomy = {
            "version": "1.0",
            "domain": "custom",
            "categories": {
                "special": {"delta": 0.5, "risk_keywords": ["special"], "description": "Test"}
            }
        }
        path = tmp_path / "custom.json"
        path.write_text(json.dumps(taxonomy))

        entry = TaxonomyLoader.lookup("special", taxonomy_path=str(path))
        assert entry["delta"] == 0.5

    def test_cache_resets(self):
        TaxonomyLoader._cache = {"cached": True}
        TaxonomyLoader.reset_cache()
        assert TaxonomyLoader._cache is None
