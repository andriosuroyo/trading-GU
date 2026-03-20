"""Detailed TP breakdown for 5, 10, 15, 20 minute cutoffs"""

import pandas as pd

df = pd.read_csv('multi_tp_corrected_results.csv')

cutoffs = [5, 10, 15, 20]

for cutoff in cutoffs:
    print()
    print('='*100)
    print(f'CUTOFF: {cutoff} MINUTES - FULL TP BREAKDOWN')
    print('='*100)
    
    subset = df[df['cutoff'] == cutoff].sort_values('tp_points')
    
    print(f'{"TP (pts)":<10} {"TP ($)":<10} {"Hits":<6} {"Miss":<6} {"Win%":<8} {"TP Profit":<12} {"Miss Loss":<14} {"NET P&L":<12} {"Avg Miss":<10}')
    print('-'*100)
    
    for _, row in subset.iterrows():
        print(f'{int(row["tp_points"]):<10} {row["tp_dollars"]:<10.2f} {int(row["tp_hits"]):<6} {int(row["misses"]):<6} {row["win_rate"]:<8.1f} {row["tp_pnl"]:<12.2f} {row["miss_pnl"]:<14.2f} {row["total_pnl"]:<12.2f} {row["avg_miss_pnl"]:<10.2f}')
    
    # Summary stats for this cutoff
    best = subset.loc[subset['total_pnl'].idxmax()]
    worst = subset.loc[subset['total_pnl'].idxmin()]
    
    print()
    print(f'Best:  TP {int(best["tp_points"])}pts = ${best["total_pnl"]:.2f}')
    print(f'Worst: TP {int(worst["tp_points"])}pts = ${worst["total_pnl"]:.2f}')
    print()

print('='*100)
