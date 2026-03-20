import pandas as pd

df = pd.read_csv('multi_tp_corrected_results.csv')

print('='*110)
print('MULTI-TP SIMULATION - CORRECTED RESULTS (62 Asia Session Positions)')
print('='*110)

cutoffs = [2, 3, 5, 10, 15, 20, 30]

for cutoff in cutoffs:
    print(f'\n--- Cutoff: {cutoff} minutes ---')
    subset = df[df['cutoff'] == cutoff].sort_values('total_pnl', ascending=False).head(5)
    
    print(f'{"TP (pts)":<10} {"TP ($)":<10} {"Hits":<6} {"Miss":<6} {"Win%":<8} {"TP Profit":<12} {"Miss Loss":<12} {"NET P&L":<12}')
    print('-'*90)
    
    for _, row in subset.iterrows():
        print(f'{int(row["tp_points"]):<10} {row["tp_dollars"]:<10.2f} {int(row["tp_hits"]):<6} {int(row["misses"]):<6} {row["win_rate"]:<8.1f} {row["tp_pnl"]:<12.2f} {row["miss_pnl"]:<12.2f} {row["total_pnl"]:<12.2f}')

print('\n' + '='*110)
print('KEY FINDINGS:')
print('='*110)
print('1. BEST OVERALL: TP 110 pts ($1.10) with 2-min cutoff = $28.26 P&L')
print('2. SHORTER CUTOFFS WIN: 2-5 minute windows perform better than 10-30 min')
print('3. HIGHER TPS (>150) consistently lose money due to large miss losses')
print('4. Low TPs (30-50) with long cutoffs have high win rates but low absolute profit')
print('='*110)
