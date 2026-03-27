"""Analyze March 20, 2026 GU positions"""
import json
from datetime import datetime
from collections import defaultdict

with open('data/gu_positions_vantage.json', 'r') as f:
    data = json.load(f)

# Get March 20 positions
march_20 = []
for p in data['closed_positions']:
    open_time = datetime.fromisoformat(p['open_time'])
    if open_time.date().day == 20 and open_time.date().month == 3:
        march_20.append(p)

print("=" * 70)
print("MARCH 20, 2026 - GU POSITION ANALYSIS")
print("=" * 70)
print(f"Total positions: {len(march_20)}")

# Overall stats
total_gross = sum(p['profit'] for p in march_20)
total_net = sum(p['net_pl'] for p in march_20)
total_comm = sum(p['commission'] for p in march_20)
total_swap = sum(p['swap'] for p in march_20)
winners = sum(1 for p in march_20 if p['net_pl'] > 0)
losers = len(march_20) - winners

print(f"\nOverall P&L:")
print(f"  Gross Profit: ${total_gross:,.2f}")
print(f"  Commission: ${total_comm:,.2f}")
print(f"  Swap: ${total_swap:,.2f}")
print(f"  Net P/L: ${total_net:,.2f}")
print(f"  Win Rate: {winners}/{len(march_20)} ({winners/len(march_20)*100:.1f}%)")

# By session
by_session = defaultdict(list)
for p in march_20:
    by_session[p['session']].append(p)

print(f"\nBy Session:")
print(f"{'Session':<10} {'Count':>6} {'Net P/L':>12} {'Win Rate':>10} {'Avg Duration':>12}")
print("-" * 70)
for session, positions in sorted(by_session.items()):
    net = sum(p['net_pl'] for p in positions)
    wins = sum(1 for p in positions if p['net_pl'] > 0)
    avg_dur = sum(p['duration_minutes'] for p in positions) / len(positions)
    print(f"{session:<10} {len(positions):>6} ${net:>10,.2f} {wins/len(positions)*100:>9.0f}% {avg_dur:>11.1f}m")

# Show first 15 positions
print(f"\nFirst 15 Positions (chronological):")
print(f"{'Time':<12} {'Dir':<5} {'Entry':>8} {'Exit':>8} {'P/L':>8} {'Duration':>10} {'Comment':<25}")
print("-" * 95)
for p in march_20[:15]:
    open_time = datetime.fromisoformat(p['open_time'])
    time_str = open_time.strftime('%H:%M:%S')
    comment = p['comment'][:25] if p['comment'] else ''
    print(f"{time_str:<12} {p['direction']:<5} {p['open_price']:>8.2f} {p['close_price']:>8.2f} ${p['net_pl']:>7.2f} {p['duration_minutes']:>9.1f}m {comment:<25}")

# Distribution of P/L
print(f"\nP/L Distribution:")
profit_ranges = [
    (float('-inf'), -10, "Large Loss (<-$10)"),
    (-10, -5, "Medium Loss (-$5 to -$10)"),
    (-5, 0, "Small Loss (-$5 to $0)"),
    (0, 5, "Small Win ($0 to $5)"),
    (5, 10, "Medium Win ($5 to $10)"),
    (10, float('inf'), "Large Win (>$10)")
]

for min_val, max_val, label in profit_ranges:
    count = sum(1 for p in march_20 if min_val <= p['net_pl'] < max_val)
    pct = count / len(march_20) * 100
    bar = "#" * int(pct / 2)
    print(f"  {label:<25}: {count:>3} ({pct:>5.1f}%) {bar}")

# Magic number analysis
by_magic = defaultdict(list)
for p in march_20:
    by_magic[p['magic']].append(p)

print(f"\nBy Magic Number:")
print(f"{'Magic':<12} {'Count':>6} {'Net P/L':>12} {'Win Rate':>10}")
print("-" * 50)
for magic, positions in sorted(by_magic.items()):
    net = sum(p['net_pl'] for p in positions)
    wins = sum(1 for p in positions if p['net_pl'] > 0)
    print(f"{magic:<12} {len(positions):>6} ${net:>10,.2f} {wins/len(positions)*100:>9.0f}%")
