#!/usr/bin/env python3
"""Verify real position data"""
import pandas as pd

df = pd.read_csv('asia_mfe_mae_correct.csv')

print('REAL DATA VERIFICATION')
print('='*80)
print(f'Total positions: {len(df)}')

# Check actual durations
df_under_1min = df[df['duration_min'] < 1]
df_under_2min = df[df['duration_min'] < 2]
df_under_5min = df[df['duration_min'] < 5]

print(f'\nPositions closed under 1 minute: {len(df_under_1min)} ({len(df_under_1min)/len(df)*100:.1f}%)')
print(f'Positions closed under 2 minutes: {len(df_under_2min)} ({len(df_under_2min)/len(df)*100:.1f}%)')
print(f'Positions closed under 5 minutes: {len(df_under_5min)} ({len(df_under_5min)/len(df)*100:.1f}%)')

# Check P&L for those under 1 min
print(f'\nPositions under 1 minute:')
print(f'  Count: {len(df_under_1min)}')
profitable_1min = (df_under_1min['actual_pl_norm'] > 0).sum()
print(f'  Profitable: {profitable_1min}')
print(f'  Avg P&L: ${df_under_1min["actual_pl_norm"].mean():.4f}')
print(f'  Total P&L: ${df_under_1min["actual_pl_norm"].sum():.4f}')

# Check the MFE distribution
print(f'\nMFE Distribution (during actual trade duration):')
print(f'  Min: ${df["mfe_norm"].min():.4f}')
print(f'  Max: ${df["mfe_norm"].max():.4f}')
print(f'  Mean: ${df["mfe_norm"].mean():.4f}')
print(f'  Median: ${df["mfe_norm"].median():.4f}')

# Check how many had MFE >= 0.20
mfe_20plus = df[df['mfe_norm'] >= 0.20]
print(f'\nPositions with MFE >= $0.20: {len(mfe_20plus)} ({len(mfe_20plus)/len(df)*100:.1f}%)')

if len(mfe_20plus) > 0:
    print(f'  Avg P&L: ${mfe_20plus["actual_pl_norm"].mean():.4f}')
    print(f'  Avg Duration: {mfe_20plus["duration_min"].mean():.2f} min')

# Check how many had MFE >= 0.10
mfe_10plus = df[df['mfe_norm'] >= 0.10]
print(f'\nPositions with MFE >= $0.10: {len(mfe_10plus)} ({len(mfe_10plus)/len(df)*100:.1f}%)')

# Check how many had MFE >= 0.05
mfe_5plus = df[df['mfe_norm'] >= 0.05]
print(f'Positions with MFE >= $0.05: {len(mfe_5plus)} ({len(mfe_5plus)/len(df)*100:.1f}%)')

# Sample of early closes
print(f'\nSample positions (first 10):')
sample = df.head(10)[['time', 'duration_min', 'mfe_norm', 'actual_pl_norm']]
for _, row in sample.iterrows():
    t = row['time'][:16] if len(str(row['time'])) > 16 else row['time']
    print(f'  {t}: {row["duration_min"]:.2f}min, MFE=${row["mfe_norm"]:.4f}, P&L=${row["actual_pl_norm"]:.4f}')

# Check actual closes - look at the close times
print(f'\nDuration breakdown:')
df['dur_bin'] = pd.cut(df['duration_min'], bins=[0, 0.5, 1, 2, 5, 10, 40], labels=['<0.5m', '0.5-1m', '1-2m', '2-5m', '5-10m', '10m+'])
print(df.groupby('dur_bin').size())
