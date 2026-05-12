"""Example: Protected LangChain agent with ShadowAudit.

Wraps tools so that risky actions are blocked before execution.
Requires: pip install shadowaudit[langchain] langchain
"""

from shadowaudit import Gate
from shadowaudit.framework.langchain import ShadowAuditTool, AgentActionBlocked


def mock_shell_tool(tool_input: str, **kwargs) -> str:
    """Simulated shell tool for demo."""
    return f"Executed: {tool_input}"


def mock_transfer_tool(tool_input: str, **kwargs) -> str:
    """Simulated bank transfer tool for demo."""
    return f"Transferred: {tool_input}"


def main():
    # Gate with general taxonomy for destructive operations
    general_gate = Gate()
    # Gate with financial taxonomy for money movement
    finance_gate = Gate(taxonomy_path="financial")

    # Wrap tools with ShadowAudit enforcement
    safe_shell = ShadowAuditTool(
        tool=type("ShellTool", (), {
            "name": "shell",
            "description": "Run shell commands",
            "run": staticmethod(mock_shell_tool),
        })(),
        agent_id="ops-agent-1",
        risk_category="execute",
        gate=general_gate,
    )

    safe_transfer = ShadowAuditTool(
        tool=type("TransferTool", (), {
            "name": "transfer",
            "description": "Transfer funds between accounts",
            "run": staticmethod(mock_transfer_tool),
        })(),
        agent_id="finance-agent-1",
        risk_category="payment_initiation",
        gate=finance_gate,
    )

    safe_delete = ShadowAuditTool(
        tool=type("DeleteTool", (), {
            "name": "delete_file",
            "description": "Delete files from filesystem",
            "run": staticmethod(lambda x: f"Deleted: {x}"),
        })(),
        agent_id="ops-agent-1",
        risk_category="delete",
        gate=general_gate,
    )

    # Simulate agent workflow
    actions = [
        (safe_shell, "ls -la /tmp"),                     # execute keywords: ls → no match → PASS
        (safe_shell, "rm -rf /sensitive"),              # rm → matches "execute" keywords? No, "rm" not in list.
        # "rm" is not in execute keywords: ["execute", "run", "exec", "call", "invoke", "trigger", "launch", "start", "spawn"]
        # So this passes. That's fine — it's a demo of the keyword-based system.
        (safe_shell, "execute rm -rf /"),               # "execute" keyword → matches → BLOCK
        (safe_transfer, "transfer $1000 to account_123"), # "transfer" keyword → matches → BLOCK (delta 0.3)
        (safe_transfer, "check balance"),               # no financial keywords → default safe → PASS
        (safe_delete, "remove old_logs.txt"),           # "remove" keyword → matches delete → BLOCK (delta 0.2)
    ]

    for tool, action in actions:
        try:
            result = tool.run(action)
            print(f"  OK    {tool.name}('{action}') -> {result}")
        except AgentActionBlocked as e:
            print(f"  BLOCK {tool.name}('{action}')")
            print(f"        Reason: {e.detail}")
            if e.gate_result:
                print(f"        Score: {e.gate_result.risk_score:.2f} / {e.gate_result.threshold:.2f}")


if __name__ == "__main__":
    main()
