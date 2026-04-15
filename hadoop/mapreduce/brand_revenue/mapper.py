#!/usr/bin/env python3
"""Mapper: emit brand, price for each purchase record."""
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split(",")
    if len(parts) < 2:
        continue
    brand = parts[0].strip()
    price = parts[1].strip()
    if brand and price:
        print(f"{brand}\t{price}")
