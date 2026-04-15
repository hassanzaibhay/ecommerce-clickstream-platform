#!/usr/bin/env python3
"""Reducer: sum event counts per (category, event_type)."""
import sys
from collections import defaultdict

counts: dict[tuple[str, str], int] = defaultdict(int)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split("\t")
    if len(parts) != 3:
        continue
    category, event_type, count_str = parts
    try:
        counts[(category, event_type)] += int(count_str)
    except ValueError:
        continue

for (category, event_type), count in sorted(counts.items()):
    print(f"{category}\t{event_type}\t{count}")
