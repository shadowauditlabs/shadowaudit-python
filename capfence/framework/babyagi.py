"""BabyAGI Plugin Adapter for CapFence.

Enforces compliance checks in BabyAGI loops.
"""

from __future__ import annotations

from typing import Any

from capfence.core.gate import Gate


class BabyAGIAdapter:
    """Adapter for BabyAGI tasks."""

    def __init__(self, gate: Gate) -> None:
        self._gate = gate

    def wrap_task(self, task_def: Any) -> None:
        """W17 MVP: Stub for wrapping BabyAGI tasks."""
        pass
