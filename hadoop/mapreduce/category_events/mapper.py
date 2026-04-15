#!/usr/bin/env python3
"""Mapper: emit category, event_type, 1 for each record."""
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split(",")
    if len(parts) < 2:
        continue
    category = parts[0].strip()
    event_type = parts[1].strip()
    if category and event_type:
        print(f"{category}\t{event_type}\t1")
