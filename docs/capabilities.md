# Capability Taxonomy

ShadowAudit uses a **Capability Taxonomy** to govern what AI agents are permitted to do, independent of the underlying tool implementation.

## Core Principles
1. **Reusability**: `filesystem.read` means the same thing whether an agent uses Python's `os` module, a Bash command, or an MCP server.
2. **Inheritance**: `filesystem.all` implies `filesystem.read`, `filesystem.write`, and `filesystem.delete`.
3. **Deterministic Evaluation**: Capabilities are mapped directly to allow, deny, or require_approval actions via the Policy Engine.

## Standard Capabilities

### Filesystem
- `filesystem.read`
- `filesystem.write`
- `filesystem.delete`

### Shell
- `shell.execute`
- `shell.root_access`

### Database
- `database.read`
- `database.write`
- `database.drop`

### Network & APIs
- `network.external_request`
- `payments.transfer`
- `mcp.tool.execute`

## Grouping
You can group capabilities to simplify policies:

```python
registry.register_group("database.all", ["database.read", "database.write", "database.drop"])
```
