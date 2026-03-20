#!/usr/bin/env python3
"""Check the scale of MFE/points"""
import pandas as pd

df = pd.read_csv('asia_mfe_mae_correct.csv')

print('Checking raw price data and MFE calculation:')
print('='*80)

# Sample a few positions
sample = df.head(5)
for _, row in sample.iterrows():
    t = str(row['time'])[:16]
    print(f'\nPosition: {t}')
    print(f'  Direction: {row["direction"]}')
    print(f'  Open Price: {row["open_price"]}')
    print(f'  MFE (stored): {row["mfe_points"]:.2f}')
    print(f'  MFE dollars (0.01 lot): ${row["mfe_norm"]:.4f}')
    
    # Calculate implied point value
    if row['mfe_points'] != 0:
        implied = row['mfe_norm'] / row['mfe_points']
        print(f'  Implied point value: ${implied:.4f} per point')

print('\n' + '='*80)
print('Price Analysis:')

print(f'Open price range: {df["open_price"].min():.2f} to {df["open_price"].max():.2f}')
print(f'Sample open prices:')
for p in df['open_price'].head(10):
    print(f'  {p:.2f}')

print('\n' + '='*80)
print('MFE Statistics (as stored):')
print(f'  Mean: {df["mfe_points"].mean():.2f}')
print(f'  Median: {df["mfe_points"].median():.2f}')
print(f'  Max: {df["mfe_points"].max():.2f}')

print('\n' + '='*80)
print('If numbers are off by factor of 100:')
print(f'  Mean MFE: {df["mfe_points"].mean() * 100:.0f} points')
print(f'  Median MFE: {df["mfe_points"].median() * 100:.0f} points')
print(f'  Max MFE: {df["mfe_points"].max() * 100:.0f} points')

print('\nThis would mean:')
print(f'  93 points = ${93 * 0.01:.2f} on 0.01 lot')
print(f'  315 points = ${315 * 0.01:.2f} on 0.01 lot')
