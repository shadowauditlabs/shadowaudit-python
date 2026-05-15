"""Read-only tools — safe operations with no side effects.

Low risk, but still wrapped with CapFenceTool for audit trail completeness.
"""

from langchain.tools import BaseTool


class BalanceInquiryTool(BaseTool):
    """Check account balance — read-only, no side effects.

    Risk: LOW — informational only.
    Category: read_only (delta=1.0)
    """
    name: str = "check_balance"
    description: str = "Retrieve the current balance for a customer account."

    def _run(self, account_id: str) -> str:
        return f"Balance for account {account_id}: $12,450.75"


class TransactionHistoryTool(BaseTool):
    """Retrieve transaction history — read-only.

    Risk: LOW — informational only.
    Category: read_only (delta=1.0)
    """
    name: str = "transaction_history"
    description: str = "Retrieve recent transaction history for a customer account."

    def _run(self, account_id: str, limit: int = 10) -> str:
        return f"Last {limit} transactions for account {account_id} retrieved"
