#!/usr/bin/env python3
"""Vantage Live Performance Analysis with Lot-Normalized P/L"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
sys.path.insert(0, r'c:\Trading_GU\.agents\scripts')

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import gu_tools

# Connect to Vantage
print('='*70)
print('CONNECTING TO VANTAGE INTERNATIONAL-DEMO')
print('='*70)
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect to Vantage')
    exit(1)

# Fetch last 14 days
date_from = datetime.now(timezone.utc) - timedelta(days=14)
date_to = datetime.now(timezone.utc)

positions = gu_tools.fetch_positions(date_from, date_to)
gu_tools.mt5.shutdown()

df = pd.DataFrame(positions)
print(f'\nFetched {len(df)} raw positions from Vantage')

# Filter GU magics
df = df[df['magic'].astype(str).str.startswith('282603')].copy()
print(f'GU positions after filtering: {len(df)}')

if df.empty:
    print('No GU positions found!')
    exit(0)

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

# Calculate lot normalization factor (normalize to 0.01 lot equivalent)
avg_lot = df['volume'].mean() if not df.empty else 0.01
lot_norm_factor = avg_lot * 100  # e.g., 0.10 lots * 100 = 10 (divide by 10)

# Normalize P/L
df['net_pl_normalized'] = df['net_pl'] / lot_norm_factor
df['profit_normalized'] = df['profit'] / lot_norm_factor

# Overall Performance
print()
print('='*70)
print('VANTAGE LIVE PERFORMANCE (Last 14 Days)')
print('='*70)
print(f'Average Lot Size: {avg_lot:.2f} lots')
print(f'Normalization Factor: Divide by {lot_norm_factor:.0f} for 0.01 lot equivalent')
print()

total = len(df)
wins = len(df[df['net_pl'] > 0])
losses = len(df[df['net_pl'] < 0])
win_rate = wins / total * 100 if total > 0 else 0
net_pl = df['net_pl'].sum()
net_pl_norm = df['net_pl_normalized'].sum()

print(f'Total Trades:     {total}')
print(f'Winners:          {wins}')
print(f'Losers:           {losses}')
print(f'Flat:             {total - wins - losses}')
print(f'Win Rate:         {win_rate:.1f}%')
print()
print('RAW P/L (at current lot size):')
print(f'  Gross P/L:      ${df["profit"].sum():.2f}')
print(f'  Commission:     ${df["commission"].sum():.2f}')
print(f'  Swap:           ${df["swap"].sum():.2f}')
print(f'  Net P/L:        ${net_pl:.2f}')
print()
print('NORMALIZED P/L (0.01 lot equivalent):')
print(f'  Gross P/L:      ${df["profit_normalized"].sum():.2f}')
print(f'  Net P/L:        ${net_pl_norm:.2f}')
print()

# By Strategy
print('-'*70)
print('PERFORMANCE BY STRATEGY (0.01 lot normalized)')
print('-'*70)
print(f'{"Strategy":<12} {"Trades":>8} {"Win%":>8} {"Net P/L":>12} {"Avg Trade":>10}')
print('-'*70)
for strat in sorted(df['strategy'].unique()):
    sub = df[df['strategy'] == strat]
    w = len(sub[sub['net_pl'] > 0])
    t = len(sub)
    wr = w/t*100 if t > 0 else 0
    net = sub['net_pl_normalized'].sum()
    avg = net/t if t > 0 else 0
    print(f'{strat:<12} {t:>8} {wr:>7.1f}% {net:>+11.2f} {avg:>+9.3f}')

# By Session
print()
print('-'*70)
print('PERFORMANCE BY SESSION (0.01 lot normalized)')
print('-'*70)
print(f'{"Session":<12} {"Trades":>8} {"Win%":>8} {"Net P/L":>12} {"Avg Trade":>10}')
print('-'*70)
for sess in ['ASIA', 'LONDON', 'NY', 'FULL']:
    sub = df[df['session'] == sess]
    if len(sub) == 0: continue
    w = len(sub[sub['net_pl'] > 0])
    t = len(sub)
    wr = w/t*100 if t > 0 else 0
    net = sub['net_pl_normalized'].sum()
    avg = net/t if t > 0 else 0
    print(f'{sess:<12} {t:>8} {wr:>7.1f}% {net:>+11.2f} {avg:>+9.3f}')

# By Magic Number
print()
print('-'*70)
print('PERFORMANCE BY MAGIC (0.01 lot normalized)')
print('-'*70)
print(f'{"Magic":<15} {"Strategy":<10} {"Session":<8} {"Trades":>8} {"Win%":>8} {"Net P/L":>12}')
print('-'*70)
magic_stats = df.groupby('magic').agg({
    'net_pl_normalized': ['count', 'sum', lambda x: (x > 0).sum()],
    'strategy': 'first',
    'session': 'first'
})
magic_stats.columns = ['trades', 'net_pl', 'wins', 'strategy', 'session']
magic_stats['win_rate'] = magic_stats['wins'] / magic_stats['trades'] * 100
magic_stats = magic_stats.sort_values('trades', ascending=False)
for magic, row in magic_stats.iterrows():
    print(f'{int(magic):<15} {row["strategy"]:<10} {row["session"]:<8} {int(row["trades"]):>8} {row["win_rate"]:>7.1f}% {row["net_pl"]:>+11.2f}')

# Hourly breakdown
print()
print('-'*70)
print('HOURLY BREAKDOWN - IDENTIFY TOXIC HOURS (0.01 lot normalized)')
print('-'*70)
print(f'{"Hour (UTC)":<12} {"Trades":>8} {"Win%":>8} {"Total P/L":>12} {"Avg P/L":>10}')
print('-'*70)
hourly = df.groupby('open_hour_utc').agg({
    'net_pl_normalized': ['count', 'sum', lambda x: (x > 0).sum()]
})
hourly.columns = ['trades', 'net_pl', 'wins']
hourly['win_rate'] = hourly['wins'] / hourly['trades'] * 100
for hr in sorted(hourly.index):
    row = hourly.loc[hr]
    avg = row['net_pl'] / row['trades'] if row['trades'] > 0 else 0
    print(f'{hr:02d}:00-{(hr+1)%24:02d}:00   {int(row["trades"]):>8} {row["win_rate"]:>7.1f}% {row["net_pl"]:>+11.2f} {avg:>+9.3f}')

# Warning flags
print()
print('='*70)
print('ANOMALY DETECTION (0.01 lot normalized)')
print('='*70)

# Check for low win rate sessions
for sess in ['ASIA', 'LONDON', 'NY']:
    sub = df[df['session'] == sess]
    if len(sub) > 5:
        w = len(sub[sub['net_pl'] > 0])
        wr = w/len(sub)*100
        if wr < 70:
            print(f'[WARNING] {sess} session win rate is {wr:.1f}% (below 70% threshold)')

# Check for toxic hours
for hr in hourly.index:
    row = hourly.loc[hr]
    if row['trades'] >= 10 and row['net_pl'] < -5:
        print(f'[WARNING] UTC {hr:02d}:00 is toxic: {int(row["trades"])} trades, ${row["net_pl"]:.2f} net loss (normalized)')

print()
print('Analysis complete.')
