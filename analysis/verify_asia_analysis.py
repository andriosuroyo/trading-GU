#!/usr/bin/env python3
"""Verify Asia session analysis - list all first positions"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import gu_tools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Connect to Vantage
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect')
    exit(1)

# Fetch positions from March 1 onwards
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
date_to = datetime.now(timezone.utc)
positions = gu_tools.fetch_positions(date_from, date_to)
gu_tools.mt5.shutdown()

print(f'Total positions fetched: {len(positions)}')

# Filter for GU magics only
gu_positions = [p for p in positions if str(p['magic']).startswith('282603')]
print(f'GU positions (282603xx): {len(gu_positions)}')

# Parse strategy and session
def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): return 'UNKNOWN', 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    session_id = m[7] if len(m) > 7 else '0'
    
    strategies = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    sessions = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    
    return strategies.get(strat_id, f'STRAT_{strat_id}'), sessions.get(session_id, f'SESS_{session_id}')

for p in gu_positions:
    strat, sess = parse_magic(p['magic'])
    p['strategy'] = strat
    p['session'] = sess
    p['date'] = p['open_time'].date()
    p['hour'] = p['open_time'].hour

# Filter for ASIA session only
asia_positions = [p for p in gu_positions if p['session'] == 'ASIA']
print(f'\nASIA session positions: {len(asia_positions)}')

# Group by date and count
by_date = defaultdict(int)
for p in asia_positions:
    by_date[p['date']] += 1

print('\nASIA positions by date:')
for date in sorted(by_date.keys()):
    print(f'  {date}: {by_date[date]} positions')

# Check for simultaneous positions (same magic, within 5 seconds)
print('\n--- Checking for simultaneous positions ---')
simultaneous = []
asia_sorted = sorted(asia_positions, key=lambda x: (x['magic'], x['open_time']))

for i in range(len(asia_sorted) - 1):
    curr = asia_sorted[i]
    next_p = asia_sorted[i + 1]
    
    if curr['magic'] == next_p['magic']:
        time_diff = (next_p['open_time'] - curr['open_time']).total_seconds()
        if time_diff <= 5:  # Within 5 seconds
            simultaneous.append((curr, next_p, time_diff))

if simultaneous:
    print(f'Found {len(simultaneous)} pairs of simultaneous positions:')
    for curr, next_p, diff in simultaneous[:10]:
        t1 = curr['open_time'].strftime('%Y-%m-%d %H:%M:%S')
        print(f'  {t1} - Magic {curr["magic"]} - {diff:.1f}s apart')
else:
    print('No simultaneous positions found (all baskets appear to be single-position)')

# List ALL Asia positions with details
print('\n' + '='*100)
print('ALL ASIA SESSION POSITIONS (First Position of Each Basket)')
print('='*100)
print(f'{"#":<4} {"Date":<12} {"Time (UTC)":<12} {"Strategy":<8} {"Magic":<12} {"Direction":<8} {"Price":<10} {"P/L ($)":<10}')
print('-'*100)

# Sort by open time
asia_sorted = sorted(asia_positions, key=lambda x: x['open_time'])

for i, p in enumerate(asia_sorted, 1):
    date_str = p['open_time'].strftime('%Y-%m-%d')
    time_str = p['open_time'].strftime('%H:%M:%S')
    magic_str = str(p['magic'])
    pl_str = f"{p['net_pl']:.2f}"
    price_str = f"{p['open_price']:.2f}"
    
    print(f"{i:<4} {date_str:<12} {time_str:<12} {p['strategy']:<8} {magic_str:<12} {p['direction']:<8} {price_str:<10} {pl_str:<10}")

print('-'*100)
print(f'Total: {len(asia_sorted)} positions')

# Summary by strategy
print('\n--- Summary by Strategy ---')
for strat in ['MH', 'HR05', 'HR10', 'TESTS']:
    strat_pos = [p for p in asia_positions if p['strategy'] == strat]
    if strat_pos:
        total_pl = sum(p['net_pl'] for p in strat_pos)
        wins = len([p for p in strat_pos if p['net_pl'] > 0])
        print(f'{strat}: {len(strat_pos)} trades, {wins} wins, ${total_pl:.2f} P/L')
