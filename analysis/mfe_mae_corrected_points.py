#!/usr/bin/env python3
"""
MFE / MAE Analysis - CORRECTED to POINTS (×100)
"""
import pandas as pd

df = pd.read_csv('asia_mfe_mae_correct.csv')

# CORRECT: Multiply by 100 to get true points
# Price 5194.74 -> 5195.67 = 0.93 price = 93 points
df['mfe_points_correct'] = df['mfe_points'] * 100
df['mae_points_correct'] = df['mae_points'] * 100

print("="*100)
print("MFE / MAE ANALYSIS - CORRECTED TO POINTS (×100)")
print("="*100)
print("\nXAUUSD: Price 5194.74 to 5195.67 = 0.93 price move = 93 points")
print("1 point = $0.01 on 0.01 lot")
print()

print("="*80)
print("CORRECTED STATISTICS (in points)")
print("="*80)
print(f"\n{'Metric':<30} {'Mean':>12} {'Median':>12} {'Min':>12} {'Max':>12}")
print("-"*80)
print(f"{'MFE (points)':<30} {df['mfe_points_correct'].mean():>11.2f} {df['mfe_points_correct'].median():>11.2f} "
      f"{df['mfe_points_correct'].min():>11.2f} {df['mfe_points_correct'].max():>11.2f}")
print(f"{'MAE (points)':<30} {df['mae_points_correct'].mean():>11.2f} {df['mae_points_correct'].median():>11.2f} "
      f"{df['mae_points_correct'].min():>11.2f} {df['mae_points_correct'].max():>11.2f}")
print(f"{'Duration (minutes)':<30} {df['duration_min'].mean():>11.2f} {df['duration_min'].median():>11.2f} "
      f"{df['duration_min'].min():>11.2f} {df['duration_min'].max():>11.2f}")

print("\n" + "="*80)
print("MFE DISTRIBUTION (in points)")
print("="*80)

ranges = [
    (0, 50, "0-50 points"),
    (50, 100, "50-100 points"),
    (100, 150, "100-150 points"),
    (150, 200, "150-200 points"),
    (200, 300, "200-300 points"),
    (300, 500, "300-500 points"),
    (500, 9999, "500+ points")
]

print(f"\n{'Range':<20} {'Count':>8} {'%':>8} {'Avg P&L ($)':>12}")
print("-"*55)

for min_pts, max_pts, label in ranges:
    mask = (df['mfe_points_correct'] >= min_pts) & (df['mfe_points_correct'] < max_pts)
    count = mask.sum()
    pct = count / len(df) * 100
    avg_pl = df[mask]['actual_pl_norm'].mean() if count > 0 else 0
    print(f"{label:<20} {count:>8} {pct:>7.1f}% ${avg_pl:>10.2f}")

print("\n" + "="*80)
print("POSITIONS WITH MFE >= 20 POINTS")
print("="*80)

high_mfe = df[df['mfe_points_correct'] >= 20]
print(f"\nPositions with MFE >= 20 points: {len(high_mfe)}/{len(df)} ({len(high_mfe)/len(df)*100:.1f}%)")

if len(high_mfe) > 0:
    print(f"\nPositions with MFE >= 100 points: {(df['mfe_points_correct'] >= 100).sum()}")
    print(f"Positions with MFE >= 200 points: {(df['mfe_points_correct'] >= 200).sum()}")
    print(f"Positions with MFE >= 300 points: {(df['mfe_points_correct'] >= 300).sum()}")

print("\n" + "="*80)
print("SAMPLE POSITIONS (First 15)")
print("="*80)

print(f"\n{'Time':<20} {'Dir':<6} {'MFE (pts)':>12} {'MAE (pts)':>12} {'P&L ($)':>10} {'Dur (min)':>10}")
print("-"*85)

sample = df.head(15)
for _, row in sample.iterrows():
    t = str(row['time'])[:16]
    print(f"{t:<20} {row['direction']:<6} {row['mfe_points_correct']:>12.2f} "
          f"{row['mae_points_correct']:>12.2f} ${row['actual_pl_norm']:>9.2f} {row['duration_min']:>10.2f}")

print("\n" + "="*80)
print("WINNERS vs LOSERS (MFE in points)")
print("="*80)

winners = df[df['actual_pl_norm'] > 0]
losers = df[df['actual_pl_norm'] < 0]

print(f"\nWinners ({len(winners)} positions, {len(winners)/len(df)*100:.1f}%):")
print(f"  Avg MFE: {winners['mfe_points_correct'].mean():.2f} points")
print(f"  Avg MAE: {winners['mae_points_correct'].mean():.2f} points")
print(f"  Avg P&L: ${winners['actual_pl_norm'].mean():.2f}")

print(f"\nLosers ({len(losers)} positions, {len(losers)/len(df)*100:.1f}%):")
if len(losers) > 0:
    print(f"  Avg MFE: {losers['mfe_points_correct'].mean():.2f} points")
    print(f"  Avg MAE: {losers['mae_points_correct'].mean():.2f} points")
    print(f"  Avg P&L: ${losers['actual_pl_norm'].mean():.2f}")

print("\n" + "="*80)
print("KEY INSIGHT (CORRECTED)")
print("="*80)
print(f"""
Average MFE: {df['mfe_points_correct'].mean():.0f} points (${df['mfe_points_correct'].mean()*0.01:.2f} on 0.01 lot)
Maximum MFE: {df['mfe_points_correct'].max():.0f} points (${df['mfe_points_correct'].max()*0.01:.2f} on 0.01 lot)

For a $0.20 TP, you need 20 points MFE.
Positions reaching 20+ points MFE: {(df['mfe_points_correct'] >= 20).sum()}/{len(df)} ({(df['mfe_points_correct'] >= 20).sum()/len(df)*100:.1f}%)

So a $0.20 TP IS achievable for many positions!
""")
