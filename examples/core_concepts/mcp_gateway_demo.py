"""Example: MCP gateway with ShadowAudit gating (Week 9).

Demonstrates how to wrap an MCP server with ShadowAudit enforcement.
"""

from shadowaudit.mcp.gateway import MCPGatewayServer
from shadowaudit.mcp.adapter import ShadowAuditMCPSession


def main():
    # Example 1: Gateway server (stdio proxy mode)
    print("MCP Gateway Server")
    print("=" * 40)
    gateway = MCPGatewayServer(
        upstream_command=["python", "-m", "mcp_server_filesystem", "/tmp"],
        agent_id="mcp-agent-1",
        default_risk_category="command_execution",
    )
    print(f"Gateway created for agent: {gateway._agent_id}")
    print(f"Default risk category: {gateway._default_risk_category}")

    # Example 2: In-process adapter
    print("\nMCP In-Process Adapter")
    print("=" * 40)

    class MockMCPSession:
        """Mock MCP client session for demo."""

        async def call_tool(self, name: str, arguments: dict):
            return f"Mock result for {name}"

    session = ShadowAuditMCPSession(
        underlying_session=MockMCPSession(),
        agent_id="mcp-agent-2",
        default_risk_category="read_only",
    )
    print(f"Session created for agent: {session._agent_id}")

    # Test category guessing
    print("\nRisk category guessing:")
    for tool_name in ["read_file", "shell", "pay_vendor", "delete_user", "update_config"]:
        cat = MCPGatewayServer._guess_category(tool_name)
        print(f"  {tool_name:<20} -> {cat}")


if __name__ == "__main__":
    main()
