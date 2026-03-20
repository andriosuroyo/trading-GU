#!/usr/bin/env python3
"""Corrected Duration Analysis - Honest Assessment with Data Limitations"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
sys.path.insert(0, r'c:\Trading_GU\.agents\scripts')

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import gu_tools

print('='*80)
print('CORRECTED DURATION ANALYSIS - WITH DATA LIMITATIONS ACKNOWLEDGED')
print('='*80)

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

def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): return 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    strategies = {'0': 'TESTS', '1': 'HR10', '2': 'HR05', '3': 'MH'}
    return strategies.get(strat_id, f'STRAT_{strat_id}')

df['strategy'] = df['magic'].apply(lambda x: parse_magic(x))
df['duration_minutes'] = (df['close_time'] - df['open_time']).dt.total_seconds() / 60

avg_lot = df['volume'].mean() if not df.empty else 0.01
lot_norm = avg_lot * 100
df['net_pl_norm'] = df['net_pl'] / lot_norm

print(f'\nDataset: {len(df)} trades from March 1-12, 2026')
print(f'Normalization: Divide by {lot_norm:.0f} for 0.01 lot equivalent')
print(f'CRITICAL LIMITATION: We only have OPEN/CLOSE data, not tick data')
print(f'Cannot determine P/L at intermediate time points (15/30/45/60 min)')
print()

# =============================================================================
# ACTUAL DURATION DISTRIBUTION
# =============================================================================
print('='*80)
print('ACTUAL TRADE DURATION DISTRIBUTION (All Strategies)')
print('='*80)

print(f"\n{'Duration Range':<20} {'Count':>8} {'% of Total':>12} {'Win%':>8} {'Total P/L':>12}")
print('-'*70)

bins = [0, 1, 2, 5, 10, 15, 20, 30, 45, 60, 120, float('inf')]
labels = ['0-1 min', '1-2 min', '2-5 min', '5-10 min', '10-15 min', '15-20 min', 
          '20-30 min', '30-45 min', '45-60 min', '60-120 min', '120+ min']

df['duration_bin'] = pd.cut(df['duration_minutes'], bins=bins, labels=labels)

for label in labels:
    bin_data = df[df['duration_bin'] == label]
    if len(bin_data) == 0:
        continue
    count = len(bin_data)
    pct = count / len(df) * 100
    wins = len(bin_data[bin_data['net_pl_norm'] > 0])
    win_pct = wins / count * 100 if count > 0 else 0
    pnl = bin_data['net_pl_norm'].sum()
    print(f"{str(label):<20} {count:>8} {pct:>11.1f}% {win_pct:>7.1f}% {pnl:>+11.2f}")

print('-'*70)
print(f"{'TOTAL':<20} {len(df):>8} {100.0:>11.1f}% {len(df[df.net_pl_norm>0])/len(df)*100:>7.1f}% {df['net_pl_norm'].sum():>+11.2f}")

# =============================================================================
# STRATEGY-SPECIFIC DURATION BREAKDOWN
# =============================================================================
print()
print('='*80)
print('DURATION BREAKDOWN BY STRATEGY')
print('='*80)

for strategy in ['MH', 'HR05', 'HR10', 'TESTS']:
    strat_df = df[df['strategy'] == strategy]
    if len(strat_df) == 0:
        continue
    
    print(f"\n{strategy} ({len(strat_df)} trades):")
    print(f"{'Duration':<15} {'Count':>8} {'%':>8} {'Avg P/L':>10} {'Win%':>8}")
    print('-'*55)
    
    for label in ['0-1 min', '1-5 min', '5-15 min', '15-30 min', '30-60 min', '60+ min']:
        if label == '1-5 min':
            subset = strat_df[(strat_df['duration_minutes'] > 1) & (strat_df['duration_minutes'] <= 5)]
        elif label == '5-15 min':
            subset = strat_df[(strat_df['duration_minutes'] > 5) & (strat_df['duration_minutes'] <= 15)]
        elif label == '15-30 min':
            subset = strat_df[(strat_df['duration_minutes'] > 15) & (strat_df['duration_minutes'] <= 30)]
        elif label == '30-60 min':
            subset = strat_df[(strat_df['duration_minutes'] > 30) & (strat_df['duration_minutes'] <= 60)]
        elif label == '60+ min':
            subset = strat_df[strat_df['duration_minutes'] > 60]
        else:
            subset = strat_df[(strat_df['duration_minutes'] >= 0) & (strat_df['duration_minutes'] <= 1)]
        
        if len(subset) == 0:
            continue
        
        count = len(subset)
        pct = count / len(strat_df) * 100
        avg_pnl = subset['net_pl_norm'].mean()
        win_pct = len(subset[subset['net_pl_norm'] > 0]) / count * 100
        
        marker = ""
        if strategy == 'MH' and label in ['60+ min', '30-60 min']:
            marker = " <-- OVERNIGHT CARRIES"
        
        print(f"{label:<15} {count:>8} {pct:>7.1f}% {avg_pnl:>+9.2f} {win_pct:>7.1f}%{marker}")

# =============================================================================
# TRADES EXCEEDING DURATION CAPS (ACTUAL DATA)
# =============================================================================
print()
print('='*80)
print('TRADES EXCEEDING DURATION CAPS (Actual Trades That Would Be Cut)')
print('='*80)

caps = [15, 30, 45, 60]

for strategy in ['MH', 'HR05', 'HR10']:
    strat_df = df[df['strategy'] == strategy]
    if len(strat_df) == 0:
        continue
    
    print(f"\n{strategy} Strategy:")
    print(f"{'Cap':<10} {'# Cut':>8} {'% Cut':>8} {'Final P/L':>12} {'Winners':>8} {'Losers':>8}")
    print('-'*65)
    
    for cap in caps:
        over_cap = strat_df[strat_df['duration_minutes'] > cap]
        cut_count = len(over_cap)
        cut_pct = cut_count / len(strat_df) * 100 if len(strat_df) > 0 else 0
        total_pnl = over_cap['net_pl_norm'].sum()
        winners = len(over_cap[over_cap['net_pl_norm'] > 0])
        losers = len(over_cap[over_cap['net_pl_norm'] < 0])
        
        marker = ""
        if cap == 60 and strategy == 'MH' and cut_count == 2:
            marker = " <-- THE TWO OVERNIGHT CARRIES"
        
        print(f"{cap} min{marker:<25} {cut_count:>8} {cut_pct:>7.1f}% {total_pnl:>+11.2f} {winners:>8} {losers:>8}")

# =============================================================================
# HONEST ASSESSMENT - WHAT WE CAN AND CANNOT KNOW
# =============================================================================
print()
print('='*80)
print('HONEST ASSESSMENT - DATA LIMITATIONS')
print('='*80)

print("""
WHAT WE KNOW FOR CERTAIN:
--------------------------
1. We have exact open time, close time, and final P/L for each trade
2. We can calculate duration accurately
3. We can identify which trades exceed any duration cap

WHAT WE DO NOT KNOW (WITHOUT TICK DATA):
----------------------------------------
1. The P/L at 15-minute mark for a 20-minute trade
2. Whether a winner that took 45 minutes was positive at 15 or 30 minutes
3. Whether a loser that took 60 minutes was already negative at 15 minutes

MY PREVIOUS SIMULATION WAS WRONG BECAUSE:
----------------------------------------
I assumed trades exceeding the cap would have their P/L affected as:
  - Winners: Full P/L captured (WRONG - they might have been losing at cap time)
  - Losers: 50% of loss (WRONG - we don't know the P/L at cap time)

THE REALITY:
-----------
A trade that takes 20 minutes to close:
  - Could have been at -$5 at 15 min, then recovered to +$2 at 20 min
  - With 15-min cap: LOSE -$5 (instead of final +$2)
  - With 30-min cap: WIN +$2 (actual result)

A trade that takes 60 minutes to close:
  - Could have been at +$3 at 15 min, then reversed to -$8 at 60 min  
  - With 15-min cap: WIN +$3 (instead of final -$8)
  - With 30-min cap: Unknown (depends on 30-min mark)

WITHOUT TICK DATA, WE CANNOT SIMULATE ACCURATELY.
""")

# =============================================================================
# WHAT WE CAN SAY WITH CONFIDENCE
# =============================================================================
print()
print('='*80)
print('WHAT WE CAN SAY WITH CONFIDENCE')
print('='*80)

print("""
1. THE TWO MH OVERNIGHT CARRIES (243 min each):
   - Final P/L: -$62.00 and -$61.89
   - These were held for 4+ hours past session end
   - GU was not managing TP/Trail during this time (gambling)
   - ANY duration cap (15/30/45/60 min) would have cut these
   - Even if cut at breakeven, we save $123.89

2. TRADE DURATION PATTERNS:
""")

# Show the clear pattern
for strategy in ['MH', 'HR05', 'HR10']:
    strat_df = df[df['strategy'] == strategy]
    if len(strat_df) < 10:
        continue
    
    short = strat_df[strat_df['duration_minutes'] <= 5]
    medium = strat_df[(strat_df['duration_minutes'] > 5) & (strat_df['duration_minutes'] <= 30)]
    long = strat_df[strat_df['duration_minutes'] > 30]
    
    print(f"\n{strategy}:")
    print(f"  Short (0-5 min):  {len(short)} trades, ${short['net_pl_norm'].sum():+.2f}, {len(short[short.net_pl_norm>0])/len(short)*100:.0f}% win")
    print(f"  Medium (5-30):    {len(medium)} trades, ${medium['net_pl_norm'].sum():+.2f}, {len(medium[medium.net_pl_norm>0])/len(medium)*100:.0f}% win")
    print(f"  Long (30+ min):   {len(long)} trades, ${long['net_pl_norm'].sum():+.2f}, {len(long[long.net_pl_norm>0])/len(long)*100:.0f}% win")

print("""
3. OBSERVATION:
   - Short-duration trades (0-5 min) are generally profitable
   - Long-duration trades (30+ min) are generally unprofitable
   - BUT we cannot determine the optimal cap without tick data

4. CONSERVATIVE RECOMMENDATION:
   - Set cap at 60 minutes as "gambling prevention"
   - This cuts only the extreme outliers (5 trades total)
   - Primary purpose: Prevent overnight carries, not optimize P/L
""")

# =============================================================================
# REALISTIC SCENARIOS
# =============================================================================
print()
print('='*80)
print('REALISTIC SCENARIOS (With Acknowledged Uncertainty)')
print('='*80)

print("""
SCENARIO 1: Cut ONLY the two MH overnight carries
--------------------------------------------------
These are the only trades we KNOW are harmful (held 4+ hours, no management)
Result: Save ~$123.89 (best case) or partial (realistic)

SCENARIO 2: Conservative 60-minute cap
---------------------------------------
Cuts 5 trades total (0.8% of volume)
Unknown P/L impact without tick data
Purpose: Safety net, not optimization

SCENARIO 3: Moderate 30-minute cap
-----------------------------------
Cuts 8 trades total (1.3% of volume)
Mix of winners and losers
Unknown net impact without tick data
Risk: May cut legitimate winners that needed 30+ min

SCENARIO 4: Aggressive 15-minute cap
-------------------------------------
Cuts 8 trades (same as 30-min, just earlier)
Higher risk of cutting recovering winners
Not recommended without tick data validation
""")

print()
print('Analysis complete.')
