"""Example: OpenAI Agents SDK integration with ShadowAudit (Week 10).

Demonstrates ShadowAuditOpenAITool wrapper.
"""

import asyncio
from shadowaudit.framework.openai_agents import ShadowAuditOpenAITool


class MockOpenAITool:
    """Mock OpenAI Agents SDK tool."""

    def __init__(self, name: str):
        self.name = name
        self.description = f"Mock tool: {name}"
        self.params_json_schema = {"type": "object"}

    async def on_invoke_tool(self, context, input_json: str):
        return f"Executed {self.name} with {input_json}"


def main():
    # Create mock tools
    read_tool = MockOpenAITool("read_data")
    pay_tool = MockOpenAITool("process_payment")

    # Wrap with ShadowAudit
    safe_read = ShadowAuditOpenAITool(
        tool=read_tool,
        agent_id="openai-agent-1",
        risk_category="read_only",
    )
    safe_pay = ShadowAuditOpenAITool(
        tool=pay_tool,
        agent_id="openai-agent-1",
        risk_category="payment_initiation",
    )

    print("OpenAI Agents SDK Integration")
    print("=" * 40)
    print(f"Read tool name: {safe_read.name}")
    print(f"Pay tool name:  {safe_pay.name}")

    # Test safe call
    print("\nTest 1: read_data (safe)")
    try:
        result = asyncio.run(safe_read.on_invoke_tool(None, '{"query": "users"}'))
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Blocked: {e}")

    # Test blocked call
    print("\nTest 2: process_payment with high amount (blocked)")
    try:
        result = asyncio.run(safe_pay.on_invoke_tool(None, '{"amount": 999999, "to": "hacker"}'))
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Blocked: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
