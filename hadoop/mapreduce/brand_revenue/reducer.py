#!/usr/bin/env python3
"""Reducer: sum revenue and count purchases per brand."""
import sys
from collections import defaultdict

revenue: dict[str, float] = defaultdict(float)
counts: dict[str, int] = defaultdict(int)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split("\t")
    if len(parts) != 2:
        continue
    brand, price_str = parts
    try:
        revenue[brand] += float(price_str)
        counts[brand] += 1
    except ValueError:
        continue

for brand in sorted(revenue.keys()):
    print(f"{brand}\t{revenue[brand]:.2f}\t{counts[brand]}")
