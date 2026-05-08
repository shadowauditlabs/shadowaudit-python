"""Admin agent — handles account management and data operations.

Wraps DeleteAccountTool and UpdateAccountTool with ShadowAuditTool.
BulkDataExportTool is intentionally LEFT UNGATED (simulates a real oversight).
"""

from shadowaudit.framework.langchain import ShadowAuditTool

from fintech_agent.tools.account_tools import DeleteAccountTool, UpdateAccountTool, BulkDataExportTool
from fintech_agent.tools.readonly_tools import BalanceInquiryTool, TransactionHistoryTool


def build_admin_agent():
    """Build the admin agent with gated tools.

    BulkDataExportTool is intentionally NOT wrapped — another oversight
    that ShadowAudit's CI check would catch before deployment.
    """
    safe_delete = ShadowAuditTool(
        tool=DeleteAccountTool(),
        agent_id="admin-agent-1",
        risk_category="delete",
    )

    safe_update = ShadowAuditTool(
        tool=UpdateAccountTool(),
        agent_id="admin-agent-1",
        risk_category="update",
    )

    safe_balance = ShadowAuditTool(
        tool=BalanceInquiryTool(),
        agent_id="admin-agent-1",
        risk_category="read_only",
    )

    safe_history = ShadowAuditTool(
        tool=TransactionHistoryTool(),
        agent_id="admin-agent-1",
        risk_category="read_only",
    )

    # BulkDataExportTool — INTENTIONALLY UNGATED
    # This is a data exfiltration risk that should be caught in CI
    bulk_export = BulkDataExportTool()

    return {
        "delete_account": safe_delete,
        "update_account": safe_update,
        "check_balance": safe_balance,
        "transaction_history": safe_history,
        "bulk_export": bulk_export,  # UNGATED — ShadowAudit will flag this
    }
