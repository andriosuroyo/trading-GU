#!/usr/bin/env python3
"""
Time-Based Exit Simulation for Asia Session
Tracks price path to determine if TP is hit before time limit
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

def simulate_position(open_price, direction, ticks_df, tp_dollars, time_limit_min):
    """
    Simulate a position with time-based exit.
    
    Rules:
    - If TP reached within first 60s → Take profit at TP
    - If TP not reached by time_limit → Exit at market price
    - TP in dollars for 0.01 lot (e.g., $0.20 = 20 points)
    
    Returns: {
        'outcome': 'TP_HIT' or 'TIME_EXIT',
        'pnl_dollars': float,
        'exit_time_seconds': int,
        'max_mfe_dollars': float,
        'max_mae_dollars': float
    }
    """
    if ticks_df.empty:
        return None
    
    tp_points = tp_dollars / 0.01  # Convert dollars to points
    time_limit_sec = time_limit_min * 60
    
    # Filter ticks within time limit
    start_time = ticks_df['time'].iloc[0]
    end_time = start_time + timedelta(minutes=time_limit_min)
    window = ticks_df[ticks_df['time'] <= end_time].copy()
    
    if window.empty:
        return None
    
    # Calculate running MFE/MAE and check for TP
    if direction == 'BUY':
        window['mfe'] = window['price'] - open_price
        window['mae'] = open_price - window['price']
        window['pnl'] = window['price'] - open_price
    else:  # SELL
        window['mfe'] = open_price - window['price']
        window['mae'] = window['price'] - open_price
        window['pnl'] = open_price - window['price']
    
    # Check if TP hit within first 60 seconds
    first_60s = window[window['time'] <= start_time + timedelta(seconds=60)]
    tp_hit_early = (first_60s['mfe'] >= tp_points).any() if not first_60s.empty else False
    
    max_mfe = window['mfe'].max() * 0.01  # Convert to dollars
    max_mae = window['mae'].max() * 0.01
    
    if tp_hit_early:
        # TP hit within 60s
        return {
            'outcome': 'TP_HIT',
            'pnl_dollars': tp_dollars,
            'exit_time_seconds': first_60s[first_60s['mfe'] >= tp_points].iloc[0]['time'].timestamp() - start_time.timestamp(),
            'max_mfe_dollars': max_mfe,
            'max_mae_dollars': max_mae
        }
    else:
        # Exit at time limit (last tick price)
        final_pnl = window['pnl'].iloc[-1] * 0.01
        return {
            'outcome': 'TIME_EXIT',
            'pnl_dollars': final_pnl,
            'exit_time_seconds': time_limit_sec,
            'max_mfe_dollars': max_mfe,
            'max_mae_dollars': max_mae
        }

# Connect to MT5
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect')
    exit(1)

# Get positions
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
positions = gu_tools.fetch_positions(date_from, datetime.now(timezone.utc))

# Filter GU Asia
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
asia = []
for p in gu_pos:
    if parse_sess(p['magic']) == 'ASIA':
        p['strategy'] = parse_strat(p['magic'])
        asia.append(p)

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
print("TIME-BASED EXIT SIMULATION - ASIA SESSION")
print("="*100)
print(f"\nSimulating {len(clean_positions)} first positions")
print("Rule: TP hit in first 60s = WIN, otherwise exit at time limit")
print()

# TargetProfit values to test
# From MFE analysis, max MFE was ~$0.03, but actual P&L reached $1.79
# So we need to test reasonable TP values
tp_values = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 1.00, 1.50, 2.00]

# Time limits to test (2 to 30 minutes)
time_limits = list(range(2, 31))

# Store results
all_results = []

for tp in tp_values:
    print(f"\nTesting TargetProfit = ${tp:.2f}")
    print("-" * 80)
    
    tp_results = []
    
    for time_limit in time_limits:
        position_results = []
        
        for pos in clean_positions:
            # Fetch ticks from open to time_limit (+ buffer)
            from_time = pos['open_time']
            to_time = pos['open_time'] + timedelta(minutes=time_limit) + timedelta(seconds=10)
            
            ticks = fetch_ticks_range('XAUUSD+', from_time, to_time)
            
            if ticks.empty:
                continue
            
            # Normalize lot size
            lot_size = pos['lot_size']
            norm_factor = lot_size * 100
            tp_normalized = tp  # Already for 0.01 lot
            
            result = simulate_position(pos['open_price'], pos['direction'], ticks, tp_normalized, time_limit)
            
            if result:
                result['pos_id'] = pos['pos_id']
                result['strategy'] = pos['strategy']
                result['tp_setting'] = tp
                result['time_limit'] = time_limit
                result['actual_pl_norm'] = pos['net_pl'] / norm_factor
                position_results.append(result)
        
        if position_results:
            df = pd.DataFrame(position_results)
            
            tp_hits = (df['outcome'] == 'TP_HIT').sum()
            time_exits = (df['outcome'] == 'TIME_EXIT').sum()
            total_pnl = df['pnl_dollars'].sum()
            win_rate = tp_hits / len(df) * 100
            
            tp_results.append({
                'tp': tp,
                'time_limit': time_limit,
                'total_trades': len(df),
                'tp_hits': tp_hits,
                'time_exits': time_exits,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_pnl': total_pnl / len(df),
                'avg_mfe': df['max_mfe_dollars'].mean(),
                'avg_mae': df['max_mae_dollars'].mean()
            })
            
            all_results.extend(position_results)
    
    # Summary for this TP
    if tp_results:
        tp_df = pd.DataFrame(tp_results)
        best = tp_df.loc[tp_df['total_pnl'].idxmax()]
        
        print(f"  Best time limit: {best['time_limit']:.0f} minutes")
        print(f"  Win rate: {best['win_rate']:.1f}% ({best['tp_hits']:.0f}/{best['total_trades']:.0f})")
        print(f"  Total P&L: ${best['total_pnl']:.2f}")
        print(f"  Avg P&L per trade: ${best['avg_pnl']:.2f}")

mt5.shutdown()

# Save all results
results_df = pd.DataFrame(all_results)
if not results_df.empty:
    results_df.to_csv('time_exit_simulation_detailed.csv', index=False)

# Create summary table
print("\n" + "="*100)
print("SUMMARY: OPTIMAL TIME LIMIT BY TARGET PROFIT")
print("="*100)

summary_rows = []
for tp in tp_values:
    tp_data = [r for r in all_results if r['tp_setting'] == tp]
    if not tp_data:
        continue
    
    # Group by time limit
    by_time = {}
    for r in tp_data:
        tl = r['time_limit']
        if tl not in by_time:
            by_time[tl] = []
        by_time[tl].append(r)
    
    best_pnl = -999
    best_time = 0
    best_wr = 0
    
    for tl, results in by_time.items():
        total_pnl = sum(r['pnl_dollars'] for r in results)
        wins = sum(1 for r in results if r['outcome'] == 'TP_HIT')
        wr = wins / len(results) * 100
        
        if total_pnl > best_pnl:
            best_pnl = total_pnl
            best_time = tl
            best_wr = wr
    
    summary_rows.append({
        'tp': tp,
        'optimal_time': best_time,
        'win_rate': best_wr,
        'total_pnl': best_pnl,
        'avg_pnl': best_pnl / len(tp_data) if tp_data else 0
    })

summary_df = pd.DataFrame(summary_rows)
print("\nTargetProfit | Optimal Time | Win Rate | Total P&L | Avg P&L")
print("-" * 70)
for _, row in summary_df.iterrows():
    marker = " <-- BEST" if row['total_pnl'] == summary_df['total_pnl'].max() else ""
    print(f"${row['tp']:>10.2f} | {row['optimal_time']:>12}min | {row['win_rate']:>7.1f}% | "
          f"${row['total_pnl']:>8.2f} | ${row['avg_pnl']:>6.2f}{marker}")

# Best overall
best_overall = summary_df.loc[summary_df['total_pnl'].idxmax()]
print(f"\n[OPTIMAL CONFIGURATION]")
print(f"  TargetProfit: ${best_overall['tp']:.2f}")
print(f"  Time Limit: {best_overall['optimal_time']:.0f} minutes")
print(f"  Expected Win Rate: {best_overall['win_rate']:.1f}%")
print(f"  Expected Total P&L: ${best_overall['total_pnl']:.2f}")

summary_df.to_csv('time_exit_simulation_summary.csv', index=False)
print("\n[SAVED] Results saved to CSV files")
