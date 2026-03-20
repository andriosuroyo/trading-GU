#!/usr/bin/env python3
"""
MFE/MAE Analysis in POINTS (not dollars)
"""
import pandas as pd

df = pd.read_csv('asia_mfe_mae_correct.csv')

print("="*100)
print("MFE / MAE ANALYSIS - IN POINTS")
print("="*100)
print("\n1 point = $0.01 on 0.01 lot = $0.10 on 0.10 lot")
print()

print("="*80)
print("OVERALL STATISTICS")
print("="*80)
print(f"\n{'Metric':<30} {'Mean':>12} {'Median':>12} {'Min':>12} {'Max':>12}")
print("-"*80)
print(f"{'MFE (points)':<30} {df['mfe_points'].mean():>11.2f} {df['mfe_points'].median():>11.2f} {df['mfe_points'].min():>11.2f} {df['mfe_points'].max():>11.2f}")
print(f"{'MAE (points)':<30} {df['mae_points'].mean():>11.2f} {df['mae_points'].median():>11.2f} {df['mae_points'].min():>11.2f} {df['mae_points'].max():>11.2f}")
print(f"{'Duration (minutes)':<30} {df['duration_min'].mean():>11.2f} {df['duration_min'].median():>11.2f} {df['duration_min'].min():>11.2f} {df['duration_min'].max():>11.2f}")

print("\n" + "="*80)
print("MFE DISTRIBUTION")
print("="*80)

# Count by MFE ranges
ranges = [
    (0, 1, "0-1 points"),
    (1, 2, "1-2 points"),
    (2, 3, "2-3 points"),
    (3, 5, "3-5 points"),
    (5, 10, "5-10 points"),
    (10, 20, "10-20 points"),
    (20, 50, "20-50 points"),
    (50, 999, "50+ points")
]

print(f"\n{'Range':<15} {'Count':>8} {'%':>8} {'Avg P&L ($)':>12}")
print("-"*50)

for min_pts, max_pts, label in ranges:
    mask = (df['mfe_points'] >= min_pts) & (df['mfe_points'] < max_pts)
    count = mask.sum()
    pct = count / len(df) * 100
    avg_pl = df[mask]['actual_pl_norm'].mean() if count > 0 else 0
    print(f"{label:<15} {count:>8} {pct:>7.1f}% ${avg_pl:>10.2f}")

print("\n" + "="*80)
print("SAMPLE POSITIONS (First 15)")
print("="*80)

print(f"\n{'Time':<20} {'Dir':<6} {'MFE (pts)':>10} {'MAE (pts)':>10} {'P&L ($)':>10} {'Dur (min)':>10}")
print("-"*80)

sample = df.head(15)
for _, row in sample.iterrows():
    t = str(row['time'])[:16]
    print(f"{t:<20} {row['direction']:<6} {row['mfe_points']:>10.2f} {row['mae_points']:>10.2f} ${row['actual_pl_norm']:>9.2f} {row['duration_min']:>10.2f}")

print("\n" + "="*80)
print("POSITIONS WITH MFE >= 20 POINTS")
print("="*80)

high_mfe = df[df['mfe_points'] >= 20]
if len(high_mfe) > 0:
    print(f"\nFound {len(high_mfe)} positions with MFE >= 20 points:")
    print(f"\n{'Time':<20} {'MFE':>10} {'MAE':>10} {'P&L':>10} {'Duration':>10}")
    print("-"*70)
    for _, row in high_mfe.iterrows():
        t = str(row['time'])[:16]
        print(f"{t:<20} {row['mfe_points']:>10.2f} {row['mae_points']:>10.2f} ${row['actual_pl_norm']:>9.2f} {row['duration_min']:>10.2f}")
else:
    print("\nNO positions had MFE >= 20 points")
    print(f"Max MFE was {df['mfe_points'].max():.2f} points")

print("\n" + "="*80)
print("WINNERS vs LOSERS (by MFE in points)")
print("="*80)

winners = df[df['actual_pl_norm'] > 0]
losers = df[df['actual_pl_norm'] < 0]

print(f"\nWinners ({len(winners)} positions, {len(winners)/len(df)*100:.1f}%):")
print(f"  Avg MFE: {winners['mfe_points'].mean():.2f} points")
print(f"  Avg MAE: {winners['mae_points'].mean():.2f} points")
print(f"  Avg P&L: ${winners['actual_pl_norm'].mean():.2f}")

print(f"\nLosers ({len(losers)} positions, {len(losers)/len(df)*100:.1f}%):")
if len(losers) > 0:
    print(f"  Avg MFE: {losers['mfe_points'].mean():.2f} points")
    print(f"  Avg MAE: {losers['mae_points'].mean():.2f} points")
    print(f"  Avg P&L: ${losers['actual_pl_norm'].mean():.2f}")

print("\n" + "="*80)
print("KEY INSIGHT")
print("="*80)
print(f"""
Average MFE: {df['mfe_points'].mean():.2f} points (${df['mfe_points'].mean()*0.01:.2f} on 0.01 lot)
Maximum MFE: {df['mfe_points'].max():.2f} points (${df['mfe_points'].max()*0.01:.2f} on 0.01 lot)

For a $0.20 TP, you need 20 points MFE.
Positions reaching 20+ points MFE: {(df['mfe_points'] >= 20).sum()}/{len(df)}

The trailing stop captures profits through small, quick moves.
""")
