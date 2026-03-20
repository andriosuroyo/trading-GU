#!/usr/bin/env python3
"""
Low TargetProfit Simulation
Testing TP values below $0.20 since max MFE is only $0.03
"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import MetaTrader5 as mt5
import gu_tools
from datetime import datetime, timezone, timedelta
import pandas as pd

def fetch_ticks(symbol, from_time, to_time):
    ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['price'] = (df['bid'] + df['ask']) / 2
    return df

def simulate(open_price, direction, ticks_df, tp_dollars, time_limit_min):
    if ticks_df.empty:
        return None
    
    tp_points = tp_dollars / 0.01
    start_time = ticks_df['time'].iloc[0]
    end_time = start_time + timedelta(minutes=time_limit_min)
    window = ticks_df[ticks_df['time'] <= end_time].copy()
    
    if window.empty:
        return None
    
    if direction == 'BUY':
        window['mfe'] = window['price'] - open_price
        window['pnl'] = window['price'] - open_price
    else:
        window['mfe'] = open_price - window['price']
        window['pnl'] = open_price - window['price']
    
    # Check if TP hit
    tp_hit = (window['mfe'] >= tp_points).any()
    
    if tp_hit:
        pnl = tp_dollars
        outcome = 'TP_HIT'
    else:
        pnl = window['pnl'].iloc[-1] * 0.01
        outcome = 'TIME_EXIT'
    
    return {'outcome': outcome, 'pnl': pnl}

# Connect
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    exit(1)

# Get Asia first positions
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
positions = gu_tools.fetch_positions(date_from, datetime.now(timezone.utc))

# Filter
def parse_sess(m):
    sess = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    return sess.get(str(int(m))[7] if len(str(int(m))) > 7 else '0', 'UNKNOWN')

def parse_strat(m):
    strat = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    return strat.get(str(int(m))[6] if len(str(int(m))) > 6 else '0', 'UNKNOWN')

asia = [p for p in positions if str(p['magic']).startswith('282603') and parse_sess(p['magic']) == 'ASIA']
for p in asia:
    p['strategy'] = parse_strat(p['magic'])

# Group baskets
asia_sorted = sorted(asia, key=lambda x: (x['magic'], x['open_time']))
baskets = []
current = None
for p in asia_sorted:
    if current is None or p['magic'] != current['magic']:
        current = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
        baskets.append(current)
    else:
        if (p['open_time'] - current['positions'][0]['open_time']).total_seconds() <= 60:
            current['positions'].append(p)
        else:
            current = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
            baskets.append(current)

first_pos = [b['positions'][0] for b in baskets]
glitches = [datetime(2026, 3, 12, 5, 2, 15, tzinfo=timezone.utc), datetime(2026, 3, 12, 5, 5, 19, tzinfo=timezone.utc)]
clean = [p for p in first_pos if p['open_time'] not in glitches]

print("="*80)
print("LOW TP SIMULATION - Asia Session")
print("="*80)
print(f"Testing {len(clean)} positions")

# Fetch tick data
print("\nFetching tick data...")
pos_data = []
for pos in clean:
    ticks = fetch_ticks('XAUUSD+', pos['open_time'], pos['open_time'] + timedelta(minutes=30))
    if not ticks.empty:
        norm = pos['lot_size'] * 100
        pos_data.append({
            'pos': pos,
            'ticks': ticks,
            'actual_norm': pos['net_pl'] / norm
        })

print(f"Loaded {len(pos_data)} positions")

# Test low TP values
tp_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15]
time_limits = [2, 3, 5, 10, 15, 20, 30]

print("\n" + "-"*80)
print("RESULTS: TargetProfit vs Time Limit")
print("-"*80)
print(f"{'TP':>8} | {'Time':>6} | {'Win%':>6} | {'TP Hits':>8} | {'Total P&L':>10} | {'vs Actual':>10}")
print("-"*80)

results = []
actual_total = sum(p['actual_norm'] for p in pos_data)

for tp in tp_values:
    for tl in time_limits:
        sim_results = []
        for pdata in pos_data:
            r = simulate(pdata['pos']['open_price'], pdata['pos']['direction'], pdata['ticks'], tp, tl)
            if r:
                sim_results.append(r)
        
        if sim_results:
            wins = sum(1 for r in sim_results if r['outcome'] == 'TP_HIT')
            total_pnl = sum(r['pnl'] for r in sim_results)
            wr = wins / len(sim_results) * 100
            vs_actual = total_pnl - actual_total
            
            results.append({
                'tp': tp, 'time': tl, 'win_rate': wr, 
                'tp_hits': wins, 'total': len(sim_results),
                'pnl': total_pnl, 'vs_actual': vs_actual
            })

# Print results
for r in results:
    marker = ""
    if r['vs_actual'] > 0 and r['vs_actual'] == max(x['vs_actual'] for x in results if x['tp'] == r['tp']):
        marker = " *"
    print(f"${r['tp']:>6.2f} | {r['time']:>5}m | {r['win_rate']:>5.1f}% | {r['tp_hits']:>3}/{r['total']:<3} | ${r['pnl']:>8.2f} | ${r['vs_actual']:>+8.2f}{marker}")

# Best by TP
print("\n" + "="*80)
print("OPTIMAL TIME LIMIT BY TARGET PROFIT")
print("="*80)

df = pd.DataFrame(results)
for tp in tp_values:
    tp_df = df[df['tp'] == tp]
    if tp_df.empty:
        continue
    best = tp_df.loc[tp_df['pnl'].idxmax()]
    print(f"TP ${tp:.2f}: {best['time']:.0f}min | WR {best['win_rate']:.1f}% | P&L ${best['pnl']:.2f}")

# Best overall
best = df.loc[df['pnl'].idxmax()]
print(f"\n[BEST OVERALL]")
print(f"TP: ${best['tp']:.2f}, Time: {best['time']:.0f}min")
print(f"Win Rate: {best['win_rate']:.1f}%, P&L: ${best['pnl']:.2f}")
print(f"vs Actual: ${best['vs_actual']:+.2f}")

# Compare to actual
print(f"\nActual Performance: ${actual_total:.2f} ({len(pos_data)} trades)")
print(f"Best Simulated: ${best['pnl']:.2f}")
if best['pnl'] > actual_total:
    print(f"Improvement: +${best['pnl'] - actual_total:.2f} (+{(best['pnl']/actual_total-1)*100:.1f}%)")
else:
    print(f"Current trailing stop is BETTER by ${actual_total - best['pnl']:.2f}")

mt5.shutdown()
