"""Test that ShadowAudit correctly detects gated and ungated tools.

Run with: shadowaudit check src/ --fail-on-ungated
"""

import subprocess
import sys
from pathlib import Path


def test_shadowaudit_check_finds_all_tools():
    """Verify shadowaudit check detects all 8 tools in the project."""
    src_dir = Path(__file__).parent.parent / "src"
    result = subprocess.run(
        [sys.executable, "-m", "shadowaudit.cli", "check", str(src_dir)],
        capture_output=True,
        text=True,
    )
    output = result.stdout

    # All 8 tools should be found
    assert "8 tool(s) found" in output, f"Expected 8 tools, got:\n{output}"

    # 6 should be gated
    assert "Gated:           6" in output, f"Expected 6 gated, got:\n{output}"

    # 2 should be ungated
    assert "Ungated:         2" in output, f"Expected 2 ungated, got:\n{output}"

    # 1 high-risk ungated (BulkDataExportTool, delta=0.15 <= 0.2)
    # WireTransferTool is ungated but delta=0.3 > 0.2, so not "high-risk"
    assert "High-risk ungated: 1" in output, f"Expected 1 high-risk ungated, got:\n{output}"


def test_shadowaudit_check_fail_on_ungated():
    """Verify --fail-on-ungated exits with code 1 when ungated tools exist."""
    src_dir = Path(__file__).parent.parent / "src"
    result = subprocess.run(
        [sys.executable, "-m", "shadowaudit.cli", "check", str(src_dir), "--fail-on-ungated"],
        capture_output=True,
        text=True,
    )

    # Should exit non-zero because there are ungated high-risk tools
    assert result.returncode == 1, (
        f"Expected exit code 1 for ungated tools, got {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_shadowaudit_check_cross_file_detection():
    """Verify cross-file wrapper detection works.

    Tools are defined in fintech_agent/tools/*.py
    Wrappers are in fintech_agent/agents/*.py

    The scanner must connect these across files.
    """
    src_dir = Path(__file__).parent.parent / "src"
    result = subprocess.run(
        [sys.executable, "-m", "shadowaudit.cli", "check", str(src_dir)],
        capture_output=True,
        text=True,
    )
    output = result.stdout

    # These tools are wrapped in agents/*.py — cross-file detection must work
    assert "PaymentTool" in output and "YES" in output, "PaymentTool should be gated"
    assert "RefundTool" in output and "YES" in output, "RefundTool should be gated"
    assert "DeleteAccountTool" in output and "YES" in output, "DeleteAccountTool should be gated"
    assert "UpdateAccountTool" in output and "YES" in output, "UpdateAccountTool should be gated"
    assert "BalanceInquiryTool" in output and "YES" in output, "BalanceInquiryTool should be gated"
    assert "TransactionHistoryTool" in output and "YES" in output, "TransactionHistoryTool should be gated"

    # These are intentionally ungated
    assert "WireTransferTool" in output and "NO" in output, "WireTransferTool should be ungated"
    assert "BulkDataExportTool" in output and "NO" in output, "BulkDataExportTool should be ungated"
