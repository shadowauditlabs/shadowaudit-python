"""AutoGPT Plugin Adapter for CapFence.

Enforces compliance checks for AutoGPT agents.
"""

from __future__ import annotations

from typing import Any

from capfence.core.gate import Gate


class AutoGPTAdapter:
    """Adapter for AutoGPT tools."""

    def __init__(self, gate: Gate) -> None:
        self._gate = gate

    def wrap_tool(self, tool_def: Any) -> None:
        """W17 MVP: Stub for wrapping AutoGPT tools."""
        pass
