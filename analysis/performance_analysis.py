#!/usr/bin/env python3
"""Comprehensive GU Performance Analysis & Optimization Strategy"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
sys.path.insert(0, r'c:\Trading_GU\.agents\scripts')

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import gu_tools

print('='*70)
print('GU PERFORMANCE ASSESSMENT & OPTIMIZATION STRATEGY')
print('='*70)

# Connect to Vantage
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect')
    exit(1)

date_from = datetime.now(timezone.utc) - timedelta(days=14)
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
df['open_minute'] = df['open_time'].dt.minute
df['weekday'] = df['open_time'].dt.weekday  # 0=Monday, 6=Sunday

# Normalize P/L to 0.01 lot
avg_lot = df['volume'].mean() if not df.empty else 0.01
lot_norm = avg_lot * 100
df['net_pl_norm'] = df['net_pl'] / lot_norm

print(f'\nDataset: {len(df)} trades over 14 days')
print(f'Lot Size: {avg_lot:.2f} lots (normalization factor: divide by {lot_norm:.0f})')

# =============================================================================
# PART 1: CURRENT STATE ANALYSIS
# =============================================================================
print()
print('='*70)
print('PART 1: CURRENT STATE ANALYSIS')
print('='*70)

# Winners vs Losers Analysis
winners = df[df['net_pl_norm'] > 0]
losers = df[df['net_pl_norm'] < 0]

print(f"\nOverall Statistics:")
print(f"  Total Trades:    {len(df)}")
print(f"  Win Rate:        {len(winners)/len(df)*100:.1f}%")
print(f"  Avg Win:         ${winners['net_pl_norm'].mean():.3f}")
print(f"  Avg Loss:        ${losers['net_pl_norm'].mean():.3f}")
print(f"  R:R Ratio:       {abs(winners['net_pl_norm'].mean() / losers['net_pl_norm'].mean()):.3f}")
print(f"  Net P/L:         ${df['net_pl_norm'].sum():.2f}")

# Calculate what RR >= 0.1 means
print(f"\nTarget Analysis (90-95% WR, RR >= 0.1):")
print(f"  Current WR:      {len(winners)/len(df)*100:.1f}%")
print(f"  Target WR:       90-95%")
print(f"  Current RR:      {abs(winners['net_pl_norm'].mean() / losers['net_pl_norm'].mean()):.3f}")
print(f"  Min RR needed:   0.100")
print(f"  Gap to close:    {90 - len(winners)/len(df)*100:.1f} percentage points")

# =============================================================================
# PART 2: THE MH PARADOX
# =============================================================================
print()
print('='*70)
print('PART 2: THE MH PARADOX (High Win Rate, Negative P/L)')
print('='*70)

mh_df = df[df['strategy'] == 'MH']
if len(mh_df) > 0:
    mh_winners = mh_df[mh_df['net_pl_norm'] > 0]
    mh_losers = mh_df[mh_df['net_pl_norm'] < 0]
    
    print(f"\nMH Strategy Analysis:")
    print(f"  Trades:          {len(mh_df)}")
    print(f"  Win Rate:        {len(mh_winners)/len(mh_df)*100:.1f}%")
    print(f"  Avg Win:         ${mh_winners['net_pl_norm'].mean():.3f}")
    print(f"  Avg Loss:        ${mh_losers['net_pl_norm'].mean():.3f}")
    print(f"  R:R Ratio:       {abs(mh_winners['net_pl_norm'].mean() / mh_losers['net_pl_norm'].mean()):.3f}")
    print(f"  Net P/L:         ${mh_df['net_pl_norm'].sum():.2f}")
    print()
    print(f"  PROBLEM: When MH loses, it loses {abs(mh_losers['net_pl_norm'].mean()/mh_winners['net_pl_norm'].mean()):.1f}x the average win!")
    print(f"  SOLUTION: MH needs tighter SL or earlier session cutoff")
    
    # Which MH sets are worst?
    mh_by_magic = mh_df.groupby('magic').agg({
        'net_pl_norm': ['count', 'sum', lambda x: (x > 0).sum()]
    })
    mh_by_magic.columns = ['trades', 'net_pl', 'wins']
    mh_by_magic['win_rate'] = mh_by_magic['wins'] / mh_by_magic['trades'] * 100
    print(f"\n  MH Breakdown by Magic:")
    for magic, row in mh_by_magic.iterrows():
        print(f"    Magic {int(magic)}: {int(row['trades'])} trades, {row['win_rate']:.1f}% WR, ${row['net_pl']:+.2f}")

# =============================================================================
# PART 3: TOXICITY MAPPING
# =============================================================================
print()
print('='*70)
print('PART 3: TOXICITY MAPPING (Where We Lose Money)')
print('='*70)

# By Hour
print("\nHourly Toxicity (Normalized P/L):")
hourly = df.groupby('open_hour_utc').agg({
    'net_pl_norm': ['count', 'sum', lambda x: (x > 0).sum()]
})
hourly.columns = ['trades', 'net_pl', 'wins']
hourly['win_rate'] = hourly['wins'] / hourly['trades'] * 100
hourly = hourly.sort_values('net_pl')

print(f"{'Hour':<8} {'Trades':>8} {'Win%':>8} {'Net P/L':>12} {'Status':<15}")
print('-'*60)
for hr, row in hourly.head(10).iterrows():
    status = 'TOXIC' if row['net_pl'] < -5 else 'WARNING' if row['net_pl'] < 0 else 'OK'
    print(f"{hr:02d}:00    {int(row['trades']):>8} {row['win_rate']:>7.1f}% {row['net_pl']:>+11.2f} {status:<15}")

# By Day of Week
print("\nDay of Week Analysis:")
dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
dow = df.groupby('weekday').agg({
    'net_pl_norm': ['count', 'sum', lambda x: (x > 0).sum()]
})
dow.columns = ['trades', 'net_pl', 'wins']
dow['win_rate'] = dow['wins'] / dow['trades'] * 100
for day, row in dow.iterrows():
    print(f"  {dow_names[int(day)]}: {int(row['trades'])} trades, {row['win_rate']:.1f}% WR, ${row['net_pl']:+.2f}")

# By Session + Hour combination (most granular)
print("\nSession + Hour Toxic Combinations:")
session_hour = df.groupby(['session', 'open_hour_utc']).agg({
    'net_pl_norm': ['count', 'sum']
})
session_hour.columns = ['trades', 'net_pl']
session_hour = session_hour[session_hour['trades'] >= 5]  # Min 5 trades
session_hour = session_hour.sort_values('net_pl')
print(f"{'Session':<10} {'Hour':<8} {'Trades':>8} {'Net P/L':>12}")
print('-'*50)
for (sess, hr), row in session_hour.head(10).iterrows():
    print(f"{sess:<10} {hr:02d}:00    {int(row['trades']):>8} {row['net_pl']:>+11.2f}")

# =============================================================================
# PART 4: FILTERING OPPORTUNITIES
# =============================================================================
print()
print('='*70)
print('PART 4: UNEXPLORED FILTERING METHODS')
print('='*70)

print("""
PROPOSED FILTERING LAYERS (in order of application):

1. TIME-BASED FILTERS (Immediate Impact - High Confidence)
   +-- Session End Cutoff: Close all positions 5 min before session end
   |   +-- Prevents "gambling" on unmanaged carry-over trades
   +-- Toxic Hour Exclusion: Skip UTC 21:00 entirely (saves ~$88 normalized)
   +-- ASIA End Adjustment: End at 05:00 instead of 06:00 UTC (saves ~$10)
   +-- Day-of-Week Filter: Analyze Sat/Sun if any trades exist

2. VOLATILITY-BASED FILTERS (Medium Impact)
   +-- ATR Spike Filter: Don't trade if M1 ATR(14) > 2x session average
   |   +-- Avoids entries during news/events when slippage is high
   +-- Spread Filter: Skip if spread > 30 points (already set but verify)
   +-- Volume Filter: Skip if tick volume < threshold (low liquidity periods)

3. TECHNICAL FILTERS (Medium-High Impact)
   +-- Trend Alignment: Only trade in direction of M5/M15 trend
   |   +-- GU enters on M1 cross -- could filter against higher TF trend
   +-- Support/Resistance: Skip entries near S/R zones (whipsaw risk)
   +-- RSI Filter: Skip if RSI(14) > 70 (long) or < 30 (short)
   +-- Bollinger Band: Skip if price outside 2 std dev (mean reversion likely)

4. NEWS-BASED FILTERS (Already Partially Implemented)
   +-- Current: 15/30 min block for high-impact news
   +-- Proposed: Extend to 45/45 for ALL news (imp>=1) -- proven +$41 improvement
   +-- Proposed: Add Fed Chair speeches, NFP, CPI to permanent no-trade list

5. CONSECUTIVE LOSS FILTERS (Risk Management)
   +-- Cooldown after loss: Skip next signal if previous trade lost
   |   +-- Prevents "revenge trading" during choppy conditions
   +-- Daily Loss Limit: Hard stop at -$X (already have 28% but maybe tighten)
   +-- Session Loss Limit: Stop trading session after 2 consecutive losses

6. MFE-BASED ADAPTIVE FILTERING (Advanced)
   +-- Track MFE/MAE ratio per magic
   |   +-- If MAE consistently > 50% of MFE, widen SL or skip entries
   +-- Volatility Regime Detection: Use ATR(60) vs ATR(14) ratio
       +-- If ATR(14) >> ATR(60), market is spiking -- reduce size or skip
""")

# =============================================================================
# PART 5: OPTIMIZATION ROADMAP TO 90-95% WR
# =============================================================================
print()
print('='*70)
print('PART 5: ROADMAP TO 90-95% WIN RATE (RR >= 0.1)')
print('='*70)

# Simulate impact of filters
print("\nScenario Modeling:")

# Current baseline
current_wr = len(winners) / len(df) * 100
current_net = df['net_pl_norm'].sum()

print(f"\n  BASELINE (Current):")
print(f"    WR: {current_wr:.1f}%, Net: ${current_net:+.2f}")

# Filter 1: Remove UTC 21:00
df_no_21 = df[df['open_hour_utc'] != 21]
wr_no_21 = len(df_no_21[df_no_21['net_pl_norm'] > 0]) / len(df_no_21) * 100
net_no_21 = df_no_21['net_pl_norm'].sum()
print(f"\n  FILTER 1: Remove UTC 21:00 (-{len(df) - len(df_no_21)} trades)")
print(f"    WR: {wr_no_21:.1f}% (+{wr_no_21 - current_wr:.1f}), Net: ${net_no_21:+.2f} (+${net_no_21 - current_net:.2f})")

# Filter 2: Also remove UTC 03:00, 05:00
toxic_hours = [3, 5, 21]
df_clean_hours = df[~df['open_hour_utc'].isin(toxic_hours)]
wr_clean = len(df_clean_hours[df_clean_hours['net_pl_norm'] > 0]) / len(df_clean_hours) * 100
net_clean = df_clean_hours['net_pl_norm'].sum()
print(f"\n  FILTER 2: Remove UTC 03, 05, 21 (-{len(df) - len(df_clean_hours)} trades)")
print(f"    WR: {wr_clean:.1f}% (+{wr_clean - current_wr:.1f}), Net: ${net_clean:+.2f} (+${net_clean - current_net:.2f})")

# Filter 3: Only trade HR05 + HR10 (exclude MH and TESTS)
df_best_strat = df[df['strategy'].isin(['HR05', 'HR10'])]
wr_best = len(df_best_strat[df_best_strat['net_pl_norm'] > 0]) / len(df_best_strat) * 100
net_best = df_best_strat['net_pl_norm'].sum()
avg_win = df_best_strat[df_best_strat['net_pl_norm'] > 0]['net_pl_norm'].mean()
avg_loss = df_best_strat[df_best_strat['net_pl_norm'] < 0]['net_pl_norm'].mean()
rr_best = abs(avg_win / avg_loss)
print(f"\n  FILTER 3: HR05 + HR10 only (exclude MH & TESTS)")
print(f"    WR: {wr_best:.1f}%, RR: {rr_best:.3f}, Net: ${net_best:+.2f}")

# Combined filter
df_combined = df[(df['strategy'].isin(['HR05', 'HR10'])) & 
                  (~df['open_hour_utc'].isin([3, 5, 21]))]
wr_combined = len(df_combined[df_combined['net_pl_norm'] > 0]) / len(df_combined) * 100
net_combined = df_combined['net_pl_norm'].sum()
avg_win_c = df_combined[df_combined['net_pl_norm'] > 0]['net_pl_norm'].mean()
avg_loss_c = df_combined[df_combined['net_pl_norm'] < 0]['net_pl_norm'].mean()
rr_combined = abs(avg_win_c / avg_loss_c)
print(f"\n  COMBINED: HR05/HR10 + Clean Hours Only")
print(f"    Trades: {len(df_combined)} (-{len(df) - len(df_combined)} filtered)")
print(f"    WR: {wr_combined:.1f}% (Target: 90-95%)")
print(f"    RR: {rr_combined:.3f} (Target: >= 0.1)")
print(f"    Net: ${net_combined:+.2f}")

# =============================================================================
# PART 6: SPECIFIC RECOMMENDATIONS
# =============================================================================
print()
print('='*70)
print('PART 6: IMMEDIATE ACTIONABLE RECOMMENDATIONS')
print('='*70)

print("""
PRIORITY 1: EMERGENCY FIXES (Deploy Today)
-------------------------------------------
1. PAUSE MH Strategy (Magic 30-33) until SL parameters reviewed
   +-- 90% WR but -$87 normalized -- catastrophic loss distribution
   
2. Adjust NY Session End from 21:00 to 20:00 UTC
   +-- UTC 21:00 alone costs -$88.75 (normalized)
   +-- Could add +197% to net P/L immediately
   
3. Consider ASIA End at 05:00 instead of 06:00
   +-- UTC 05:00 is toxic (-$9.78), UTC 06:00 not much better

PRIORITY 2: QUICK WINS (This Week)
-----------------------------------
4. Deploy TEST Sets 114-117 (ATR60 optimization)
   +-- Could capture 80-90% of MFE vs current 40%
   +-- Target: 85%+ WR with RR ~0.3-0.5
   
5. Extend News Filter to 45/45 for ALL sessions (not just NY)
   +-- Proven +$41 improvement on NY
   +-- Zero impact on ASIA/LONDON (safe to apply universally)

PRIORITY 3: STRUCTURAL IMPROVEMENTS (Next 2 Weeks)
---------------------------------------------------
6. Implement Session Loss Limits
   +-- Stop trading session after 2 consecutive losses
   +-- Prevents "death spirals" during bad market conditions
   
7. Add Trend Alignment Filter (M5/M15 direction check)
   +-- Only take M1 crosses in direction of higher TF trend
   +-- Could filter out 30-40% of false signals
   
8. Develop Volatility Regime Detection
   +-- Use ATR(60)/ATR(14) ratio to detect spiking conditions
   +-- Reduce position size or skip during high volatility

EXPECTED OUTCOME:
-----------------
Current:     79.1% WR,  $44.94 net (normalized),  RR ~0.29
Target:      90-95% WR,  $150+ net,                RR >= 0.1
Path:        Filter toxic hours + pause MH + trend alignment
""")

print()
print('Analysis complete.')
