"""MCP (Model Context Protocol) gateway for CapFence.

Provides proxy and in-process interception of MCP tool calls
through the CapFence Gate.
"""

from capfence.mcp.gateway import MCPGatewayServer
from capfence.mcp.adapter import CapFenceMCPSession

__all__ = ["MCPGatewayServer", "CapFenceMCPSession"]
