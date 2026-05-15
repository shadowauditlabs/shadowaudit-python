"""Taxonomy loader with embedded starter packs.

The open-source SDK includes basic taxonomies for common domains.
Proprietary taxonomies are loaded from user-provided JSON or cloud API.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast


class TaxonomyLoader:
    """Load risk taxonomies from embedded starter packs or user paths."""

    _cache: dict[str, Any] | None = None

    @classmethod
    def _starter_dir(cls) -> Path:
        """Return the directory containing built-in taxonomy JSONs."""
        import capfence
        pkg_dir = Path(capfence.__file__).parent
        # Package-bundled taxonomies (wheel install)
        in_pkg = pkg_dir / "taxonomies"
        if in_pkg.exists():
            return in_pkg
        # Source tree: taxonomies/ sibling to capfence/
        src_tree = pkg_dir.parent / "taxonomies"
        if src_tree.exists():
            return src_tree
        return in_pkg

    @classmethod
    def load(cls, path: str | Path | None = None) -> dict[str, Any]:
        cache_key = str(path) if path is not None else "__default__"
        if cls._cache is not None and cache_key == "__default__":
            return copy.deepcopy(cls._cache)

        if path is not None:
            name = str(path)
            if "/" not in name and "\\" not in name and not name.endswith(".json"):
                starter_path = cls._starter_dir() / f"{name}.json"
                if starter_path.exists():
                    with open(starter_path, "r", encoding="utf-8") as f:
                        data: dict[str, Any] = cast(dict[str, Any], json.load(f))
                    return copy.deepcopy(data)
            with open(path, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
        else:
            data = cls._load_embedded("general")

        if path is None:
            cls._cache = data
        return copy.deepcopy(data)

    @classmethod
    def lookup(
        cls,
        risk_category: str | None,
        *,
        taxonomy_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Return taxonomy entry or safe default."""
        data = cls.load(taxonomy_path)
        categories = data.get("categories", {})
        if risk_category and risk_category in categories:
            return cast(dict[str, Any], categories[risk_category])
        return cast(dict[str, Any], {"delta": 0.1, "risk_keywords": [], "description": "Unknown category"})

    @classmethod
    def _load_embedded(cls, name: str) -> dict[str, Any]:
        """Load a built-in starter pack from taxonomies/<name>.json."""
        starter_dir = cls._starter_dir()
        file_path = starter_dir / f"{name}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
                return data
        # Fallback to hard-coded general taxonomy if files aren't on disk
        return cast(dict[str, Any], {
            "version": "1.0",
            "domain": name,
            "categories": {
                "low_risk": {
                    "delta": 1.0,
                    "risk_keywords": ["read", "list", "get", "view"],
                    "description": "Read-only operations",
                },
                "write": {
                    "delta": 0.4,
                    "risk_keywords": ["write", "update", "modify", "create"],
                    "description": "Data mutation operations",
                },
                "delete": {
                    "delta": 0.6,
                    "risk_keywords": ["delete", "remove", "drop", "destroy"],
                    "description": "Destructive operations",
                },
                "financial": {
                    "delta": 0.8,
                    "risk_keywords": ["transfer", "disburse", "pay", "withdraw", "send_money"],
                    "description": "Financial transactions",
                },
            },
        })

    @classmethod
    def reset_cache(cls) -> None:
        cls._cache = None


def load_taxonomy(path: str | Path | None = None) -> dict[str, Any]:
    return TaxonomyLoader.load(path)


# Week 5: Stripe API method → risk category mapper
STRIPE_API_MAP: dict[str, str] = {
    # Payment Intents (charges)
    "charges.create": "stripe_payment_initiation",
    "charges.capture": "stripe_payment_initiation",
    "charges.update": "stripe_payment_initiation",
    "payment_intents.create": "stripe_payment_initiation",
    "payment_intents.confirm": "stripe_payment_initiation",
    "payment_intents.capture": "stripe_payment_initiation",
    "payment_intents.update": "stripe_payment_initiation",
    "setup_intents.create": "stripe_payment_initiation",
    "setup_intents.confirm": "stripe_payment_initiation",

    # Refunds
    "refunds.create": "stripe_refund",
    "refunds.update": "stripe_refund",
    "refunds.cancel": "stripe_refund",

    # Payouts
    "payouts.create": "stripe_payout",
    "payouts.cancel": "stripe_payout",
    "payouts.reverse": "stripe_payout",

    # Subscriptions
    "subscriptions.create": "stripe_subscription",
    "subscriptions.update": "stripe_subscription",
    "subscriptions.cancel": "stripe_subscription",
    "invoices.create": "stripe_subscription",
    "invoices.pay": "stripe_subscription",

    # Issuing (cards)
    "issuing.cards.create": "stripe_issuing_card",
    "issuing.cardholders.create": "stripe_issuing_card",

    # Customer management
    "customers.create": "stripe_customer_mgmt",
    "customers.update": "stripe_customer_mgmt",
    "payment_methods.attach": "stripe_customer_mgmt",
    "payment_methods.detach": "stripe_customer_mgmt",

    # Disputes
    "disputes.create": "stripe_dispute",
    "disputes.update": "stripe_dispute",
    "disputes.close": "stripe_dispute",
}


def stripe_mapper(api_method: str) -> str | None:
    """Map a Stripe API method to its CapFence risk category.

    Args:
        api_method: Stripe API method string (e.g. "charges.create", "payouts.cancel").

    Returns:
        Risk category name from the financial taxonomy, or the closest match
        if an exact match is not found. Returns None if no mapping can be inferred.

    Examples:
        >>> stripe_mapper("charges.create")
        "stripe_payment_initiation"
        >>> stripe_mapper("refunds.create")
        "stripe_refund"
        >>> stripe_mapper("unknown.method")
        None
    """
    # Exact match
    if api_method in STRIPE_API_MAP:
        return STRIPE_API_MAP[api_method]

    # Fuzzy match: try the resource prefix (e.g. "charges.xxx" → "charges")
    resource = api_method.split(".")[0] if "." in api_method else api_method
    for key, category in STRIPE_API_MAP.items():
        if key.startswith(resource + "."):
            return category

    return None

