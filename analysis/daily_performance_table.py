#!/usr/bin/env python3
"""Daily Performance Table - MH, HR05, HR10 by Date"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
sys.path.insert(0, r'c:\Trading_GU\.agents\scripts')

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import gu_tools

print('='*70)
print('DAILY PERFORMANCE TABLE - MH, HR05, HR10 (March 1-12, 2026)')
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

# Parse strategy
def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): return 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    strategies = {'0': 'TESTS', '1': 'HR10', '2': 'HR05', '3': 'MH'}
    return strategies.get(strat_id, f'STRAT_{strat_id}')

df['strategy'] = df['magic'].apply(lambda x: parse_magic(x))
df['date'] = df['open_time'].dt.date
df['open_hour_utc'] = df['open_time'].dt.hour

# Normalize P/L to 0.01 lot
avg_lot = df['volume'].mean() if not df.empty else 0.01
lot_norm = avg_lot * 100
df['net_pl_norm'] = df['net_pl'] / lot_norm

# Filter to only MH, HR05, HR10 (exclude TESTS)
df_baselines = df[df['strategy'].isin(['MH', 'HR05', 'HR10'])].copy()

# Create daily summary by strategy
daily_summary = df_baselines.groupby(['date', 'strategy']).agg({
    'net_pl_norm': ['count', 'sum', lambda x: (x > 0).sum()]
}).unstack(fill_value=0)

print(f"\nNormalization: {avg_lot:.2f} lots per trade (divide by {lot_norm:.0f})")
print(f"Strategies: MH, HR05, HR10 (TESTS excluded)")
print()

# Print header
print(f"{'Date':<12} {'MH(T/W/L/PnL)':<20} {'HR05(T/W/L/PnL)':<20} {'HR10(T/W/L/PnL)':<20} {'Daily Total':<15}")
print('-'*95)

# Get all unique dates
all_dates = sorted(df_baselines['date'].unique())

for date in all_dates:
    day_data = df_baselines[df_baselines['date'] == date]
    
    row_str = f"{str(date):<12}"
    daily_total = 0
    
    for strategy in ['MH', 'HR05', 'HR10']:
        strat_day = day_data[day_data['strategy'] == strategy]
        trades = len(strat_day)
        wins = len(strat_day[strat_day['net_pl_norm'] > 0])
        losses = len(strat_day[strat_day['net_pl_norm'] < 0])
        pnl = strat_day['net_pl_norm'].sum()
        daily_total += pnl
        
        if trades > 0:
            row_str += f" {trades}/{wins}/{losses}/${pnl:>+6.2f}"
        else:
            row_str += f" {'--':>17}"
    
    row_str += f"   ${daily_total:>+7.2f}"
    print(row_str)

# Totals row
print('-'*95)
row_str = f"{'TOTAL':<12}"
grand_total = 0
for strategy in ['MH', 'HR05', 'HR10']:
    strat_data = df_baselines[df_baselines['strategy'] == strategy]
    trades = len(strat_data)
    wins = len(strat_data[strat_data['net_pl_norm'] > 0])
    losses = len(strat_data[strat_data['net_pl_norm'] < 0])
    pnl = strat_data['net_pl_norm'].sum()
    grand_total += pnl
    row_str += f" {trades}/{wins}/{losses}/${pnl:>+6.2f}"
row_str += f"   ${grand_total:>+7.2f}"
print(row_str)

# =============================================================================
# WHY NY END HOUR 21:00 NEEDS TO CHANGE
# =============================================================================
print()
print('='*70)
print('ANALYSIS: WHY NY END HOUR 21:00 MUST CHANGE TO 20:00')
print('='*70)

ny_data = df_baselines[df_baselines['strategy'].isin(['HR05', 'HR10', 'MH'])]
ny_data = ny_data[ny_data['open_hour_utc'].isin([17, 18, 19, 20, 21])]  # NY window hours

print(f"\nNY Session Performance by Hour (17-21 UTC):")
print(f"{'Hour':<8} {'Trades':>8} {'Win%':>8} {'Net P/L':>12} {'Avg P/L':>10}")
print('-'*55)

for hour in [17, 18, 19, 20, 21]:
    hour_data = ny_data[ny_data['open_hour_utc'] == hour]
    if len(hour_data) == 0:
        continue
    trades = len(hour_data)
    wins = len(hour_data[hour_data['net_pl_norm'] > 0])
    win_pct = wins / trades * 100
    pnl = hour_data['net_pl_norm'].sum()
    avg = pnl / trades
    print(f"{hour:02d}:00    {trades:>8} {win_pct:>7.1f}% {pnl:>+11.2f} {avg:>+9.3f}")

# Calculate impact of removing 21:00
ny_without_21 = df_baselines[df_baselines['strategy'].isin(['HR05', 'HR10', 'MH'])]
ny_without_21 = ny_without_21[ny_without_21['open_hour_utc'].isin([17, 18, 19, 20])]
ny_with_21 = df_baselines[df_baselines['strategy'].isin(['HR05', 'HR10', 'MH'])]
ny_with_21 = ny_with_21[ny_with_21['open_hour_utc'].isin([17, 18, 19, 20, 21])]

print(f"\nImpact of Removing UTC 21:00:")
print(f"  With 21:00:    {len(ny_with_21)} trades, ${ny_with_21['net_pl_norm'].sum():+.2f}")
print(f"  Without 21:00: {len(ny_without_21)} trades, ${ny_without_21['net_pl_norm'].sum():+.2f}")
print(f"  Improvement:   +${ny_without_21['net_pl_norm'].sum() - ny_with_21['net_pl_norm'].sum():.2f}")

# =============================================================================
# WHY ASIA END HOUR 06:00 NEEDS TO CHANGE TO 05:00
# =============================================================================
print()
print('='*70)
print('ANALYSIS: WHY ASIA END HOUR 06:00 SHOULD CHANGE TO 05:00')
print('='*70)

asia_data = df_baselines[df_baselines['strategy'].isin(['HR05', 'HR10', 'MH'])]
asia_data = asia_data[asia_data['open_hour_utc'].isin([2, 3, 4, 5, 6])]  # Asia window

print(f"\nAsia Session Performance by Hour (02-06 UTC):")
print(f"{'Hour':<8} {'Trades':>8} {'Win%':>8} {'Net P/L':>12} {'Avg P/L':>10}")
print('-'*55)

for hour in [2, 3, 4, 5, 6]:
    hour_data = asia_data[asia_data['open_hour_utc'] == hour]
    if len(hour_data) == 0:
        continue
    trades = len(hour_data)
    wins = len(hour_data[hour_data['net_pl_norm'] > 0])
    win_pct = wins / trades * 100
    pnl = hour_data['net_pl_norm'].sum()
    avg = pnl / trades
    print(f"{hour:02d}:00    {trades:>8} {win_pct:>7.1f}% {pnl:>+11.2f} {avg:>+9.3f}")

asia_without_6 = df_baselines[df_baselines['strategy'].isin(['HR05', 'HR10', 'MH'])]
asia_without_6 = asia_without_6[asia_data['open_hour_utc'].isin([2, 3, 4, 5])]
asia_with_6 = df_baselines[df_baselines['strategy'].isin(['HR05', 'HR10', 'MH'])]
asia_with_6 = asia_with_6[asia_with_6['open_hour_utc'].isin([2, 3, 4, 5, 6])]

print(f"\nImpact of Removing UTC 06:00:")
print(f"  With 06:00:    {len(asia_with_6)} trades, ${asia_with_6['net_pl_norm'].sum():+.2f}")
print(f"  Without 06:00: {len(asia_without_6)} trades, ${asia_without_6['net_pl_norm'].sum():+.2f}")
print(f"  Improvement:   +${asia_without_6['net_pl_norm'].sum() - asia_with_6['net_pl_norm'].sum():.2f}")

print()
print('Analysis complete.')
