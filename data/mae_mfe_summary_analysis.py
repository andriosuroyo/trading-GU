"""Summary analysis of MAE/MFE simulation results"""
import pandas as pd
import numpy as np

df = pd.read_csv('data/mae_mfe_march20_magic20_30.csv')

print("=" * 70)
print("MAE/MFE ANALYSIS SUMMARY - March 20, 2026 (Magic 20 & 30)")
print("=" * 70)
print(f"Total Positions Analyzed: {len(df)}")
print(f"Data Quality: {(df['data_quality_score']=='High').sum()} High, {(df['data_quality_score']=='Medium').sum()} Medium, {(df['data_quality_score']=='Low').sum()} Low")

# Split by strategy
hr20 = df[df['magic_number'] == 20]
hr30 = df[df['magic_number'] == 30]

print(f"\nStrategy Breakdown:")
print(f"  HR10 (Magic 20): {len(hr20)} positions")
print(f"  HR05 (Magic 30): {len(hr30)} positions")

print("\n" + "=" * 70)
print("MAE/MFE STATISTICS")
print("=" * 70)
print(f"{'Metric':<30} {'HR10 (Magic 20)':>18} {'HR05 (Magic 30)':>18} {'Combined':>15}")
print("-" * 70)

metrics = [
    ('Avg MAE (points)', 'mae_points'),
    ('Avg MFE (points)', 'mfe_points'),
    ('Avg Efficiency Ratio', 'efficiency_ratio'),
    ('Avg MFE Capture %', 'mfe_capture_pct'),
    ('Avg Actual Points', 'actual_points'),
    ('Avg Normalized P/L ($)', 'normalized_net_pl'),
]

for label, col in metrics:
    v20 = hr20[col].mean() if len(hr20) > 0 else 0
    v30 = hr30[col].mean() if len(hr30) > 0 else 0
    v_all = df[col].mean()
    print(f"{label:<30} {v20:>18.2f} {v30:>18.2f} {v_all:>15.2f}")

print("\n" + "=" * 70)
print("DURATION & TIME ANALYSIS")
print("=" * 70)

print(f"\nTime to MAE/MFE:")
print(f"  Avg Time to MAE: {df['time_to_mae_sec'].mean():.1f} seconds")
print(f"  Avg Time to MFE: {df['time_to_mfe_sec'].mean():.1f} seconds")
print(f"  MAE before MFE: {(df['time_to_mae_sec'] < df['time_to_mfe_sec']).sum()}/{len(df)} ({(df['time_to_mae_sec'] < df['time_to_mfe_sec']).mean()*100:.1f}%)")

print(f"\nCheckpoint Survival:")
print(f"  Reached 2 min: {df['reached_2min'].sum()}/{len(df)} ({df['reached_2min'].mean()*100:.1f}%)")
print(f"  Reached 5 min: {df['reached_5min'].sum()}/{len(df)} ({df['reached_5min'].mean()*100:.1f}%)")
print(f"  Reached 15 min: {df['reached_15min'].sum()}/{len(df)} ({df['reached_15min'].mean()*100:.1f}%)")

print("\n" + "=" * 70)
print("DIRECTION ANALYSIS")
print("=" * 70)

for direction in ['BUY', 'SELL']:
    subset = df[df['direction'] == direction]
    if len(subset) > 0:
        print(f"\n{direction} ({len(subset)} positions):")
        print(f"  Win Rate: {(subset['normalized_net_pl'] > 0).sum()}/{len(subset)} ({(subset['normalized_net_pl'] > 0).mean()*100:.1f}%)")
        print(f"  Avg Normalized P/L: ${subset['normalized_net_pl'].mean():.2f}")
        print(f"  Avg MAE: {subset['mae_points'].mean():.2f} points")
        print(f"  Avg MFE: {subset['mfe_points'].mean():.2f} points")

print("\n" + "=" * 70)
print("MFE CAPTURE EFFICIENCY DISTRIBUTION")
print("=" * 70)

capture_bins = [
    (float('-inf'), 0, "Negative (Stopped out before MFE)"),
    (0, 25, "0-25% (Poor capture)"),
    (25, 50, "25-50% (Below average)"),
    (50, 75, "50-75% (Average)"),
    (75, 100, "75-100% (Good)"),
    (100, 150, "100-150% (Excellent - captured more than MFE)"),
    (150, float('inf'), ">150% (Exceptional)")
]

for min_val, max_val, label in capture_bins:
    count = ((df['mfe_capture_pct'] >= min_val) & (df['mfe_capture_pct'] < max_val)).sum()
    pct = count / len(df) * 100
    bar = "#" * int(pct / 3)
    print(f"  {label:<45}: {count:>3} ({pct:>5.1f}%) {bar}")

print("\n" + "=" * 70)
print("HIGH MAE ALERT (>10 points)")
print("=" * 70)

high_mae = df[df['mae_points'] > 10].copy()
if len(high_mae) > 0:
    print(f"\n{len(high_mae)} positions with MAE > 10 points:")
    print(f"{'Time':<12} {'Dir':<5} {'MAE':>8} {'MFE':>8} {'Captured':>10} {'Net PL':>10}")
    print("-" * 70)
    for _, row in high_mae.head(10).iterrows():
        time_str = row['open_time'][11:19]
        print(f"{time_str:<12} {row['direction']:<5} {row['mae_points']:>8.2f} {row['mfe_points']:>8.2f} {row['actual_points']:>10.2f} ${row['normalized_net_pl']:>9.2f}")
else:
    print("No positions with MAE > 10 points")

print("\n" + "=" * 70)
print("KEY INSIGHTS")
print("=" * 70)
print(f"""
1. EFFICIENCY RATIO: {df['efficiency_ratio'].mean():.2f}
   - For every 1 point of risk (MAE), positions had {df['efficiency_ratio'].mean():.2f} points of reward potential (MFE)
   - {'Favorable' if df['efficiency_ratio'].mean() > 1 else 'Unfavorable'} risk:reward structure

2. MFE CAPTURE: {df['mfe_capture_pct'].mean():.1f}%
   - On average, positions captured {df['mfe_capture_pct'].mean():.1f}% of maximum favorable excursion
   - {'Poor execution' if df['mfe_capture_pct'].mean() < 50 else 'Acceptable execution' if df['mfe_capture_pct'].mean() < 80 else 'Good execution'}

3. TIME TO MFE vs MAE:
   - MFE occurs at {df['time_to_mfe_sec'].mean():.0f}s on average
   - MAE occurs at {df['time_to_mae_sec'].mean():.0f}s on average
   - {'MAE typically comes first - consider faster exits' if df['time_to_mae_sec'].mean() < df['time_to_mfe_sec'].mean() else 'MFE typically comes first - good for momentum'}

4. CHECKPOINT SURVIVAL:
   - {(~df['reached_2min']).sum()} positions ({(~df['reached_2min']).mean()*100:.1f}%) closed before 2 min
   - These early exits had ${df[~df['reached_2min']]['normalized_net_pl'].mean():.2f} avg normalized P/L
""")

print("\nCSV file saved: data/mae_mfe_march20_magic20_30.csv")
print("Ready for further analysis or import into Excel/Tableau")
