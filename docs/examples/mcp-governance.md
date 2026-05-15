# MCP Governance Example

This example puts CapFence between an agent and an MCP server so MCP tool calls are authorized before they reach the upstream server.

## Gateway

```python
from capfence.mcp.gateway import MCPGatewayServer

gateway = MCPGatewayServer(
    upstream_command=[
        "python",
        "-m",
        "mcp_server_filesystem",
        "/tmp",
    ],
    policy_path="policies/mcp_filesystem.yaml",
)

gateway.run()
```

## Policy

```yaml
# policies/mcp_filesystem.yaml

deny:
  - capability: filesystem.delete
  - capability: filesystem.write
    path_prefix: /etc

require_approval:
  - capability: filesystem.write
    path_prefix: /var

allow:
  - capability: filesystem.read
  - capability: filesystem.list
```

## Decision flow

```text
Agent → CapFence MCP Gateway → MCP Server
          │
          ├─ allow read/list tools
          ├─ require approval for sensitive writes
          └─ deny destructive filesystem tools
```

## Operational use

Use this pattern when a model can discover and call tools from an MCP server but you still need infrastructure-grade authorization at execution time.

