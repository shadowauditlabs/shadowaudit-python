"""Example: Realistic LangChain agent with BaseTool subclasses and ShadowAudit wrappers.

This file uses actual BaseTool inheritance patterns (not mocks) so the
AST scanner can detect them via `shadowaudit check`.

Usage:
    shadowaudit check ./examples/langchain_realistic.py
    shadowaudit check ./examples/langchain_realistic.py --output report.html
"""

from langchain.tools import BaseTool

from shadowaudit.framework.langchain import ShadowAuditTool


class ShellTool(BaseTool):
    """Run shell commands on the host system."""
    name: str = "shell"
    description: str = "Execute shell commands"

    def _run(self, command: str) -> str:
        return f"Executed: {command}"


class PaymentTool(BaseTool):
    """Process customer payments via Stripe."""
    name: str = "payment"
    description: str = "Process Stripe payments and transfers"

    def _run(self, amount: float, destination: str) -> str:
        return f"Paid ${amount} to {destination}"


class ReadBalanceTool(BaseTool):
    """Read account balance — read-only, safe."""
    name: str = "read_balance"
    description: str = "Read account balance information"

    def _run(self, account_id: str) -> str:
        return f"Balance for {account_id}: $1,000.00"


class DeleteAccountTool(BaseTool):
    """Permanently delete a customer account."""
    name: str = "delete_account"
    description: str = "Delete customer accounts from the system"

    def _run(self, account_id: str) -> str:
        return f"Deleted account: {account_id}"


class SendEmailTool(BaseTool):
    """Send emails via external API."""
    name: str = "send_email"
    description: str = "Send emails to customers via SendGrid"

    def _run(self, to_address: str, subject: str, body: str) -> str:
        return f"Sent email to {to_address}"


# These tools ARE wrapped with ShadowAuditTool — the scanner should detect this
safe_shell = ShadowAuditTool(
    tool=ShellTool(),
    agent_id="ops-agent-1",
    risk_category="execute",
)

# Payment tool intentionally LEFT ungated for demo purposes
# (the scanner should flag this as a high-risk ungated finding)

# Read-only tool wrapped for auditing
safe_balance = ShadowAuditTool(
    tool=ReadBalanceTool(),
    agent_id="finance-agent-1",
    risk_category="read_only",
)

# Delete tool wrapped
safe_delete = ShadowAuditTool(
    tool=DeleteAccountTool(),
    agent_id="ops-agent-1",
    risk_category="delete",
)

# Email tool intentionally LEFT ungated


def main():
    print("Realistic LangChain agent with 5 tools:")
    print(f"  - ShellTool (gated)")
    print(f"  - PaymentTool (UNGATED)")
    print(f"  - ReadBalanceTool (gated)")
    print(f"  - DeleteAccountTool (gated)")
    print(f"  - SendEmailTool (UNGATED)")


if __name__ == "__main__":
    main()