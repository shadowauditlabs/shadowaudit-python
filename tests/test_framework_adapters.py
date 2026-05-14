from __future__ import annotations

import pytest

from shadowaudit.errors import AgentActionBlocked
from shadowaudit.framework.autogen import ShadowAuditAutoGenTool
from shadowaudit.framework.llamaindex import ShadowAuditLlamaIndexTool
from shadowaudit.framework.pydanticai import ShadowAuditPydanticTool


def _write_policy(tmp_path, content: str) -> str:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(content, encoding="utf-8")
    return str(policy_path)


def test_pydanticai_tool_allows(tmp_path):
    policy_path = _write_policy(
        tmp_path,
        """
allow:
  - capability: tool.execute
""",
    )

    def tool_fn(value: str) -> str:
        return f"ok:{value}"

    safe_tool = ShadowAuditPydanticTool(
        tool=tool_fn,
        agent_id="test-agent",
        capability="tool.execute",
        policy_path=policy_path,
    )

    assert safe_tool("hello") == "ok:hello"


def test_pydanticai_tool_blocks(tmp_path):
    policy_path = _write_policy(
        tmp_path,
        """
deny:
  - capability: tool.execute
""",
    )

    def tool_fn(value: str) -> str:
        return f"ok:{value}"

    safe_tool = ShadowAuditPydanticTool(
        tool=tool_fn,
        agent_id="test-agent",
        capability="tool.execute",
        policy_path=policy_path,
    )

    with pytest.raises(AgentActionBlocked):
        safe_tool("blocked")


def test_llamaindex_tool_allows(tmp_path):
    policy_path = _write_policy(
        tmp_path,
        """
allow:
  - capability: tool.execute
""",
    )

    class DummyTool:
        name = "dummy"

        def call(self, payload):
            return {"ok": payload}

    safe_tool = ShadowAuditLlamaIndexTool(
        tool=DummyTool(),
        agent_id="test-agent",
        capability="tool.execute",
        policy_path=policy_path,
    )

    assert safe_tool.call({"value": 1}) == {"ok": {"value": 1}}


def test_llamaindex_tool_blocks(tmp_path):
    policy_path = _write_policy(
        tmp_path,
        """
deny:
  - capability: tool.execute
""",
    )

    class DummyTool:
        name = "dummy"

        def call(self, payload):
            return {"ok": payload}

    safe_tool = ShadowAuditLlamaIndexTool(
        tool=DummyTool(),
        agent_id="test-agent",
        capability="tool.execute",
        policy_path=policy_path,
    )

    with pytest.raises(AgentActionBlocked):
        safe_tool.call({"value": 1})


def test_autogen_tool_allows(tmp_path):
    policy_path = _write_policy(
        tmp_path,
        """
allow:
  - capability: tool.execute
""",
    )

    def tool_fn(payload):
        return f"ok:{payload['value']}"

    safe_tool = ShadowAuditAutoGenTool(
        tool=tool_fn,
        agent_id="test-agent",
        capability="tool.execute",
        policy_path=policy_path,
    )

    assert safe_tool({"value": "hi"}) == "ok:hi"


def test_autogen_tool_blocks(tmp_path):
    policy_path = _write_policy(
        tmp_path,
        """
deny:
  - capability: tool.execute
""",
    )

    def tool_fn(payload):
        return f"ok:{payload['value']}"

    safe_tool = ShadowAuditAutoGenTool(
        tool=tool_fn,
        agent_id="test-agent",
        capability="tool.execute",
        policy_path=policy_path,
    )

    with pytest.raises(AgentActionBlocked):
        safe_tool({"value": "blocked"})
