"""Analyze RecoveryAnalysis files in depth"""
import pandas as pd

# Load all three files
dates = ['2026-03-20', '2026-03-23', '2026-03-24']
all_data = []

for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis.xlsx')
    all_data.append(df)
    print(f'{date}: {len(df)} losses')

df_all = pd.concat(all_data, ignore_index=True)

print('\n' + '='*100)
print('COMBINED ANALYSIS - ALL THREE DATES')
print('='*100)
print(f'Total losing positions: {len(df_all)}')

# Recovery rate
recovered = df_all[df_all['Recovered'] == 'YES']
not_recovered = df_all[df_all['Recovered'] == 'NO']
print(f'Recovered: {len(recovered)} ({len(recovered)/len(df_all)*100:.1f}%)')
print(f'Not recovered: {len(not_recovered)} ({len(not_recovered)/len(df_all)*100:.1f}%)')

# Recovery time analysis
print('\n' + '='*100)
print('RECOVERY TIME ANALYSIS (for recovered positions)')
print('='*100)
print(f'Mean: {recovered["RecoveryDurationMin"].mean():.1f} min')
print(f'Median: {recovered["RecoveryDurationMin"].median():.1f} min')
print(f'Min: {recovered["RecoveryDurationMin"].min():.1f} min')
print(f'Max: {recovered["RecoveryDurationMin"].max():.1f} min')
print(f'75th percentile: {recovered["RecoveryDurationMin"].quantile(0.75):.1f} min')
print(f'90th percentile: {recovered["RecoveryDurationMin"].quantile(0.90):.1f} min')
print(f'95th percentile: {recovered["RecoveryDurationMin"].quantile(0.95):.1f} min')

# Time buckets
print('\nRecovery Time Distribution:')
buckets = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 120), (120, 240)]
for min_mins, max_mins in buckets:
    count = len(recovered[(recovered['RecoveryDurationMin'] >= min_mins) & (recovered['RecoveryDurationMin'] < max_mins)])
    pct = count / len(recovered) * 100
    print(f'  {min_mins:3d}-{max_mins:3d} min: {count:3d} ({pct:.1f}%)')

# Opposing count analysis
print('\n' + '='*100)
print('OPPOSING COUNT ANALYSIS (at recovery time)')
print('='*100)
print(f'Mean: {recovered["OpposingCount"].mean():.1f}')
print(f'Median: {recovered["OpposingCount"].median():.1f}')
print(f'Max: {recovered["OpposingCount"].max()}')

print('\nDistribution:')
opp_dist = recovered['OpposingCount'].value_counts().sort_index()
for opp, count in opp_dist.head(15).items():
    pct = count / len(recovered) * 100
    print(f'  {opp:2d} opposing: {count:3d} ({pct:.1f}%)')

# Not recovered analysis
print('\n' + '='*100)
print('NOT RECOVERED ANALYSIS')
print('='*100)
print(f'Total not recovered: {len(not_recovered)}')
print(f'Avg opposing count: {not_recovered["OpposingCount"].mean():.1f}')
print('\nBy date:')
for date in dates:
    nr = not_recovered[not_recovered['Date'] == date]
    print(f'  {date}: {len(nr)} not recovered')

# Show the not recovered positions
print('\nNot Recovered Details:')
print(not_recovered[['Date', 'Ticket', 'Magic', 'Direction', 'OpenTime', 'OpposingCount', 'LossPoints']].to_string(index=False))

# Financial impact
print('\n' + '='*100)
print('FINANCIAL IMPACT')
print('='*100)
total_loss_points = df_all['LossPoints'].sum()
total_recovery_profit = recovered['RecoveryProfitPoints'].sum()
print(f'Total loss points: {total_loss_points:,.0f}')
print(f'Total potential recovery profit: {total_recovery_profit:,.0f} points')
print(f'Net if all recovered: {total_loss_points + total_recovery_profit:,.0f} points')
print(f'Recovery efficiency: {abs(total_recovery_profit/total_loss_points)*100:.1f}%')

# By magic
print('\n' + '='*100)
print('TOP 10 MAGIC NUMBERS - RECOVERY STATS')
print('='*100)
magic_stats = recovered.groupby('Magic').agg({
    'Ticket': 'count',
    'RecoveryDurationMin': 'mean',
    'OpposingCount': 'mean',
    'RecoveryProfitPoints': 'sum'
}).round(1)
magic_stats.columns = ['Recovered', 'AvgTime', 'AvgOpp', 'TotalProfit']
magic_stats = magic_stats.sort_values('Recovered', ascending=False)
print(magic_stats.head(10).to_string())

# X threshold analysis
print('\n' + '='*100)
print('X THRESHOLD ANALYSIS')
print('='*100)
print('Recovery rate by max opposing count allowed:')
for x in [0, 1, 2, 3, 5, 7, 10, 15, 20, 25]:
    eligible = recovered[recovered['OpposingCount'] <= x]
    total_eligible = len(df_all[df_all['OpposingCount'] <= x])
    if total_eligible > 0:
        rec_rate = len(eligible) / total_eligible * 100
        print(f'  X={x:2d}: {len(eligible):3d}/{total_eligible:3d} eligible recoveries ({rec_rate:.1f}%)')
