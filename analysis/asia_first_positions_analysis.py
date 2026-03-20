#!/usr/bin/env python3
"""Detailed analysis of ASIA session first positions"""
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

# Filter for GU magics only
gu_positions = [p for p in positions if str(p['magic']).startswith('282603')]

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

# Identify baskets and their positions
# Group by magic + time window (within 60 seconds = same basket)
asia_sorted = sorted(asia_positions, key=lambda x: (x['magic'], x['open_time']))

baskets = []
current_basket = None

for p in asia_sorted:
    if current_basket is None or p['magic'] != current_basket['magic']:
        # New basket
        current_basket = {
            'magic': p['magic'],
            'strategy': p['strategy'],
            'positions': [p]
        }
        baskets.append(current_basket)
    else:
        # Check if within 60 seconds of first position in basket
        first_time = current_basket['positions'][0]['open_time']
        time_diff = (p['open_time'] - first_time).total_seconds()
        if time_diff <= 60:
            current_basket['positions'].append(p)
        else:
            # New basket
            current_basket = {
                'magic': p['magic'],
                'strategy': p['strategy'],
                'positions': [p]
            }
            baskets.append(current_basket)

print('='*120)
print('ASIA SESSION - ALL FIRST POSITIONS OF EACH BASKET')
print('='*120)
print(f'{"Basket #":<10} {"Date":<12} {"Time (UTC)":<12} {"Strategy":<8} {"Magic":<12} {"Dir":<6} {"Price":<10} {"P/L ($)":<10} {"Notes":<20}')
print('-'*120)

first_positions = []
for i, basket in enumerate(baskets, 1):
    first_pos = basket['positions'][0]
    first_positions.append(first_pos)
    
    date_str = first_pos['open_time'].strftime('%Y-%m-%d')
    time_str = first_pos['open_time'].strftime('%H:%M:%S')
    magic_str = str(first_pos['magic'])
    pl_str = f"{first_pos['net_pl']:.2f}"
    price_str = f"{first_pos['open_price']:.2f}"
    
    notes = ""
    if len(basket['positions']) > 1:
        other_dirs = [p['direction'] for p in basket['positions'][1:]]
        notes = f"+{len(basket['positions'])-1} pos ({','.join(other_dirs)})"
    
    print(f"{i:<10} {date_str:<12} {time_str:<12} {first_pos['strategy']:<8} {magic_str:<12} {first_pos['direction']:<6} {price_str:<10} {pl_str:<10} {notes:<20}")

print('-'*120)
print(f'Total baskets: {len(baskets)}')
print(f'First positions: {len(first_positions)}')

# Check for multi-position baskets
multi_pos_baskets = [b for b in baskets if len(b['positions']) > 1]
print(f'\nMulti-position baskets: {len(multi_pos_baskets)}')

if multi_pos_baskets:
    print('\n--- Multi-Position Basket Details ---')
    for basket in multi_pos_baskets:
        print(f"\nBasket: Magic {basket['magic']} ({basket['strategy']})")
        for j, pos in enumerate(basket['positions'], 1):
            pos_time = pos['open_time'].strftime('%H:%M:%S')
            print(f"  Pos {j}: {pos_time} {pos['direction']} @ {pos['open_price']:.2f} -> ${pos['net_pl']:.2f}")

# Summary stats for FIRST positions only
print('\n' + '='*80)
print('SUMMARY: FIRST POSITIONS ONLY')
print('='*80)

wins = len([p for p in first_positions if p['net_pl'] > 0])
losses = len([p for p in first_positions if p['net_pl'] < 0])
total_pl = sum(p['net_pl'] for p in first_positions)
win_rate = wins / len(first_positions) * 100 if first_positions else 0

print(f'Total first positions: {len(first_positions)}')
print(f'Wins: {wins} ({win_rate:.1f}%)')
print(f'Losses: {losses}')
print(f'Total P/L: ${total_pl:.2f}')

# By strategy
print('\n--- By Strategy ---')
for strat in ['MH', 'HR05', 'HR10']:
    strat_pos = [p for p in first_positions if p['strategy'] == strat]
    if strat_pos:
        strat_wins = len([p for p in strat_pos if p['net_pl'] > 0])
        strat_pl = sum(p['net_pl'] for p in strat_pos)
        strat_wr = strat_wins / len(strat_pos) * 100
        print(f'{strat}: {len(strat_pos)} trades, {strat_wins} wins ({strat_wr:.1f}%), ${strat_pl:.2f} P/L')

# Check for "glitch" simultaneous BUY/SELL
print('\n--- Glitch Detection (Simultaneous BUY/SELL) ---')
glitches = []
for basket in baskets:
    if len(basket['positions']) >= 2:
        # Check if BUY and SELL at same time
        directions = [p['direction'] for p in basket['positions']]
        if 'BUY' in directions and 'SELL' in directions:
            # Check if same timestamp
            times = [p['open_time'] for p in basket['positions']]
            if len(set(times)) < len(times):  # Duplicate times
                glitches.append(basket)

if glitches:
    print(f'FOUND {len(glitches)} GLITCH BASKETS (simultaneous BUY/SELL):')
    for g in glitches:
        print(f"  Magic {g['magic']} at {g['positions'][0]['open_time']}")
else:
    print('No glitch baskets found')
