"""
Recovery Performance Recap - March 23, 24, 25
"""
import pandas as pd

print('='*100)
print('RECOVERY PERFORMANCE RECAP - MARCH 23-25, 2026')
print('='*100)
print()
print('Current Settings:')
print('  - ATR Multiplier: 2.0x')
print('  - Recovery Window: 120 minutes')
print('  - Opposing Threshold: 10 positions')
print('  - Layer 1: Immediate entry at SL hit')
print('  - Layer 2+: Entry after GU confirmation with ATR-based spacing')
print('  - All layers close together as RecoveryBasket')
print()

dates = ['20260323', '20260324', '20260325']
total_baskets = 0
total_positions = 0
total_recovered = 0
total_potential = 0
all_layers_data = []

for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis_FINAL.xlsx')
    
    print('='*100)
    print(f'{date} SUMMARY')
    print('='*100)
    
    # Basic stats
    baskets = len(df)
    positions = df['NumPos'].sum()
    recovered = len(df[df['Recovered'] == 'YES'])
    recovery_rate = recovered / baskets * 100 if baskets > 0 else 0
    
    print(f'\nBaskets: {baskets}')
    print(f'Total Positions: {positions}')
    print(f'Recovered: {recovered} ({recovery_rate:.1f}%)')
    print(f'Not Recovered: {baskets - recovered} ({100-recovery_rate:.1f}%)')
    
    # Layer distribution
    print('\nLayer Distribution:')
    layer_dist = df['NumLayers'].value_counts().sort_index()
    for layers, count in layer_dist.items():
        pct = count / baskets * 100
        print(f'  {int(layers)} layer(s): {count} ({pct:.1f}%)')
    
    print(f'\nMax Layers: {df["NumLayers"].max()}')
    print(f'Avg Layers: {df["NumLayers"].mean():.2f}')
    
    # ATR stats
    print(f'\nATR Range: {df["ATRPoints"].min():.0f} - {df["ATRPoints"].max():.0f}')
    print(f'Avg ATR: {df["ATRPoints"].mean():.0f} points')
    
    # Opposing count
    print(f'\nOpposing Count Range: {df["OpposingCount"].min()} - {df["OpposingCount"].max()}')
    print(f'Avg Opposing: {df["OpposingCount"].mean():.1f}')
    
    # Recovery time
    recovered_df = df[df['Recovered'] == 'YES']
    if len(recovered_df) > 0:
        print(f'\nRecovery Time (recovered only):')
        print(f'  Mean: {recovered_df["RecoveryDurationMin"].mean():.1f} min')
        print(f'  Median: {recovered_df["RecoveryDurationMin"].median():.1f} min')
        print(f'  Max: {recovered_df["RecoveryDurationMin"].max():.1f} min')
    
    # MAE Analysis
    print('\nMAE Analysis:')
    max_mae = 0
    total_mae_exposure = 0
    mae_count = 0
    
    for idx, row in df.iterrows():
        basket_mae = 0
        for i in range(1, int(row['NumLayers']) + 1):
            mae = row[f'Layer{i}MAE']
            if pd.notna(mae):
                basket_mae = max(basket_mae, mae)  # Max MAE across layers
                max_mae = max(max_mae, mae)
                total_mae_exposure += mae
                mae_count += 1
    
    if mae_count > 0:
        print(f'  Max MAE: {max_mae:.0f} points')
        print(f'  Avg MAE per layer: {total_mae_exposure/mae_count:.0f} points')
    
    # Profit Potential
    print('\nProfit Potential:')
    recovered_potential = 0
    lost_potential = 0
    
    for idx, row in df.iterrows():
        basket_potential = 0
        for i in range(1, int(row['NumLayers']) + 1):
            pot = row[f'Layer{i}Potential']
            if pd.notna(pot):
                basket_potential += pot
        
        if row['Recovered'] == 'YES':
            recovered_potential += basket_potential
        else:
            lost_potential += basket_potential
        
        total_potential += basket_potential
    
    print(f'  Recovered baskets: {recovered_potential:,.0f} points')
    print(f'  Lost baskets: {lost_potential:,.0f} points')
    print(f'  Total potential: {recovered_potential + lost_potential:,.0f} points')
    
    # Accumulate totals
    total_baskets += baskets
    total_positions += positions
    total_recovered += recovered

# Combined summary
print('\n' + '='*100)
print('COMBINED SUMMARY - MARCH 23-25')
print('='*100)
print(f'\nTotal Baskets: {total_baskets}')
print(f'Total Positions: {total_positions}')
print(f'Recovered: {total_recovered} ({total_recovered/total_baskets*100:.1f}%)')
print(f'Not Recovered: {total_baskets - total_recovered} ({(total_baskets-total_recovered)/total_baskets*100:.1f}%)')
print(f'\nTotal Profit Potential: {total_potential:,.0f} points')

# Performance by layer count
print('\n' + '='*100)
print('PERFORMANCE BY LAYER COUNT (Combined)')
print('='*100)

all_data = []
for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis_FINAL.xlsx')
    all_data.append(df)

df_all = pd.concat(all_data, ignore_index=True)

for layer_count in sorted(df_all['NumLayers'].unique()):
    subset = df_all[df_all['NumLayers'] == layer_count]
    rec_count = len(subset[subset['Recovered'] == 'YES'])
    total_count = len(subset)
    rec_rate = rec_count / total_count * 100 if total_count > 0 else 0
    
    # Average MAE
    maes = []
    for idx, row in subset.iterrows():
        for i in range(1, int(row['NumLayers']) + 1):
            mae = row[f'Layer{i}MAE']
            if pd.notna(mae):
                maes.append(mae)
    
    avg_mae = sum(maes)/len(maes) if maes else 0
    max_mae = max(maes) if maes else 0
    
    print(f'{int(layer_count)} layer(s): {rec_count}/{total_count} ({rec_rate:.1f}%) - Avg MAE: {avg_mae:.0f}, Max MAE: {max_mae:.0f}')

print('\n' + '='*100)
