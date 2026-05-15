"""Example: Plaid taxonomy pack (Week 12).

Demonstrates the Plaid-specific risk taxonomy for fintech agents.
"""

from capfence.core.taxonomy import TaxonomyLoader


def main():
    # Load the Plaid taxonomy
    taxonomy = TaxonomyLoader.load("financial_plaid")

    print("Plaid Taxonomy Pack")
    print("=" * 50)
    print(f"Domain:     {taxonomy['domain']}")
    print(f"Version:    {taxonomy['version']}")
    print(f"Categories: {len(taxonomy['categories'])}")
    print()

    # Print all categories with risk levels
    print(f"{'Category':<25} {'Delta':<8} {'Risk Level':<12} {'Keywords'}")
    print("-" * 80)
    for name, config in taxonomy["categories"].items():
        delta = config.get("delta", 1.0)
        level = "LOW" if delta >= 0.8 else "MEDIUM" if delta >= 0.5 else "HIGH" if delta >= 0.3 else "CRITICAL"
        keywords = ", ".join(config.get("risk_keywords", [])[:3]) + "..."
        print(f"{name:<25} {delta:<8.1f} {level:<12} {keywords}")

    # Show specific examples
    print("\nExamples:")
    transfer = taxonomy["categories"]["plaid_transfer"]
    print(f"  plaid_transfer (delta={transfer['delta']}):")
    print(f"    Keywords: {transfer['risk_keywords']}")
    print(f"    Description: {transfer['description']}")

    balance = taxonomy["categories"]["plaid_balance"]
    print(f"\n  plaid_balance (delta={balance['delta']}):")
    print(f"    Keywords: {balance['risk_keywords']}")
    print(f"    Description: {balance['description']}")


if __name__ == "__main__":
    main()
