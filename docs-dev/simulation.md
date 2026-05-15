# Policy Simulation Mode

Simulation tooling allows security engineers to safely test policy changes against historical traffic before enforcing them in production.

## Features
- **Replay Historical Sessions**: Feed a `session.json` or `trace.jsonl` into the simulator.
- **Compare Policy Outcomes**: Run traffic against an alternative policy and diff the outcomes.
- **Risk Delta Analysis**: Highlight where the new policy diverges from the existing one.

## CLI Commands

```bash
# Simulate a specific session trace
capfence simulate trace.jsonl

# Compare alternative policy
capfence simulate trace.jsonl --policy alternative.yaml --compare
```

The output will show deterministic comparisons, policy diffs, and simulation reporting.
