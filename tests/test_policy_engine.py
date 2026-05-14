from __future__ import annotations

from click.testing import CliRunner

from shadowaudit.cli import main
from shadowaudit.core.gate import Gate
from shadowaudit.core.policy import PolicyLoader


def test_policy_conditions_contains_amount_lte_and_path_prefix(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
deny:
  - capability: shell.execute
    contains: "rm -rf"
  - capability: filesystem.write
    path_prefix: "/etc"

require_approval:
  - capability: payments.transfer
    amount_gt: 1000

allow:
  - capability: shell.execute
  - capability: filesystem.write
    path_prefix: "/tmp"
  - capability: payments.transfer
    amount_lte: 1000
""",
        encoding="utf-8",
    )

    gate = Gate()

    blocked_shell = gate.evaluate(
        "agent",
        "shell",
        "read_only",
        {"command": "rm -rf /tmp/cache"},
        capability="shell.execute",
        policy_path=str(policy_path),
    )
    assert blocked_shell.passed is False
    assert blocked_shell.reason == "policy_deny"

    allowed_shell = gate.evaluate(
        "agent",
        "shell",
        "read_only",
        {"command": "ls /tmp"},
        capability="shell.execute",
        policy_path=str(policy_path),
    )
    assert allowed_shell.passed is True
    assert allowed_shell.reason == "policy_allow"

    blocked_path = gate.evaluate(
        "agent",
        "write",
        "write",
        {"path": "/etc/hosts", "content": "x"},
        capability="filesystem.write",
        policy_path=str(policy_path),
    )
    assert blocked_path.passed is False
    assert blocked_path.reason == "policy_deny"

    allowed_amount = gate.evaluate(
        "agent",
        "transfer",
        "read_only",
        {"amount": 500},
        capability="payments.transfer",
        policy_path=str(policy_path),
    )
    assert allowed_amount.passed is True
    assert allowed_amount.reason == "policy_allow"

    approval_amount = gate.evaluate(
        "agent",
        "transfer",
        "read_only",
        {"amount": 1500},
        capability="payments.transfer",
        policy_path=str(policy_path),
    )
    assert approval_amount.passed is False
    assert approval_amount.reason.startswith("approval_required:")


def test_policy_default_deny_when_no_rule_matches(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
allow:
  - capability: filesystem.read
""",
        encoding="utf-8",
    )

    result = Gate().evaluate(
        "agent",
        "db",
        "read_only",
        {"query": "select 1"},
        capability="database.write",
        policy_path=str(policy_path),
    )

    assert result.passed is False
    assert result.reason == "policy_default_deny"


def test_policy_error_fails_closed(tmp_path):
    policy_path = tmp_path / "bad.yaml"
    policy_path.write_text(
        """
allow:
  - description: missing capability
""",
        encoding="utf-8",
    )

    result = Gate().evaluate(
        "agent",
        "shell",
        "read_only",
        {"command": "ls"},
        capability="shell.execute",
        policy_path=str(policy_path),
    )

    assert result.passed is False
    assert result.reason == "policy_error_PolicyLoadError"


def test_policy_caller_depth_condition(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
deny:
  - capability: agent.delegate
    caller_depth_gt: 2
allow:
  - capability: agent.delegate
""",
        encoding="utf-8",
    )

    result = Gate().evaluate(
        "agent",
        "delegate",
        "read_only",
        {"target": "subagent"},
        capability="agent.delegate",
        policy_path=str(policy_path),
        policy_context={"caller_depth": 3},
    )

    assert result.passed is False
    assert result.reason == "policy_deny"


def test_policy_loader_rejects_unknown_condition(tmp_path):
    policy_path = tmp_path / "bad.yaml"
    policy_path.write_text(
        """
allow:
  - capability: shell.execute
    made_up_condition: true
""",
        encoding="utf-8",
    )

    try:
        PolicyLoader().load(policy_path)
    except Exception as exc:
        assert type(exc).__name__ == "PolicyLoadError"
        assert "made_up_condition" in str(exc)
    else:
        raise AssertionError("PolicyLoader accepted an unknown condition")


def test_check_policy_cli(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
allow:
  - capability: shell.execute
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["check-policy", str(policy_path)])

    assert result.exit_code == 0
    assert "[POLICY] VALID" in result.output


def test_legacy_rules_policy_schema(tmp_path):
    policy_path = tmp_path / "legacy.yaml"
    policy_path.write_text(
        """
version: "1.0"
policy_name: legacy_shell
description: Legacy starter policy shape
enforcement_mode: block
rules:
  - id: destructive
    description: Block destructive shell commands
    match_keywords:
      - "rm -rf"
    threshold: 0.1
    action: block
  - id: read_only
    description: Allow simple list commands
    match_regex:
      - "^ls"
    action: allow
""",
        encoding="utf-8",
    )

    gate = Gate()
    blocked = gate.evaluate(
        "agent",
        "shell",
        "read_only",
        {"command": "rm -rf /tmp/cache"},
        capability="shell.execute",
        policy_path=str(policy_path),
    )
    allowed = gate.evaluate(
        "agent",
        "shell",
        "read_only",
        {"command": "ls /tmp"},
        capability="shell.execute",
        policy_path=str(policy_path),
    )

    assert blocked.passed is False
    assert blocked.reason == "policy_deny"
    assert allowed.passed is True
    assert allowed.reason == "policy_allow"
