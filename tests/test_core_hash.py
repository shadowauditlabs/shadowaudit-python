"""Tests for deterministic payload hashing."""

from shadowaudit.core.hash import compute_payload_hash


class TestPayloadHash:
    def test_deterministic(self):
        p = {"b": 2, "a": 1}
        h1 = compute_payload_hash(p)
        h2 = compute_payload_hash(p)
        assert h1 == h2
        assert len(h1) == 64

    def test_order_independent(self):
        h1 = compute_payload_hash({"a": 1, "b": 2})
        h2 = compute_payload_hash({"b": 2, "a": 1})
        assert h1 == h2

    def test_different_payloads_different_hash(self):
        h1 = compute_payload_hash({"a": 1})
        h2 = compute_payload_hash({"a": 2})
        assert h1 != h2

    def test_nested(self):
        h1 = compute_payload_hash({"outer": {"inner": [1, 2, 3]}})
        h2 = compute_payload_hash({"outer": {"inner": [1, 2, 3]}})
        assert h1 == h2
