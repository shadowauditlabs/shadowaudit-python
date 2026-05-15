"""Capability Taxonomy System.

Defines reusable capabilities, groupings, and inheritance.
"""

from __future__ import annotations

from typing import Any


class CapabilityRegistry:
    """Registry for capability definitions."""

    def __init__(self) -> None:
        self._capabilities: dict[str, dict[str, Any]] = {}
        self._groups: dict[str, list[str]] = {}

    def register(self, name: str, description: str = "", parent: str | None = None) -> None:
        """Register a new capability."""
        self._capabilities[name] = {"description": description, "parent": parent}

    def register_group(self, name: str, capabilities: list[str]) -> None:
        """Register a group of capabilities."""
        self._groups[name] = capabilities

    def resolve(self, capability: str) -> list[str]:
        """Resolve a capability or group into a list of specific capabilities."""
        if capability in self._groups:
            return self._groups[capability]
        
        # Resolve inheritance
        result = [capability]
        # Currently a simple list, but could traverse children if needed.
        return result

    def get_parent(self, capability: str) -> str | None:
        """Get the parent of a capability."""
        cap = self._capabilities.get(capability)
        if cap:
            return cap.get("parent")
        return None

    def implies(self, granted_capability: str, required_capability: str) -> bool:
        """Check if granted capability implies the required capability."""
        if granted_capability == required_capability:
            return True
        
        if granted_capability.endswith(".*"):
            prefix = granted_capability[:-2]
            return required_capability.startswith(prefix)

        # Check group membership
        if granted_capability in self._groups:
            if required_capability in self._groups[granted_capability]:
                return True
        
        # Check hierarchy (if A is parent of B, does A imply B? Usually yes, or A.*)
        # For simple check, we handle wildcards and explicit groups.
        return False


# Global default registry
default_registry = CapabilityRegistry()

# Standard capabilities
default_registry.register("filesystem.read", "Read files from the filesystem")
default_registry.register("filesystem.write", "Write files to the filesystem")
default_registry.register("filesystem.delete", "Delete files from the filesystem")

default_registry.register("shell.execute", "Execute shell commands")
default_registry.register("shell.root_access", "Execute shell commands as root")

default_registry.register("database.read", "Read from database")
default_registry.register("database.write", "Write to database")
default_registry.register("database.drop", "Drop database tables")

default_registry.register("network.external_request", "Make external network requests")
default_registry.register("payments.transfer", "Transfer funds")
default_registry.register("mcp.tool.execute", "Execute an MCP tool")

# Groups
default_registry.register_group("filesystem.all", ["filesystem.read", "filesystem.write", "filesystem.delete"])
default_registry.register_group("database.all", ["database.read", "database.write", "database.drop"])
