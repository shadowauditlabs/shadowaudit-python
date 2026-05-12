"""Minimal MCP Gateway Demo."""
from shadowaudit.mcp.gateway import MCPGatewayServer
from shadowaudit.core.gate import Gate

if __name__ == "__main__":
    print("Initializing MCP Gateway...")
    gateway = MCPGatewayServer(
        upstream_command=["python", "-m", "mcp_server_filesystem", "/tmp"],
        gate=Gate(),
        agent_id="mcp-agent-1"
    )
    
    print("Gateway ready. Run with actual MCP client to see traffic intercepted.")
    # gateway.run() # Un-comment to run the actual blocking proxy
