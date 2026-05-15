# CapFence benchmarks

## Scorer benchmark

`scorer_benchmark.py` compares the built-in scorers (`KeywordScorer`,
`RegexASTScorer`, `AdaptiveScorer`) on synthetic agent tool-call traces with
known ground-truth labels.

```bash
python benchmarks/scorer_benchmark.py
python benchmarks/scorer_benchmark.py --n 1000 --seed 99
```

## Reading the results — honest caveats

**These are synthetic benchmarks.** Ground-truth labels are assigned by
construction: we generate risky payloads from a fixed template set and label
them risky, then generate benign payloads from another template set and label
them benign. The benchmark therefore measures how well each scorer matches
the assumptions encoded in our synthetic generator — not real-world
detection rates against unseen agent traffic.

Use the numbers to:

- **Compare scorers against each other** under controlled conditions.
- **Detect regressions** when scoring logic changes.
- **Inform threshold defaults** for new taxonomies.

Do **not** quote the F1/TPR/FPR numbers as production performance claims.
Real-world traces — especially adversarial ones — will produce different
results. The 30-trace edge-case corpus at `tests/corpus/edge_cases.jsonl`
documents some of the failure modes (sparse keywords, AST obfuscation in
string literals, borderline thresholds).

For production calibration, run `capfence tune --audit-log audit.db`
against your real audit log after a shadow-mode rollout.
