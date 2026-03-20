#!/usr/bin/env python3
"""
Corrected MFE/MAE Analysis - Asia Session First Positions
Understanding: 1 point = $1.00 on 0.01 lot, $10.00 on 0.10 lot
"""
import pandas as pd
import numpy as np

# Load the results
df = pd.read_csv('asia_mfe_mae_analysis.csv')

# Current lot size is 0.10, normalize MFE to 0.01 lot equivalent
LOT_SIZE = 0.10
POINT_VALUE_001 = 0.01  # $0.01 per 0.01 lot per point
POINT_VALUE_010 = 0.10  # $0.10 per 0.10 lot per point

print("="*100)
print("CORRECTED MFE/MAE ANALYSIS - ASIA SESSION FIRST POSITIONS")
print("="*100)

# Recalculate MFE in dollars (positions are 0.10 lot)
df['mfe_dollars_010lot'] = df['mfe_points'] * POINT_VALUE_010
df['mae_dollars_010lot'] = df['mae_points'] * POINT_VALUE_010

# Normalize to 0.01 lot for consistent comparison
df['mfe_norm'] = df['mfe_dollars_010lot'] / 10  # Divide by 10
df['mae_norm'] = df['mae_dollars_010lot'] / 10
df['actual_pl_norm'] = df['actual_pl'] / 10

# Get 30-minute data for full analysis
df_30 = df[df['holding_min'] == 30].copy()

print(f"\nDataset: {len(df_30)} first positions (0.10 lot)")
print(f"Normalized to 0.01 lot equivalent for comparison")

# Summary statistics
print("\n" + "-"*80)
print("MFE vs ACTUAL P&L CAPTURE (Normalized to 0.01 lot)")
print("-"*80)
print(f"{'Metric':<30} {'Mean':>12} {'Median':>12} {'Max':>12}")
print("-"*80)
print(f"{'MFE (Max Favorable Excursion)':<30} {df_30['mfe_norm'].mean():>11.2f}$ {df_30['mfe_norm'].median():>11.2f}$ {df_30['mfe_norm'].max():>11.2f}$")
print(f"{'MAE (Max Adverse Excursion)':<30} {df_30['mae_norm'].mean():>11.2f}$ {df_30['mae_norm'].median():>11.2f}$ {df_30['mae_norm'].max():>11.2f}$")
print(f"{'Actual P&L Captured':<30} {df_30['actual_pl_norm'].mean():>11.2f}$ {df_30['actual_pl_norm'].median():>11.2f}$ {df_30['actual_pl_norm'].max():>11.2f}$")

# MFE Capture Rate
df_30['mfe_capture_pct'] = (df_30['actual_pl_norm'] / df_30['mfe_norm'] * 100).replace([np.inf, -np.inf], 0)
df_30['mfe_capture_pct'] = df_30['mfe_capture_pct'].fillna(0)

print(f"\n{'MFE Capture Rate':<30} {df_30['mfe_capture_pct'].mean():>11.1f}% {df_30['mfe_capture_pct'].median():>11.1f}% {df_30['mfe_capture_pct'].max():>11.1f}%")

# Winners vs Losers
winners = df_30[df_30['actual_pl_norm'] > 0]
losers = df_30[df_30['actual_pl_norm'] < 0]

print("\n" + "-"*80)
print("WINNERS vs LOSERS (Normalized to 0.01 lot)")
print("-"*80)
print(f"Winners: {len(winners)} ({len(winners)/len(df_30)*100:.1f}%)")
print(f"  - Avg MFE: ${winners['mfe_norm'].mean():.2f}")
print(f"  - Avg MAE: ${winners['mae_norm'].mean():.2f}")
print(f"  - Avg P&L: ${winners['actual_pl_norm'].mean():.2f}")
print(f"  - MFE Capture: {winners['mfe_capture_pct'].mean():.1f}%")

print(f"\nLosers: {len(losers)} ({len(losers)/len(df_30)*100:.1f}%)")
print(f"  - Avg MFE: ${losers['mfe_norm'].mean():.2f}")
print(f"  - Avg MAE: ${losers['mae_norm'].mean():.2f}")
print(f"  - Avg P&L: ${losers['actual_pl_norm'].mean():.2f}")
print(f"  - MFE Capture: {losers['mfe_capture_pct'].mean():.1f}%")

# ============================================================================
# SIMULATION 1: Time-based exits for positions failing $0.20 MFE
# ============================================================================
print("\n" + "="*100)
print("SIMULATION 1: Time-Based Exits (Normalized to 0.01 lot)")
print("Rule: If MFE >= $0.20 within time limit -> Take $0.20 profit")
print("      If MFE < $0.20 at time limit -> Exit at market price")
print("="*100)

sim_results = []
for minutes in range(2, 31):
    period_data = df[df['holding_min'] == minutes].copy()
    
    if period_data.empty:
        continue
    
    # Normalize
    period_data['mfe_norm'] = period_data['mfe_points'] * POINT_VALUE_010 / 10
    period_data['pnl_norm'] = period_data['pnl_at_exit'] * POINT_VALUE_010 / 10
    
    # Check if $0.20 MFE was reached
    period_data['hit_20mfe'] = period_data['mfe_norm'] >= 0.20
    
    # Simulate P&L
    period_data['sim_pnl'] = period_data.apply(
        lambda row: 0.20 if row['hit_20mfe'] else row['pnl_norm'], axis=1
    )
    
    total_pnl = period_data['sim_pnl'].sum()
    hit_count = period_data['hit_20mfe'].sum()
    total_count = len(period_data)
    
    sim_results.append({
        'time_limit': minutes,
        'total_pnl': total_pnl,
        'hit_20mfe': int(hit_count),
        'missed': int(total_count - hit_count),
        'hit_rate': hit_count / total_count * 100,
        'avg_pnl': total_pnl / total_count
    })

sim_df = pd.DataFrame(sim_results)

print("\nTime Limit | Hit $0.20 | Missed | Hit Rate | Total P&L | Avg P&L")
print("-" * 75)
for _, row in sim_df.iterrows():
    marker = " <-- BEST" if row['total_pnl'] == sim_df['total_pnl'].max() else ""
    print(f"{row['time_limit']:>10}min | {row['hit_20mfe']:>9} | {row['missed']:>6} | "
          f"{row['hit_rate']:>7.1f}% | ${row['total_pnl']:>7.2f} | ${row['avg_pnl']:>6.2f}{marker}")

best_time = sim_df.loc[sim_df['total_pnl'].idxmax()]
print(f"\n[OPTIMAL] Time Limit: {best_time['time_limit']:.0f} minutes")
print(f"  - Total P&L: ${best_time['total_pnl']:.2f} (vs ${df_30['actual_pl_norm'].sum():.2f} actual)")
print(f"  - Improvement: +${best_time['total_pnl'] - df_30['actual_pl_norm'].sum():.2f}")

# ============================================================================
# SIMULATION 2: Optimal TargetProfitMoney with ATR60 matching
# ============================================================================
print("\n" + "="*100)
print("SIMULATION 2: TargetProfitMoney Optimization")
print("="*100)

# Get ATR60 values
pos_data = df[df['holding_min'] == 30][['pos_id', 'atr_60', 'mfe_norm', 'actual_pl_norm']].copy()
avg_atr = pos_data['atr_60'].mean()

print(f"\nAverage ATR(60) in Asia: {avg_atr:.2f} points (${avg_atr * POINT_VALUE_010 / 10:.2f} on 0.01 lot)")

# Test different TargetProfit values
tp_values = [x * 0.10 for x in range(2, 21)]  # $0.20 to $2.00
tp_results = []

for tp in tp_values:
    # Check how many positions would hit this TP
    hit_mask = pos_data['mfe_norm'] >= tp
    hit_count = hit_mask.sum()
    total_count = len(pos_data)
    
    # For hits: get TP profit
    # For misses: get actual loss (or time-exit P&L)
    # Use pnl_at_exit for misses
    misses = pos_data[~hit_mask]
    hit_pnl = hit_count * tp
    
    # For misses, use their actual P&L (they didn't hit TP, so they exited somehow)
    miss_pnl = misses['actual_pl_norm'].sum() if len(misses) > 0 else 0
    
    total_pnl = hit_pnl + miss_pnl
    
    # ATR multiplier
    atr_dollar = avg_atr * POINT_VALUE_010 / 10
    atr_mult = tp / atr_dollar if atr_dollar > 0 else 0
    
    tp_results.append({
        'target_profit': tp,
        'atr_mult': atr_mult,
        'hit_count': int(hit_count),
        'hit_rate': hit_count / total_count * 100,
        'total_pnl': total_pnl,
        'avg_pnl': total_pnl / total_count
    })

tp_df = pd.DataFrame(tp_results)

print("\nTargetProfit | ATR Mult | Hit Rate | Total P&L | Avg P&L")
print("-" * 65)
for _, row in tp_df.iterrows():
    marker = " <-- BEST" if row['total_pnl'] == tp_df['total_pnl'].max() else ""
    print(f"${row['target_profit']:>10.2f} | {row['atr_mult']:>8.2f}x | {row['hit_rate']:>7.1f}% | "
          f"${row['total_pnl']:>7.2f} | ${row['avg_pnl']:>6.2f}{marker}")

best_tp = tp_df.loc[tp_df['total_pnl'].idxmax()]
print(f"\n[OPTIMAL] TargetProfitMoney: ${best_tp['target_profit']:.2f}")
print(f"  - ATR60 Multiplier: {best_tp['atr_mult']:.2f}x")
print(f"  - Hit Rate: {best_tp['hit_rate']:.1f}%")
print(f"  - Total P&L: ${best_tp['total_pnl']:.2f}")

# Save results
sim_df.to_csv('asia_simulation1_time_exit.csv', index=False)
tp_df.to_csv('asia_simulation2_target_profit.csv', index=False)
print("\n[SAVED] Results saved to CSV files")
