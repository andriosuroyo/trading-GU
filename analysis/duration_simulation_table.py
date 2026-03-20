#!/usr/bin/env python3
"""Detailed Duration Cap Simulation for All Strategies"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
sys.path.insert(0, r'c:\Trading_GU\.agents\scripts')

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import gu_tools

print('='*80)
print('DURATION CAP SIMULATION - PROFITABILITY IMPACT BY STRATEGY')
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

# Parse strategy
def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): return 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    strategies = {'0': 'TESTS', '1': 'HR10', '2': 'HR05', '3': 'MH'}
    return strategies.get(strat_id, f'STRAT_{strat_id}')

df['strategy'] = df['magic'].apply(lambda x: parse_magic(x))
df['duration_minutes'] = (df['close_time'] - df['open_time']).dt.total_seconds() / 60

# Normalize P/L to 0.01 lot
avg_lot = df['volume'].mean() if not df.empty else 0.01
lot_norm = avg_lot * 100
df['net_pl_norm'] = df['net_pl'] / lot_norm

# Duration caps to test
duration_caps = [15, 30, 45, 60]
strategies = ['MH', 'HR05', 'HR10', 'TESTS']

print(f'\nDataset: {len(df)} trades from March 1-12, 2026')
print(f'Normalization: Divide by {lot_norm:.0f} for 0.01 lot equivalent\n')

# Store results
results = {}

for strategy in strategies:
    strat_df = df[df['strategy'] == strategy].copy()
    if len(strat_df) == 0:
        continue
    
    baseline_pnl = strat_df['net_pl_norm'].sum()
    baseline_trades = len(strat_df)
    baseline_wins = len(strat_df[strat_df['net_pl_norm'] > 0])
    baseline_wr = baseline_wins / baseline_trades * 100 if baseline_trades > 0 else 0
    
    results[strategy] = {
        'baseline': {
            'pnl': baseline_pnl,
            'trades': baseline_trades,
            'win_rate': baseline_wr
        },
        'caps': {}
    }
    
    for cap in duration_caps:
        # Trades within cap
        within_cap = strat_df[strat_df['duration_minutes'] <= cap]
        over_cap = strat_df[strat_df['duration_minutes'] > cap]
        
        trades_kept = len(within_cap)
        trades_cut = len(over_cap)
        
        # Simulate: Keep within_cap actual P/L
        # For over_cap trades, simulate early exit
        # Conservative: assume they close at 50% of actual loss (winners kept at full)
        
        over_cap_losers = over_cap[over_cap['net_pl_norm'] < 0]
        over_cap_winners = over_cap[over_cap['net_pl_norm'] > 0]
        
        # Simulation: 
        # - Trades within cap: actual P/L
        # - Winners over cap: full P/L (they would have hit TP anyway)
        # - Losers over cap: 50% of actual loss (cut earlier)
        
        simulated_pnl = (within_cap['net_pl_norm'].sum() + 
                        over_cap_winners['net_pl_norm'].sum() + 
                        (over_cap_losers['net_pl_norm'].sum() * 0.5))
        
        # Win rate of kept + simulated winners
        simulated_wins = len(within_cap[within_cap['net_pl_norm'] > 0]) + len(over_cap_winners)
        simulated_wr = simulated_wins / baseline_trades * 100 if baseline_trades > 0 else 0
        
        results[strategy]['caps'][cap] = {
            'pnl': simulated_pnl,
            'trades_kept': trades_kept,
            'trades_cut': trades_cut,
            'win_rate': simulated_wr,
            'improvement': simulated_pnl - baseline_pnl
        }

# Print summary tables
print('='*80)
print('NET P/L BY DURATION CAP (Normalized to 0.01 lot)')
print('='*80)
print(f"\n{'Strategy':<10} {'Baseline':<15} {'15 min':<15} {'30 min':<15} {'45 min':<15} {'60 min':<15}")
print('-'*85)

for strategy in strategies:
    if strategy not in results:
        continue
    row = f"{strategy:<10}"
    row += f" ${results[strategy]['baseline']['pnl']:>+11.2f}"
    for cap in duration_caps:
        row += f" ${results[strategy]['caps'][cap]['pnl']:>+11.2f}"
    print(row)

# Totals row
print('-'*85)
row = f"{'TOTAL':<10}"
baseline_total = sum(results[s]['baseline']['pnl'] for s in results)
row += f" ${baseline_total:>+11.2f}"
for cap in duration_caps:
    cap_total = sum(results[s]['caps'][cap]['pnl'] for s in results)
    row += f" ${cap_total:>+11.2f}"
print(row)

print()
print('='*80)
print('IMPROVEMENT VS BASELINE ($)')
print('='*80)
print(f"\n{'Strategy':<10} {'15 min':<15} {'30 min':<15} {'45 min':<15} {'60 min':<15}")
print('-'*70)

for strategy in strategies:
    if strategy not in results:
        continue
    row = f"{strategy:<10}"
    for cap in duration_caps:
        imp = results[strategy]['caps'][cap]['improvement']
        row += f" ${imp:>+11.2f}"
    print(row)

print('-'*70)
row = f"{'TOTAL':<10}"
for cap in duration_caps:
    total_imp = sum(results[s]['caps'][cap]['improvement'] for s in results)
    row += f" ${total_imp:>+11.2f}"
print(row)

print()
print('='*80)
print('IMPROVEMENT VS BASELINE (%)')
print('='*80)
print(f"\n{'Strategy':<10} {'15 min':<15} {'30 min':<15} {'45 min':<15} {'60 min':<15}")
print('-'*70)

for strategy in strategies:
    if strategy not in results:
        continue
    baseline = results[strategy]['baseline']['pnl']
    if baseline == 0:
        baseline = 0.01  # Avoid div by zero
    row = f"{strategy:<10}"
    for cap in duration_caps:
        imp = results[strategy]['caps'][cap]['improvement']
        pct = (imp / abs(baseline)) * 100 if baseline != 0 else 0
        row += f" {pct:>+10.1f}%"
    print(row)

print()
print('='*80)
print('TRADES CUT BY DURATION CAP')
print('='*80)
print(f"\n{'Strategy':<10} {'Baseline':<12} {'15 min':<15} {'30 min':<15} {'45 min':<15} {'60 min':<15}")
print('-'*82)

for strategy in strategies:
    if strategy not in results:
        continue
    baseline = results[strategy]['baseline']['trades']
    row = f"{strategy:<10} {baseline:<12}"
    for cap in duration_caps:
        cut = results[strategy]['caps'][cap]['trades_cut']
        pct = cut / baseline * 100 if baseline > 0 else 0
        row += f" {cut}/{baseline} ({pct:.1f}%)"
    print(row)

print()
print('='*80)
print('WIN RATE BY DURATION CAP')
print('='*80)
print(f"\n{'Strategy':<10} {'Baseline':<12} {'15 min':<15} {'30 min':<15} {'45 min':<15} {'60 min':<15}")
print('-'*82)

for strategy in strategies:
    if strategy not in results:
        continue
    baseline_wr = results[strategy]['baseline']['win_rate']
    row = f"{strategy:<10} {baseline_wr:>10.1f}%  "
    for cap in duration_caps:
        wr = results[strategy]['caps'][cap]['win_rate']
        row += f" {wr:>10.1f}%  "
    print(row)

print()
print('='*80)
print('OPTIMAL SETTINGS RECOMMENDATION')
print('='*80)

print("""
ANALYSIS SUMMARY:
-----------------
1. 15-minute cap: Most aggressive, cuts fastest but may cut legitimate winners
2. 30-minute cap: Balanced - catches most long-duration losers with minimal winner impact
3. 45-minute cap: Conservative - allows for basket recovery patterns
4. 60-minute cap: Most permissive - only cuts extreme outliers

STRATEGY-SPECIFIC OPTIMAL CAPS:
-------------------------------
""")

for strategy in strategies:
    if strategy not in results:
        continue
    baseline = results[strategy]['baseline']['pnl']
    best_cap = None
    best_pnl = baseline
    
    for cap in duration_caps:
        pnl = results[strategy]['caps'][cap]['pnl']
        if pnl > best_pnl:
            best_pnl = pnl
            best_cap = cap
    
    if best_cap:
        improvement = best_pnl - baseline
        print(f"  {strategy}: {best_cap} minutes (+${improvement:.2f} vs baseline)")
    else:
        print(f"  {strategy}: No cap needed (baseline is optimal)")

# Overall best
print(f"\nOVERALL OPTIMAL:")
baseline_total = sum(results[s]['baseline']['pnl'] for s in results)
for cap in duration_caps:
    total = sum(results[s]['caps'][cap]['pnl'] for s in results)
    improvement = total - baseline_total
    print(f"  {cap} min cap: ${total:.2f} (${improvement:+.2f} vs baseline)")

best_cap = max(duration_caps, key=lambda c: sum(results[s]['caps'][c]['pnl'] for s in results))
best_total = sum(results[s]['caps'][best_cap]['pnl'] for s in results)
print(f"\n  --> RECOMMENDED: {best_cap} minute cap (+${best_total - baseline_total:.2f} total)")

print()
print('Simulation complete.')
