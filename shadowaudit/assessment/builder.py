"""Interactive taxonomy builder — generates custom taxonomies from user input.

Usage:
    from shadowaudit.assessment.builder import TaxonomyBuilder

    builder = TaxonomyBuilder()
    taxonomy = builder.interactive_build()
    # or programmatic:
    taxonomy = builder.build(industry="fintech", payment_methods=["stripe"], pii=True)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class BuilderConfig:
    """Configuration for taxonomy builder."""
    industry: str
    payment_methods: list[str] = field(default_factory=list)
    pii_access: bool = False
    transfer_initiation: bool = False
    has_write_tools: bool = True
    has_delete_tools: bool = False
    has_external_api: bool = True
    compliance_required: list[str] = field(default_factory=list)


class TaxonomyBuilder:
    """Build custom taxonomies from interactive or programmatic input."""

    INDUSTRY_PRESETS: dict[str, dict[str, Any]] = {
        "fintech": {
            "categories": ["balance_inquiry", "payment_initiation", "withdrawal",
                          "high_value_transfer", "account_modification", "compliance_check"],
            "payment_pack": True,
            "compliance": ["PCI-DSS", "SOX"],
        },
        "healthcare": {
            "categories": ["read_only", "write", "external_api", "delete"],
            "payment_pack": False,
            "compliance": ["HIPAA"],
        },
        "legal": {
            "categories": ["read_only", "write", "external_api"],
            "payment_pack": False,
            "compliance": ["GDPR", "eDiscovery"],
        },
        "retail": {
            "categories": ["read_only", "write", "payment_initiation"],
            "payment_pack": True,
            "compliance": ["PCI-DSS"],
        },
    }

    def interactive_build(self) -> dict[str, Any]:
        """Build taxonomy via CLI prompts."""
        print("\n--- ShadowAudit Taxonomy Builder ---\n")

        industries = list(self.INDUSTRY_PRESETS.keys()) + ["custom"]
        print("Available industries:", ", ".join(industries))
        industry = input("> What industry? [fintech/healthcare/legal/retail/custom]: ").strip().lower()

        if industry == "custom":
            return self._build_custom()

        config = self.INDUSTRY_PRESETS.get(industry, self.INDUSTRY_PRESETS["fintech"])

        payment_methods: list[str] = []
        if config["payment_pack"]:
            pm = input("> What payment methods? [stripe/plaid/square/braintree/custom/none]: ").strip().lower()
            if pm != "none":
                payment_methods = [p.strip() for p in pm.split("/")]

        pii = input("> Do agents access PII? [y/n]: ").strip().lower().startswith("y")
        transfers = input("> Do agents initiate transfers? [y/n]: ").strip().lower().startswith("y") if config["payment_pack"] else False

        return self.build(
            industry=industry,
            payment_methods=payment_methods,
            pii_access=pii,
            transfer_initiation=transfers,
            compliance_required=config["compliance"],
        )

    def build(
        self,
        industry: str,
        payment_methods: list[str] | None = None,
        pii_access: bool = False,
        transfer_initiation: bool = False,
        has_write_tools: bool = True,
        has_delete_tools: bool = False,
        has_external_api: bool = True,
        compliance_required: list[str] | None = None,
    ) -> dict[str, Any]:
        """Programmatically build a custom taxonomy."""

        config = BuilderConfig(
            industry=industry,
            payment_methods=payment_methods or [],
            pii_access=pii_access,
            transfer_initiation=transfer_initiation,
            has_write_tools=has_write_tools,
            has_delete_tools=has_delete_tools,
            has_external_api=has_external_api,
            compliance_required=compliance_required or [],
        )

        taxonomy: dict[str, Any] = {
            "version": "2.0",
            "domain": industry,
            "generated_by": "shadowaudit_taxonomy_builder",
            "description": f"Custom taxonomy for {industry} agents",
            "categories": {},
            "compliance_mapping": {},
        }

        # Base categories
        base_cats = self._get_base_categories(config)
        taxonomy["categories"] = base_cats

        # Payment method packs
        if config.payment_methods:
            for method in config.payment_methods:
                payment_cats = self._get_payment_categories(method)
                taxonomy["categories"].update(payment_cats)

        # Compliance mappings
        if config.compliance_required:
            taxonomy["compliance_mapping"] = self._get_compliance_map(config.compliance_required)

        return taxonomy

    def save(self, taxonomy: dict[str, Any], path: Path | None = None) -> Path:
        """Save taxonomy to JSON file."""
        if path is None:
            domain = taxonomy.get("domain", "custom")
            path = Path(f"custom_taxonomy_{domain}.json")
        path.write_text(json.dumps(taxonomy, indent=2), encoding="utf-8")
        logger.info("Saved taxonomy to %s", path)
        return path

    def _get_base_categories(self, config: BuilderConfig) -> dict[str, Any]:
        """Get base risk categories for the configuration."""
        cats: dict[str, Any] = {}

        cats["read_only"] = {
            "delta": 1.0,
            "risk_keywords": ["read", "list", "get", "view", "search", "balance", "inquiry"],
            "description": "Read-only operations",
        }

        if config.has_write_tools:
            cats["write"] = {
                "delta": 0.4,
                "risk_keywords": ["write", "create", "insert", "post", "submit", "update"],
                "description": "Data mutation operations",
            }

        if config.has_delete_tools:
            cats["delete"] = {
                "delta": 0.2,
                "risk_keywords": ["delete", "remove", "drop", "destroy", "purge"],
                "description": "Destructive operations",
            }

        if config.has_external_api:
            cats["external_api"] = {
                "delta": 0.3,
                "risk_keywords": ["external", "api_call", "third_party", "webhook", "outbound"],
                "description": "External API calls",
            }

        if config.pii_access:
            cats["pii_access"] = {
                "delta": 0.15,
                "risk_keywords": ["pii", "ssn", "ssn_last4", "personal_data", "phi", "patient"],
                "description": "Access to personally identifiable information",
            }

        if config.transfer_initiation:
            cats["high_value_transfer"] = {
                "delta": 0.15,
                "risk_keywords": ["transfer", "wire", "swift", "ach", "high_value", "large_amount"],
                "description": "Large or bulk transfers. Requires multi-factor approval.",
            }

        return cats

    def _get_payment_categories(self, method: str) -> dict[str, Any]:
        """Get payment-method-specific categories."""
        method = method.lower()

        if method == "stripe":
            return {
                "stripe_payment_initiation": {
                    "delta": 0.3,
                    "risk_keywords": ["charge", "payment_intent", "create_charge", "stripe_charge", "capture"],
                    "description": "Stripe: Initiating customer charges",
                },
                "stripe_refund": {
                    "delta": 0.4,
                    "risk_keywords": ["refund", "create_refund", "reverse_charge", "stripe_refund"],
                    "description": "Stripe: Reversing completed transactions",
                },
                "stripe_payout": {
                    "delta": 0.2,
                    "risk_keywords": ["payout", "create_payout", "transfer_to_bank", "stripe_payout"],
                    "description": "Stripe: Moving funds to external bank accounts",
                },
            }
        elif method == "plaid":
            return {
                "plaid_auth": {
                    "delta": 0.5,
                    "risk_keywords": ["auth", "balance", "plaid_auth", "accounts_get"],
                    "description": "Plaid: Account authentication and balance retrieval",
                },
                "plaid_transfer": {
                    "delta": 0.25,
                    "risk_keywords": ["transfer", "transfer_create", "plaid_transfer", "payment_initiation"],
                    "description": "Plaid: Initiating bank transfers",
                },
            }
        elif method == "square":
            return {
                "square_payment": {
                    "delta": 0.3,
                    "risk_keywords": ["payment", "create_payment", "square_payment", "charge"],
                    "description": "Square: Processing customer payments",
                },
            }
        else:
            return {
                f"{method}_payment": {
                    "delta": 0.3,
                    "risk_keywords": ["payment", "charge", "transfer"],
                    "description": f"Custom: {method} payment processing",
                }
            }

    def _get_compliance_map(self, frameworks: list[str]) -> dict[str, Any]:
        """Get compliance control mappings."""
        mapping: dict[str, Any] = {}
        for fw in frameworks:
            fw_upper = fw.upper()
            if fw_upper == "PCI-DSS":
                mapping[fw] = {
                    "3.4": "Render PAN unreadable — Hash module ensures payload integrity",
                    "10.2": "Audit trails — AuditLogger records all gate decisions",
                    "6.5": "Address common coding vulnerabilities — Gate prevents unauthorized tool execution",
                }
            elif fw_upper == "SOX":
                mapping[fw] = {
                    "302": "Corporate responsibility — AgentStateStore tracks all decisions",
                    "404": "Internal controls — AuditLogger provides append-only decision log",
                }
            elif fw_upper == "HIPAA":
                mapping[fw] = {
                    "164.312(a)": "Access control — Gate enforces role-based tool access",
                    "164.312(b)": "Audit controls — AuditLogger records all PHI access attempts",
                }
            else:
                mapping[fw] = {"general": f"{fw} compliance controls mapped to gate decisions"}
        return mapping

    def _build_custom(self) -> dict[str, Any]:
        """Build a fully custom taxonomy via prompts."""
        print("\n--- Custom Taxonomy Builder ---")
        cats: dict[str, Any] = {}
        while True:
            name = input("Category name (or empty to finish): ").strip()
            if not name:
                break
            delta_str = input(f"  Delta for '{name}' (0.0-1.0, lower=more risky): ").strip()
            delta = float(delta_str) if delta_str else 0.5
            keywords = input("  Risk keywords (comma-separated): ").strip()
            kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
            desc = input("  Description: ").strip()
            cats[name] = {
                "delta": delta,
                "risk_keywords": kw_list,
                "description": desc or f"Custom category: {name}",
            }
        return {
            "version": "2.0-custom",
            "domain": "custom",
            "generated_by": "shadowaudit_taxonomy_builder",
            "description": "User-defined custom taxonomy",
            "categories": cats,
            "compliance_mapping": {},
        }
