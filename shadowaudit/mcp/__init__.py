"""MCP (Model Context Protocol) gateway for ShadowAudit.

Provides proxy and in-process interception of MCP tool calls
through the ShadowAudit Gate.
"""

from shadowaudit.mcp.gateway import MCPGatewayServer
from shadowaudit.mcp.adapter import ShadowAuditMCPSession

__all__ = ["MCPGatewayServer", "ShadowAuditMCPSession"]
