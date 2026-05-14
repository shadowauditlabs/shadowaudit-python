#!/usr/bin/env python3
"""Stretch an asciinema cast file by scaling timestamps and adding minimum delays."""

import json
import sys
from pathlib import Path

def fix_cast_speed(cast_path: str, nonzero_multiplier: float = 3.0, min_delay: float = 0.35):
    p = Path(cast_path)
    lines = p.read_text().splitlines()
    if not lines:
        sys.exit("Empty cast file")

    out_lines = [lines[0]]  # header stays unchanged

    for raw in lines[1:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue

        delta = event[0]
        if delta == 0:
            event[0] = min_delay
        else:
            event[0] = round(delta * nonzero_multiplier, 3)

        out_lines.append(json.dumps(event, ensure_ascii=False))

    p.write_text("\n".join(out_lines) + "\n")

    # Report total duration
    total = sum(json.loads(line)[0] for line in out_lines[1:])
    print(f"Fixed {cast_path}: total duration now ~{total:.1f}s")

if __name__ == "__main__":
    fix_cast_speed("docs/examples/demo.cast")
