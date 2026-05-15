# Secure MCP Filesystem Access

## Policy

```yaml
deny:
  - capability: filesystem.delete

require_approval:
  - capability: filesystem.write
    path_prefix: "/data/prod"

allow:
  - capability: filesystem.read
  - capability: filesystem.list
  - capability: filesystem.write
    path_prefix: "/data/staging"
```

## Integration

```python
from capfence.mcp.gateway import MCPGatewayServer
from capfence.core.gate import Gate

MCPGatewayServer(
    upstream_command=["python", "-m", "mcp_server_filesystem", "/data"],
    gate=Gate(),
    policy_path="policies/mcp.yaml",
    agent_id="mcp-agent",
).run()
```

## Expected result

- Deletes are blocked.
- Writes to `/data/prod` require approval.
- Reads and writes to `/data/staging` are allowed.
