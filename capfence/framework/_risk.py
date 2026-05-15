"""Tool-name → risk-category heuristic shared by adapters that wrap many tools."""
from __future__ import annotations

_CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("command_execution", ("shell", "exec", "run", "command", "bash", "sh")),
    ("payment_initiation", ("pay", "transfer", "send", "disburse", "stripe")),
    ("delete", ("delete", "remove", "drop", "wipe")),
    ("write", ("write", "update", "modify", "patch")),
    ("read_only", ("read", "get", "list", "view", "query")),
)


def guess_risk_category(tool_name: str) -> str | None:
    """Map a tool name to a coarse risk category using substring keywords.

    Returns None if no keyword matches. Adapters layer their own explicit
    overrides on top of this fallback.
    """
    name = tool_name.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(k in name for k in keywords):
            return category
    return None
