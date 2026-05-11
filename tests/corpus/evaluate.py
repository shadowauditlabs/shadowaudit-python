"""Evaluate ShadowAudit gate against the public test corpus.

Runs all three corpus files through Gate.evaluate() and reports
accuracy, false positive rate, and any mismatches vs expected labels.

Run:
    python tests/corpus/evaluate.py
    python tests/corpus/evaluate.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shadowaudit import Gate


CORPUS_DIR = Path(__file__).parent
CORPUS_FILES = [
    ("benign_traces.jsonl", "Benign traces (should all PASS)"),
    ("risky_traces.jsonl", "Risky traces (should all BLOCK)"),
    ("edge_cases.jsonl", "Edge cases (mixed, check notes)"),
]


def evaluate_file(
    corpus_path: Path,
    label: str,
    verbose: bool,
) -> tuple[int, int, list[dict]]:
    """Evaluate a corpus file and return (correct, total, mismatches)."""
    mismatches: list[dict] = []
    correct = 0
    total = 0

    # Group by taxonomy so we can reuse Gate instances
    traces_by_taxonomy: dict[str, list[dict]] = {}
    with open(corpus_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            trace = json.loads(line)
            tax = trace["taxonomy"]
            traces_by_taxonomy.setdefault(tax, []).append(trace)

    for taxonomy, traces in sorted(traces_by_taxonomy.items()):
        gate = Gate(taxonomy_path=taxonomy)

        for trace in traces:
            result = gate.evaluate(
                agent_id="corpus-evaluator",
                task_context=trace["risk_category"],
                risk_category=trace["risk_category"],
                payload=trace["payload"],
            )
            total += 1
            expected_block = trace["expected"] == "block"
            actual_block = not result.passed

            if expected_block == actual_block:
                correct += 1
                if verbose:
                    status = "✓"
                    print(f"  {status} {trace['id']:<15} expected={trace['expected']:<8} "
                          f"score={result.risk_score:.3f} threshold={result.threshold:.3f}")
            else:
                mismatch = {
                    "id": trace["id"],
                    "expected": trace["expected"],
                    "actual": "block" if actual_block else "pass",
                    "risk_score": result.risk_score,
                    "threshold": result.threshold,
                    "notes": trace.get("notes", ""),
                }
                mismatches.append(mismatch)
                marker = "✗"
                print(f"  {marker} {trace['id']:<15} expected={trace['expected']:<8} "
                      f"got={'block' if actual_block else 'pass':<8} "
                      f"score={result.risk_score:.3f} threshold={result.threshold:.3f}")
                if verbose:
                    print(f"    notes: {trace.get('notes', '')}")

    return correct, total, mismatches


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ShadowAudit test corpus")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all traces, not just mismatches")
    parser.add_argument("--file", "-f", type=str, default=None,
                        help="Evaluate only this corpus file")
    args = parser.parse_args()

    print("ShadowAudit Corpus Evaluation")
    print("=" * 60)

    total_correct = 0
    total_traces = 0
    all_mismatches: list[dict] = []

    files_to_run = [(f, label) for f, label in CORPUS_FILES
                    if args.file is None or f == args.file]

    for filename, label in files_to_run:
        path = CORPUS_DIR / filename
        if not path.exists():
            print(f"\n[SKIP] {filename} not found.")
            continue

        print(f"\n{label}")
        print("-" * 60)
        correct, total, mismatches = evaluate_file(path, label, args.verbose)
        accuracy = correct / total if total > 0 else 0

        print(f"\n  Correct: {correct}/{total} ({accuracy:.0%})")
        if mismatches:
            print(f"  Mismatches: {len(mismatches)}")

        total_correct += correct
        total_traces += total
        all_mismatches.extend(mismatches)

    print()
    print("=" * 60)
    overall = total_correct / total_traces if total_traces > 0 else 0
    print(f"Overall: {total_correct}/{total_traces} ({overall:.0%})")
    print(f"Mismatches: {len(all_mismatches)}")

    if all_mismatches:
        print()
        print("NOTE: Some mismatches are expected — edge cases document known")
        print("limitations (false negatives, boundary conditions). Review the")
        print("'notes' field in each trace for the intended behavior.")
        print()
        print("To understand false negatives, read docs/THREAT_MODEL.md.")

    # Exit 1 if unexpected mismatches in benign or risky (not edge_cases)
    critical_mismatches = [m for m in all_mismatches
                           if not m["id"].startswith("edge_")]
    if critical_mismatches:
        print()
        print(f"CRITICAL: {len(critical_mismatches)} non-edge-case mismatches.")
        sys.exit(1)


if __name__ == "__main__":
    main()
