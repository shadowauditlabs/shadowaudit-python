"""Test runner for all v0.4.0 examples.

Runs each example and reports success/failure.
Usage: python examples/run_all_examples.py
"""

import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = [
    ("Hash Chain (Week 7a)", "hash_chain_demo.py"),
    ("Ed25519 Signing (Week 7b)", "ed25519_signing_demo.py"),
    ("OWASP Report (Week 8)", "owasp_report_demo.py"),
    ("MCP Gateway (Week 9)", "mcp_gateway_demo.py"),
    ("LangGraph (Week 10)", "langgraph_demo.py"),
    ("OpenAI Agents (Week 10)", "openai_agents_demo.py"),
    ("EU AI Act (Week 11)", "eu_ai_act_demo.py"),
    ("Plaid Taxonomy (Week 12)", "plaid_taxonomy_demo.py"),
    ("Telemetry (Week 13)", "telemetry_demo.py"),
]


def run_example(name: str, filename: str) -> bool:
    """Run a single example and return success status."""
    path = Path(__file__).parent / filename
    print(f"\n{'=' * 60}")
    print(f"Running: {name}")
    print(f"File:    {filename}")
    print("=" * 60)

    # Allow examples to import shadowaudit from the repo root without pip install
    env = os.environ.copy()
    repo_root = str(Path(__file__).parent.parent.resolve())
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    success = result.returncode == 0
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} (exit code: {result.returncode})")
    return success


def main():
    print("ShadowAudit v0.4.0 Example Test Runner")
    print(f"Python: {sys.version}")

    passed = 0
    failed = 0

    for name, filename in EXAMPLES:
        if run_example(name, filename):
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(EXAMPLES)}")
    print(f"Failed: {failed}/{len(EXAMPLES)}")

    if failed > 0:
        sys.exit(1)
    print("\nAll examples ran successfully!")


if __name__ == "__main__":
    main()
