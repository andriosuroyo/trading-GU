"""Check specific position details and lot sizes"""
import json
from datetime import datetime

with open('data/gu_positions_vantage.json', 'r') as f:
    data = json.load(f)

# Check lot size distribution
print("=" * 70)
print("LOT SIZE ANALYSIS")
print("=" * 70)

from collections import Counter
lots = [p['volume'] for p in data['closed_positions']]
lot_counts = Counter(lots)

print("\nLot size distribution:")
for lot, count in sorted(lot_counts.items()):
    pct = count / len(lots) * 100
    print(f"  {lot} lots: {count} positions ({pct:.1f}%)")

# Sample position with details
print("\n" + "=" * 70)
print("SAMPLE POSITION (First March 20 position)")
print("=" * 70)

march_20 = [p for p in data['closed_positions'] if '2026-03-20' in p['open_time']]
if march_20:
    p = march_20[0]
    print(f"Open Time: {p['open_time']}")
    print(f"Close Time: {p['close_time']}")
    print(f"Direction: {p['direction']}")
    print(f"Volume: {p['volume']} lots")
    print(f"Open Price: {p['open_price']}")
    print(f"Close Price: {p['close_price']}")
    print(f"Gross Profit: ${p['profit']:.2f}")
    print(f"Commission: ${p['commission']:.2f}")
    print(f"Net P/L: ${p['net_pl']:.2f}")
    print(f"Duration: {p['duration_minutes']:.1f} minutes")
    
    # Normalized to 0.01 lot
    norm_pl = p['net_pl'] / (p['volume'] * 100)
    print(f"\nNormalized to 0.01 lot: ${norm_pl:.2f}")

# Find 23:32 position
print("\n" + "=" * 70)
print("SEARCHING FOR 23:32:00 POSITION")
print("=" * 70)

target = None
for p in data['closed_positions']:
    if '2026-03-20T23:32' in p['open_time']:
        target = p
        break

if target:
    print("Found:")
    for k, v in target.items():
        print(f"  {k}: {v}")
else:
    print("Not found. Positions around 23:30-23:35:")
    for p in data['closed_positions']:
        if '2026-03-20T23:3' in p['open_time']:
            open_time = datetime.fromisoformat(p['open_time'])
            print(f"  {open_time.strftime('%H:%M:%S')}: {p['direction']} {p['volume']} lots @ {p['open_price']} -> {p['close_price']}")
