#!/usr/bin/env python3
"""Detailed Loss Analysis for GU Strategy - March 1 onwards"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
sys.path.insert(0, r'c:\Trading_GU\.agents\scripts')

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import gu_tools

print('='*70)
print('DETAILED GU LOSS ANALYSIS - MARCH 1, 2026 ONWARDS')
print('='*70)

# Connect to Vantage
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect')
    exit(1)

date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
date_to = datetime.now(timezone.utc)
positions = gu_tools.fetch_positions(date_from, date_to)
gu_tools.mt5.shutdown()

df = pd.DataFrame(positions)
df = df[df['magic'].astype(str).str.startswith('282603')].copy()

# Parse strategy and session
def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): return 'UNKNOWN', 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    session_id = m[7] if len(m) > 7 else '0'
    strategies = {'0': 'TESTS', '1': 'HR10', '2': 'HR05', '3': 'MH'}
    sessions = {'0': 'FULL', '1': 'ASIA', '2': 'LONDON', '3': 'NY'}
    return strategies.get(strat_id, f'STRAT_{strat_id}'), sessions.get(session_id, f'SESS_{session_id}')

df['strategy'] = df['magic'].apply(lambda x: parse_magic(x)[0])
df['session'] = df['magic'].apply(lambda x: parse_magic(x)[1])
df['open_hour_utc'] = df['open_time'].dt.hour

# Normalize P/L to 0.01 lot
avg_lot = df['volume'].mean() if not df.empty else 0.01
lot_norm = avg_lot * 100
df['net_pl_norm'] = df['net_pl'] / lot_norm

# Filter only losers
losers = df[df['net_pl_norm'] < 0].copy()

print(f'\nTotal Positions: {len(df)}')
print(f'Total Losers: {len(losers)}')
print(f'Loss Rate: {len(losers)/len(df)*100:.1f}%')
print(f'Total Loss (normalized): ${losers["net_pl_norm"].sum():.2f}')
print(f'Average Loss: ${losers["net_pl_norm"].mean():.3f}')

# =============================================================================
# ALL LOSSES BY STRATEGY
# =============================================================================
print()
print('='*70)
print('ALL LOSSES BY STRATEGY (March 1 onwards)')
print('='*70)

for strategy in ['MH', 'HR05', 'HR10', 'TESTS']:
    strat_losses = losers[losers['strategy'] == strategy]
    if len(strat_losses) == 0:
        continue
    
    print(f"\n{strategy} Strategy - {len(strat_losses)} losses")
    print(f"{'Open Time (UTC)':<20} {'Close Time (UTC)':<20} {'Session':<10} {'P/L':>10} {'Magic':<15}")
    print('-'*80)
    
    for _, row in strat_losses.sort_values('open_time').iterrows():
        open_time = row['open_time'].strftime('%Y-%m-%d %H:%M:%S')
        close_time = row['close_time'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{open_time:<20} {close_time:<20} {row['session']:<10} ${row['net_pl_norm']:>+8.2f} {int(row['magic']):<15}")

# =============================================================================
# LOSSES AT UTC 21:00 AND 03:00
# =============================================================================
print()
print('='*70)
print('LOSSES AT UTC 21:00 AND 03:00 (Toxic Hours)')
print('='*70)

toxic_hours = [21, 3]
toxic_losses = losers[losers['open_hour_utc'].isin(toxic_hours)].copy()

print(f"\nTotal toxic hour losses: {len(toxic_losses)}")
print(f"Total toxic hour loss amount: ${toxic_losses['net_pl_norm'].sum():.2f}")

for hour in toxic_hours:
    hour_losses = toxic_losses[toxic_losses['open_hour_utc'] == hour]
    if len(hour_losses) == 0:
        continue
    
    print(f"\nUTC {hour:02d}:00 Losses - {len(hour_losses)} trades, ${hour_losses['net_pl_norm'].sum():.2f} total")
    print(f"{'Open Time (UTC)':<20} {'Close Time (UTC)':<20} {'Strategy':<10} {'Session':<10} {'P/L':>10} {'Magic':<15}")
    print('-'*90)
    
    for _, row in hour_losses.sort_values('open_time').iterrows():
        open_time = row['open_time'].strftime('%Y-%m-%d %H:%M:%S')
        close_time = row['close_time'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{open_time:<20} {close_time:<20} {row['strategy']:<10} {row['session']:<10} ${row['net_pl_norm']:>+8.2f} {int(row['magic']):<15}")

# =============================================================================
# RECOVERY ANALYSIS
# =============================================================================
print()
print('='*70)
print('RECOVERY ANALYSIS (Price Return After SL Hit)')
print('='*70)
print("""
Concept: After an SL is hit, how often does price return to the original entry?
This is computed from the close price (SL exit) vs open price (entry).
A "recovery" would be if price moves back favorably after the losing exit.
""")

# Calculate price movement after exit
# This requires tick data which we don't have, but we can estimate from the data
print("Note: Full recovery analysis requires tick data after exit.")
print("Below shows the magnitude of losses - larger losses = less likely to recover quickly.")

losses_by_size = losers.copy()
losses_by_size['loss_size'] = pd.cut(losses_by_size['net_pl_norm'], 
                                      bins=[-float('inf'), -5, -2, -1, 0], 
                                      labels=['Major (>$5)', 'Large ($2-5)', 'Medium ($1-2)', 'Small (<$1)'])

print(f"\nLoss Distribution by Size:")
size_stats = losses_by_size.groupby('loss_size').agg({
    'net_pl_norm': ['count', 'sum', 'mean']
})
size_stats.columns = ['count', 'total', 'avg']
for size, row in size_stats.iterrows():
    print(f"  {size}: {int(row['count'])} trades, ${row['total']:.2f} total, ${row['avg']:.2f} avg")

# =============================================================================
# MH SPECIFIC ANALYSIS
# =============================================================================
print()
print('='*70)
print('MH STRATEGY - DEEP DIVE (The 90% WR / Negative P/L Paradox)')
print('='*70)

mh_losses = losers[losers['strategy'] == 'MH']
if len(mh_losses) > 0:
    print(f"\nMH Losses: {len(mh_losses)} trades")
    print(f"Total MH Loss: ${mh_losses['net_pl_norm'].sum():.2f}")
    print(f"Average MH Loss: ${mh_losses['net_pl_norm'].mean():.3f}")
    print(f"Largest Single Loss: ${mh_losses['net_pl_norm'].min():.2f}")
    
    print(f"\nDetailed MH Losses:")
    print(f"{'Open Time (UTC)':<20} {'Close Time (UTC)':<20} {'Session':<10} {'P/L':>10} {'Magic':<15} {'Duration':>10}")
    print('-'*90)
    
    for _, row in mh_losses.sort_values('open_time').iterrows():
        open_time = row['open_time'].strftime('%Y-%m-%d %H:%M:%S')
        close_time = row['close_time'].strftime('%Y-%m-%d %H:%M:%S')
        duration = (row['close_time'] - row['open_time']).total_seconds() / 60  # minutes
        print(f"{open_time:<20} {close_time:<20} {row['session']:<10} ${row['net_pl_norm']:>+8.2f} {int(row['magic']):<15} {duration:>8.1f}m")

# =============================================================================
# SUMMARY STATS
# =============================================================================
print()
print('='*70)
print('SUMMARY STATISTICS')
print('='*70)

print(f"\nLosses by Strategy:")
for strategy in ['MH', 'HR05', 'HR10', 'TESTS']:
    strat_losses = losers[losers['strategy'] == strategy]
    total_strat = df[df['strategy'] == strategy]
    if len(total_strat) > 0:
        loss_rate = len(strat_losses) / len(total_strat) * 100
        print(f"  {strategy}: {len(strat_losses)}/{len(total_strat)} ({loss_rate:.1f}%) = ${strat_losses['net_pl_norm'].sum():.2f}")

print(f"\nLosses by Hour (Top 10):")
hourly_losses = losers.groupby('open_hour_utc').agg({
    'net_pl_norm': ['count', 'sum']
}).sort_values(('net_pl_norm', 'sum'))
for hr, row in hourly_losses.head(10).iterrows():
    print(f"  UTC {hr:02d}:00: {int(row[('net_pl_norm', 'count')])} losses, ${row[('net_pl_norm', 'sum')]:.2f}")

print()
print('Analysis complete.')
