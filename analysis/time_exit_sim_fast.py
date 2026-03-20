#!/usr/bin/env python3
"""
Optimized Time-Based Exit Simulation
Fetches tick data once per position
"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import MetaTrader5 as mt5
import gu_tools
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

def fetch_ticks_range(symbol, from_time, to_time):
    """Fetch tick data for a time range."""
    ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['price'] = (df['bid'] + df['ask']) / 2
    return df

def simulate_with_preloaded_ticks(open_price, direction, ticks_df, tp_dollars, time_limit_min):
    """
    Simulate using pre-loaded tick data.
    Returns outcome dict or None
    """
    if ticks_df.empty:
        return None
    
    tp_points = tp_dollars / 0.01
    time_limit_sec = time_limit_min * 60
    
    start_time = ticks_df['time'].iloc[0]
    end_time = start_time + timedelta(minutes=time_limit_min)
    window = ticks_df[ticks_df['time'] <= end_time].copy()
    
    if window.empty:
        return None
    
    # Calculate running PnL
    if direction == 'BUY':
        window['mfe'] = window['price'] - open_price
        window['mae'] = open_price - window['price']
        window['pnl'] = window['price'] - open_price
    else:
        window['mfe'] = open_price - window['price']
        window['mae'] = window['price'] - open_price
        window['pnl'] = open_price - window['price']
    
    # Check TP within first 60s
    first_60s = window[window['time'] <= start_time + timedelta(seconds=60)]
    tp_hit_early = (first_60s['mfe'] >= tp_points).any() if not first_60s.empty else False
    
    max_mfe = window['mfe'].max() * 0.01
    max_mae = window['mae'].max() * 0.01
    
    if tp_hit_early:
        exit_time = first_60s[first_60s['mfe'] >= tp_points].iloc[0]['time']
        exit_sec = (exit_time - start_time).total_seconds()
        return {
            'outcome': 'TP_HIT',
            'pnl_dollars': tp_dollars,
            'exit_time_seconds': exit_sec,
            'max_mfe_dollars': max_mfe,
            'max_mae_dollars': max_mae
        }
    else:
        final_pnl = window['pnl'].iloc[-1] * 0.01
        return {
            'outcome': 'TIME_EXIT',
            'pnl_dollars': final_pnl,
            'exit_time_seconds': time_limit_sec,
            'max_mfe_dollars': max_mfe,
            'max_mae_dollars': max_mae
        }

# Connect
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect')
    exit(1)

# Get positions
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
positions = gu_tools.fetch_positions(date_from, datetime.now(timezone.utc))

# Filter GU
gu_pos = [p for p in positions if str(p['magic']).startswith('282603')]

def parse_sess(magic):
    m = str(int(magic))
    sessions = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    return sessions.get(m[7] if len(m) > 7 else '0', 'UNKNOWN')

def parse_strat(magic):
    m = str(int(magic))
    strategies = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    return strategies.get(m[6] if len(m) > 6 else '0', 'UNKNOWN')

# Filter Asia
asia = [p for p in gu_pos if parse_sess(p['magic']) == 'ASIA']
for p in asia:
    p['strategy'] = parse_strat(p['magic'])

# Group by basket
asia_sorted = sorted(asia, key=lambda x: (x['magic'], x['open_time']))
baskets = []
current = None
for p in asia_sorted:
    if current is None or p['magic'] != current['magic']:
        current = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
        baskets.append(current)
    else:
        time_diff = (p['open_time'] - current['positions'][0]['open_time']).total_seconds()
        if time_diff <= 60:
            current['positions'].append(p)
        else:
            current = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
            baskets.append(current)

first_positions = [b['positions'][0] for b in baskets]

# Filter glitches
glitches = [datetime(2026, 3, 12, 5, 2, 15, tzinfo=timezone.utc), datetime(2026, 3, 12, 5, 5, 19, tzinfo=timezone.utc)]
clean_positions = [p for p in first_positions if p['open_time'] not in glitches]

print("="*100)
print("TIME-BASED EXIT SIMULATION - ASIA SESSION (Optimized)")
print("="*100)
print(f"Analyzing {len(clean_positions)} positions")

# Fetch all tick data first (30 minutes max for all positions)
print("\nFetching tick data...")
position_data = []

for i, pos in enumerate(clean_positions, 1):
    from_time = pos['open_time']
    to_time = pos['open_time'] + timedelta(minutes=30) + timedelta(seconds=10)
    
    ticks = fetch_ticks_range('XAUUSD+', from_time, to_time)
    
    if not ticks.empty:
        lot_size = pos['lot_size']
        norm_factor = lot_size * 100
        
        position_data.append({
            'pos': pos,
            'ticks': ticks,
            'norm_factor': norm_factor,
            'actual_pl_norm': pos['net_pl'] / norm_factor
        })
    
    if i % 10 == 0:
        print(f"  Fetched {i}/{len(clean_positions)}...")

print(f"Successfully loaded {len(position_data)} positions with tick data")

# TP values and time limits
tp_values = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 1.00, 1.50, 2.00]
time_limits = list(range(2, 31))

# Run simulations
all_results = []

print("\nRunning simulations...")

for tp in tp_values:
    print(f"\nTP = ${tp:.2f}")
    
    best_pnl = -999
    best_time = 0
    best_stats = None
    
    for time_limit in time_limits:
        results = []
        
        for pdata in position_data:
            pos = pdata['pos']
            ticks = pdata['ticks']
            
            result = simulate_with_preloaded_ticks(
                pos['open_price'], 
                pos['direction'], 
                ticks, 
                tp, 
                time_limit
            )
            
            if result:
                result['tp_setting'] = tp
                result['time_limit'] = time_limit
                result['actual_pl_norm'] = pdata['actual_pl_norm']
                result['strategy'] = pos['strategy']
                results.append(result)
        
        if results:
            total_pnl = sum(r['pnl_dollars'] for r in results)
            wins = sum(1 for r in results if r['outcome'] == 'TP_HIT')
            win_rate = wins / len(results) * 100
            
            if total_pnl > best_pnl:
                best_pnl = total_pnl
                best_time = time_limit
                best_stats = {
                    'trades': len(results),
                    'wins': wins,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'avg_pnl': total_pnl / len(results)
                }
            
            all_results.append({
                'tp': tp,
                'time_limit': time_limit,
                'trades': len(results),
                'tp_hits': wins,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_pnl': total_pnl / len(results) if results else 0
            })
    
    if best_stats:
        print(f"  Best: {best_time}min | WR: {best_stats['win_rate']:.1f}% | P&L: ${best_stats['total_pnl']:.2f}")

mt5.shutdown()

# Summary
print("\n" + "="*100)
print("OPTIMAL TIME LIMIT BY TARGET PROFIT")
print("="*100)

results_df = pd.DataFrame(all_results)

summary = []
for tp in tp_values:
    tp_data = results_df[results_df['tp'] == tp]
    if tp_data.empty:
        continue
    
    best_idx = tp_data['total_pnl'].idxmax()
    best = tp_data.loc[best_idx]
    
    summary.append({
        'tp': tp,
        'optimal_time': int(best['time_limit']),
        'win_rate': best['win_rate'],
        'total_pnl': best['total_pnl'],
        'avg_pnl': best['avg_pnl'],
        'tp_hits': int(best['tp_hits']),
        'trades': int(best['trades'])
    })

summary_df = pd.DataFrame(summary)

print("\nTargetProfit | Optimal Time | Win Rate | TP Hits / Total | Total P&L | Avg P&L")
print("-" * 85)
for _, row in summary_df.iterrows():
    marker = " <-- BEST" if row['total_pnl'] == summary_df['total_pnl'].max() else ""
    print(f"${row['tp']:>10.2f} | {row['optimal_time']:>12}min | {row['win_rate']:>7.1f}% | "
          f"{row['tp_hits']:>3}/{row['trades']:<3} | ${row['total_pnl']:>8.2f} | ${row['avg_pnl']:>6.2f}{marker}")

# Best overall
best = summary_df.loc[summary_df['total_pnl'].idxmax()]
print(f"\n[OPTIMAL CONFIGURATION]")
print(f"  TargetProfit: ${best['tp']:.2f}")
print(f"  Time Limit: {best['optimal_time']} minutes")
print(f"  Expected Win Rate: {best['win_rate']:.1f}%")
print(f"  Expected Total P&L: ${best['total_pnl']:.2f}")
print(f"  Expected Avg P&L: ${best['avg_pnl']:.2f}")

# Save
results_df.to_csv('time_exit_simulation_results.csv', index=False)
summary_df.to_csv('time_exit_simulation_summary.csv', index=False)
print("\n[SAVED] Results saved to CSV")
