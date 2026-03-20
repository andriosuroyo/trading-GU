#!/usr/bin/env python3
"""
CORRECT MFE/MAE Analysis - Using ACTUAL trade duration
Not fixed 30-minute window
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
    
    # Use bid/ask average (XAUUSD+ doesn't have 'last')
    df['price'] = (df['bid'] + df['ask']) / 2
    
    return df

def calculate_mfe_mae(open_price, direction, ticks_df, close_time):
    """Calculate MFE/MAE up to actual close time."""
    if ticks_df.empty:
        return None
    
    # Filter ticks up to close time
    window = ticks_df[ticks_df['time'] <= close_time].copy()
    
    if window.empty:
        return None
    
    max_price = window['price'].max()
    min_price = window['price'].min()
    close_price = window['price'].iloc[-1]
    
    if direction == 'BUY':
        mfe = max_price - open_price
        mae = open_price - min_price
        pnl = close_price - open_price
    else:  # SELL
        mfe = open_price - min_price
        mae = max_price - open_price
        pnl = open_price - close_price
    
    return {
        'mfe_points': mfe,
        'mae_points': mae,
        'pnl_points': pnl,
        'close_price': close_price,
        'max_price': max_price,
        'min_price': min_price,
        'tick_count': len(window)
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

# Filter Asia and get first positions
asia = []
for p in gu_pos:
    if parse_sess(p['magic']) == 'ASIA':
        p['strategy'] = parse_strat(p['magic'])
        asia.append(p)

# Group by basket (same magic, within 60 seconds)
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

# Get first positions only
first_positions = [b['positions'][0] for b in baskets]

# Filter out glitch baskets
glitches = [
    datetime(2026, 3, 12, 5, 2, 15, tzinfo=timezone.utc),
    datetime(2026, 3, 12, 5, 5, 19, tzinfo=timezone.utc),
]
clean_positions = [p for p in first_positions if p['open_time'] not in glitches]

print("="*100)
print("CORRECTED MFE/MAE ANALYSIS - ASIA SESSION")
print("Using ACTUAL trade duration (not fixed 30-min window)")
print("="*100)
print(f"\nAnalyzing {len(clean_positions)} first positions (glitches removed)")

# Calculate MFE/MAE for each position
results = []
for i, pos in enumerate(clean_positions, 1):
    dur = pos['close_time'] - pos['open_time']
    dur_sec = dur.total_seconds()
    dur_min = dur_sec / 60
    
    # Fetch ticks from open to close (plus small buffer)
    from_time = pos['open_time']
    to_time = pos['close_time'] + timedelta(seconds=5)  # Small buffer
    
    ticks = fetch_ticks_range('XAUUSD+', from_time, to_time)
    
    if ticks.empty:
        print(f"[{i}/{len(clean_positions)}] {pos['open_time']} - No tick data")
        continue
    
    stats = calculate_mfe_mae(pos['open_price'], pos['direction'], ticks, pos['close_time'])
    
    if not stats:
        continue
    
    # Lot size normalization
    lot_size = pos['lot_size']
    norm_factor = lot_size * 100  # To convert to 0.01 lot equivalent
    
    actual_pl_norm = pos['net_pl'] / norm_factor
    mfe_norm = stats['mfe_points'] * 0.01  # 1 point = $0.01 on 0.01 lot
    mae_norm = stats['mae_points'] * 0.01
    
    # MFE capture rate
    mfe_capture = (actual_pl_norm / mfe_norm * 100) if mfe_norm > 0 else 0
    
    results.append({
        'time': pos['open_time'],
        'strategy': pos['strategy'],
        'direction': pos['direction'],
        'duration_min': dur_min,
        'lot_size': lot_size,
        'open_price': pos['open_price'],
        'close_price': pos['close_price'],
        'actual_pl': pos['net_pl'],
        'actual_pl_norm': actual_pl_norm,
        'mfe_points': stats['mfe_points'],
        'mae_points': stats['mae_points'],
        'mfe_norm': mfe_norm,
        'mae_norm': mae_norm,
        'mfe_capture_pct': mfe_capture
    })
    
    print(f"[{i}/{len(clean_positions)}] {pos['open_time'].strftime('%m-%d %H:%M:%S')} "
          f"{pos['strategy']:<6} {pos['direction']:<5} {dur_min:>5.1f}min | "
          f"MFE: {stats['mfe_points']:>6.2f}pts (${mfe_norm:>5.2f}) | "
          f"P&L: ${actual_pl_norm:>5.2f} | Capture: {mfe_capture:>5.1f}%")

mt5.shutdown()

# Convert to DataFrame
results_df = pd.DataFrame(results)

if results_df.empty:
    print("\n[ERROR] No results available")
    exit(1)

# Summary
print("\n" + "="*100)
print("SUMMARY STATISTICS (Normalized to 0.01 lot)")
print("="*100)

print(f"\n{'Metric':<30} {'Mean':>12} {'Median':>12} {'Min':>12} {'Max':>12}")
print("-"*80)
print(f"{'MFE (points)':<30} {results_df['mfe_points'].mean():>11.2f} {results_df['mfe_points'].median():>11.2f} "
      f"{results_df['mfe_points'].min():>11.2f} {results_df['mfe_points'].max():>11.2f}")
print(f"{'MFE ($ on 0.01 lot)':<30} {results_df['mfe_norm'].mean():>11.2f}$ {results_df['mfe_norm'].median():>11.2f}$ "
      f"{results_df['mfe_norm'].min():>11.2f}$ {results_df['mfe_norm'].max():>11.2f}$")
print(f"{'MAE (points)':<30} {results_df['mae_points'].mean():>11.2f} {results_df['mae_points'].median():>11.2f} "
      f"{results_df['mae_points'].min():>11.2f} {results_df['mae_points'].max():>11.2f}")
print(f"{'MAE ($ on 0.01 lot)':<30} {results_df['mae_norm'].mean():>11.2f}$ {results_df['mae_norm'].median():>11.2f}$ "
      f"{results_df['mae_norm'].min():>11.2f}$ {results_df['mae_norm'].max():>11.2f}$")
print(f"{'Actual P&L ($)':<30} {results_df['actual_pl_norm'].mean():>11.2f}$ {results_df['actual_pl_norm'].median():>11.2f}$ "
      f"{results_df['actual_pl_norm'].min():>11.2f}$ {results_df['actual_pl_norm'].max():>11.2f}$")
print(f"{'Duration (minutes)':<30} {results_df['duration_min'].mean():>11.2f} {results_df['duration_min'].median():>11.2f} "
      f"{results_df['duration_min'].min():>11.2f} {results_df['duration_min'].max():>11.2f}")

# MFE Capture analysis
print(f"\n{'MFE Capture Rate (%)':<30} {results_df['mfe_capture_pct'].mean():>11.1f}% {results_df['mfe_capture_pct'].median():>11.1f}%")

# Winners vs Losers
winners = results_df[results_df['actual_pl_norm'] > 0]
losers = results_df[results_df['actual_pl_norm'] < 0]

print("\n" + "-"*80)
print(f"Winners: {len(winners)} ({len(winners)/len(results_df)*100:.1f}%)")
print(f"  - Avg MFE: ${winners['mfe_norm'].mean():.2f}")
print(f"  - Avg MAE: ${winners['mae_norm'].mean():.2f}")
print(f"  - Avg P&L: ${winners['actual_pl_norm'].mean():.2f}")
print(f"  - Avg MFE Capture: {winners['mfe_capture_pct'].mean():.1f}%")
print(f"  - Avg Duration: {winners['duration_min'].mean():.1f} min")

print(f"\nLosers: {len(losers)} ({len(losers)/len(results_df)*100:.1f}%)")
if len(losers) > 0:
    print(f"  - Avg MFE: ${losers['mfe_norm'].mean():.2f}")
    print(f"  - Avg MAE: ${losers['mae_norm'].mean():.2f}")
    print(f"  - Avg P&L: ${losers['actual_pl_norm'].mean():.2f}")
    print(f"  - Avg Duration: {losers['duration_min'].mean():.1f} min")

# Save results
results_df.to_csv('asia_mfe_mae_correct.csv', index=False)
print("\n[SAVED] Results saved to asia_mfe_mae_correct.csv")
