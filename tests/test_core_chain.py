"""Tests for hash-chained audit log verifier."""

from capfence.core.chain import (
    ChainEntry,
    compute_entry_hash,
    verify_chain,
    verify_chain_from_rows,
)


class TestComputeEntryHash:
    def test_deterministic(self):
        fields = {"agent_id": "a", "decision": "pass", "timestamp": 1.0}
        h1 = compute_entry_hash(fields, "")
        h2 = compute_entry_hash(fields, "")
        assert h1 == h2

    def test_prev_hash_changes_output(self):
        fields = {"agent_id": "a", "decision": "pass", "timestamp": 1.0}
        h1 = compute_entry_hash(fields, "")
        h2 = compute_entry_hash(fields, "abc")
        assert h1 != h2

    def test_field_changes_output(self):
        fields1 = {"agent_id": "a", "decision": "pass", "timestamp": 1.0}
        fields2 = {"agent_id": "a", "decision": "fail", "timestamp": 1.0}
        h1 = compute_entry_hash(fields1, "")
        h2 = compute_entry_hash(fields2, "")
        assert h1 != h2


class TestVerifyChain:
    def test_empty_chain(self):
        valid, errors = verify_chain([])
        assert valid is True
        assert errors == []

    def test_single_entry(self):
        fields = {
            "agent_id": "a",
            "task_context": "t",
            "risk_category": None,
            "decision": "pass",
            "risk_score": 0.0,
            "threshold": 0.5,
            "payload_hash": None,
            "reason": None,
            "latency_ms": 1,
            "timestamp": 1.0,
        }
        h = compute_entry_hash(fields, "")
        entry = ChainEntry(
            id=1,
            agent_id="a",
            task_context="t",
            risk_category=None,
            decision="pass",
            risk_score=0.0,
            threshold=0.5,
            payload_hash=None,
            reason=None,
            latency_ms=1,
            timestamp=1.0,
            prev_hash="",
            entry_hash=h,
        )
        valid, errors = verify_chain([entry])
        assert valid is True
        assert errors == []

    def test_tampered_entry_hash(self):
        fields = {
            "agent_id": "a",
            "task_context": "t",
            "risk_category": None,
            "decision": "pass",
            "risk_score": 0.0,
            "threshold": 0.5,
            "payload_hash": None,
            "reason": None,
            "latency_ms": 1,
            "timestamp": 1.0,
        }
        compute_entry_hash(fields, "")
        entry = ChainEntry(
            id=1,
            agent_id="a",
            task_context="t",
            risk_category=None,
            decision="pass",
            risk_score=0.0,
            threshold=0.5,
            payload_hash=None,
            reason=None,
            latency_ms=1,
            timestamp=1.0,
            prev_hash="",
            entry_hash="badhash",
        )
        valid, errors = verify_chain([entry])
        assert valid is False
        assert any("entry_hash mismatch" in e for e in errors)

    def test_tampered_prev_hash(self):
        fields = {
            "agent_id": "a",
            "task_context": "t",
            "risk_category": None,
            "decision": "pass",
            "risk_score": 0.0,
            "threshold": 0.5,
            "payload_hash": None,
            "reason": None,
            "latency_ms": 1,
            "timestamp": 1.0,
        }
        h = compute_entry_hash(fields, "")
        entry = ChainEntry(
            id=1,
            agent_id="a",
            task_context="t",
            risk_category=None,
            decision="pass",
            risk_score=0.0,
            threshold=0.5,
            payload_hash=None,
            reason=None,
            latency_ms=1,
            timestamp=1.0,
            prev_hash="wrong",
            entry_hash=h,
        )
        valid, errors = verify_chain([entry])
        assert valid is False
        assert any("prev_hash mismatch" in e for e in errors)

    def test_two_entry_chain(self):
        fields1 = {
            "agent_id": "a",
            "task_context": "t1",
            "risk_category": None,
            "decision": "pass",
            "risk_score": 0.0,
            "threshold": 0.5,
            "payload_hash": None,
            "reason": None,
            "latency_ms": 1,
            "timestamp": 1.0,
        }
        h1 = compute_entry_hash(fields1, "")
        fields2 = {
            "agent_id": "a",
            "task_context": "t2",
            "risk_category": None,
            "decision": "fail",
            "risk_score": 0.9,
            "threshold": 0.5,
            "payload_hash": None,
            "reason": None,
            "latency_ms": 2,
            "timestamp": 2.0,
        }
        h2 = compute_entry_hash(fields2, h1)
        entries = [
            ChainEntry(
                id=1,
                agent_id="a",
                task_context="t1",
                risk_category=None,
                decision="pass",
                risk_score=0.0,
                threshold=0.5,
                payload_hash=None,
                reason=None,
                latency_ms=1,
                timestamp=1.0,
                prev_hash="",
                entry_hash=h1,
            ),
            ChainEntry(
                id=2,
                agent_id="a",
                task_context="t2",
                risk_category=None,
                decision="fail",
                risk_score=0.9,
                threshold=0.5,
                payload_hash=None,
                reason=None,
                latency_ms=2,
                timestamp=2.0,
                prev_hash=h1,
                entry_hash=h2,
            ),
        ]
        valid, errors = verify_chain(entries)
        assert valid is True
        assert errors == []

    def test_two_entry_broken_link(self):
        fields1 = {
            "agent_id": "a",
            "task_context": "t1",
            "risk_category": None,
            "decision": "pass",
            "risk_score": 0.0,
            "threshold": 0.5,
            "payload_hash": None,
            "reason": None,
            "latency_ms": 1,
            "timestamp": 1.0,
        }
        h1 = compute_entry_hash(fields1, "")
        fields2 = {
            "agent_id": "a",
            "task_context": "t2",
            "risk_category": None,
            "decision": "fail",
            "risk_score": 0.9,
            "threshold": 0.5,
            "payload_hash": None,
            "reason": None,
            "latency_ms": 2,
            "timestamp": 2.0,
        }
        h2 = compute_entry_hash(fields2, h1)
        entries = [
            ChainEntry(
                id=1,
                agent_id="a",
                task_context="t1",
                risk_category=None,
                decision="pass",
                risk_score=0.0,
                threshold=0.5,
                payload_hash=None,
                reason=None,
                latency_ms=1,
                timestamp=1.0,
                prev_hash="",
                entry_hash=h1,
            ),
            ChainEntry(
                id=2,
                agent_id="a",
                task_context="t2",
                risk_category=None,
                decision="fail",
                risk_score=0.9,
                threshold=0.5,
                payload_hash=None,
                reason=None,
                latency_ms=2,
                timestamp=2.0,
                prev_hash="tampered",
                entry_hash=h2,
            ),
        ]
        valid, errors = verify_chain(entries)
        assert valid is False
        assert any("prev_hash mismatch" in e for e in errors)


class TestVerifyChainFromRows:
    def test_valid_rows(self):
        rows = [
            {
                "id": 1,
                "agent_id": "a",
                "task_context": "t",
                "risk_category": None,
                "decision": "pass",
                "risk_score": 0.0,
                "threshold": 0.5,
                "payload_hash": None,
                "reason": None,
                "latency_ms": 1,
                "timestamp": 1.0,
                "prev_hash": "",
                "entry_hash": compute_entry_hash(
                    {
                        "agent_id": "a",
                        "task_context": "t",
                        "risk_category": None,
                        "decision": "pass",
                        "risk_score": 0.0,
                        "threshold": 0.5,
                        "payload_hash": None,
                        "reason": None,
                        "latency_ms": 1,
                        "timestamp": 1.0,
                    },
                    "",
                ),
            }
        ]
        valid, errors = verify_chain_from_rows(rows)
        assert valid is True
        assert errors == []
