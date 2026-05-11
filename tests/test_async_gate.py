"""Tests for Gate.evaluate_async and async adapter methods."""
import asyncio

import pytest

from shadowaudit.core.gate import Gate


RISKY_PAYLOAD = {
    "action": "create_payout",
    "disburse": True,
    "amount": 95000,
    "payout": True,
    "transfer_to_bank": True,
}


def test_evaluate_async_matches_sync():
    gate = Gate(taxonomy_path="financial")

    sync_result = gate.evaluate("a1", "payout", "stripe_payout", RISKY_PAYLOAD)
    async_result = asyncio.run(
        gate.evaluate_async("a2", "payout", "stripe_payout", RISKY_PAYLOAD)
    )

    assert sync_result.passed == async_result.passed
    assert sync_result.risk_category == async_result.risk_category


def test_evaluate_async_returns_gate_result():
    gate = Gate(taxonomy_path="financial")
    result = asyncio.run(
        gate.evaluate_async("a1", "balance", "balance_inquiry", {"account": "x"})
    )
    assert result.passed is True
    assert "confidence" in result.metadata


def test_evaluate_async_does_not_block_loop():
    """A second coroutine should make progress while evaluate_async is in flight."""
    gate = Gate(taxonomy_path="financial")
    progress = []

    async def worker() -> None:
        for i in range(3):
            await asyncio.sleep(0)
            progress.append(i)

    async def main() -> None:
        task = asyncio.create_task(worker())
        await gate.evaluate_async("a1", "balance", "balance_inquiry", {"x": 1})
        await task

    asyncio.run(main())
    assert progress == [0, 1, 2]


def test_evaluate_async_respects_bypass():
    gate = Gate(taxonomy_path="financial")

    async def main():
        with gate.bypass("a1", reason="oncall override"):
            return await gate.evaluate_async("a1", "payout", "stripe_payout", RISKY_PAYLOAD)

    result = asyncio.run(main())
    assert result.passed
    assert "oncall override" in result.metadata["bypass_reason"]


@pytest.mark.parametrize("n", [4, 8])
def test_evaluate_async_parallel_calls(n):
    """Many concurrent evaluations should all complete and produce valid results."""
    gate = Gate(taxonomy_path="financial")

    async def main():
        return await asyncio.gather(*[
            gate.evaluate_async(f"agent-{i}", "balance", "balance_inquiry", {"i": i})
            for i in range(n)
        ])

    results = asyncio.run(main())
    assert len(results) == n
    assert all(r.passed for r in results)
