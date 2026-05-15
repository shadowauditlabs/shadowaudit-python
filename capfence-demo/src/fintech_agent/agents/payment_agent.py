"""Payment agent — handles customer payments and refunds.

Wraps PaymentTool and RefundTool with CapFenceTool.
WireTransferTool is intentionally LEFT UNGATED (simulates a real oversight).
"""

from capfence.framework.langchain import CapFenceTool

from fintech_agent.tools.payment_tools import PaymentTool, RefundTool, WireTransferTool


def build_payment_agent():
    """Build the payment agent with gated tools.

    Returns a dict of tool_name -> tool_instance.
    WireTransferTool is intentionally NOT wrapped — this is the kind of
    oversight CapFence's scanner catches in CI.
    """
    safe_payment = CapFenceTool(
        tool=PaymentTool(),
        agent_id="payment-agent-1",
        risk_category="payment_initiation",
    )

    safe_refund = CapFenceTool(
        tool=RefundTool(),
        agent_id="payment-agent-1",
        risk_category="payment_initiation",
    )

    # WireTransferTool — INTENTIONALLY UNGATED
    # In a real codebase, this might happen because:
    # - A developer forgot to wrap it
    # - It was added in a hurry during an incident
    # - The team didn't realize it was a BaseTool subclass
    wire_transfer = WireTransferTool()

    return {
        "process_payment": safe_payment,
        "issue_refund": safe_refund,
        "wire_transfer": wire_transfer,  # UNGATED — CapFence will flag this
    }
