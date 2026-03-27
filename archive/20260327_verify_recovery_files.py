"""Verify RecoveryAnalysis files"""
import pandas as pd

print('='*100)
print('RECOVERYANALYSIS FILES SUMMARY - ALL DATES')
print('='*100)

dates = ['2026-03-20', '2026-03-23', '2026-03-24', '2026-03-25']

for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis.xlsx')
    print(f'\n{date}:')
    print(f'  Total losses: {len(df)}')
    
    recovered = df[df['Recovered'] == 'YES']
    print(f'  Recovered: {len(recovered)} ({len(recovered)/len(df)*100:.1f}%)')
    
    layer_dist = df['NumLayers'].value_counts().sort_index()
    print(f'  Max layers: {df["NumLayers"].max()}')
    print(f'  Avg layers: {df["NumLayers"].mean():.2f}')
    print(f'  Layer distribution: {dict((int(k), int(v)) for k, v in layer_dist.items())}')
    
    # Show a sample with layers (up to 5 layers max display)
    with_layers = df[df['NumLayers'] > 0]
    if len(with_layers) > 0:
        sample = with_layers.iloc[0]
        num_layers = min(int(sample['NumLayers']), 5)  # Show max 5
        print(f'  Sample (Ticket {sample["Ticket"]}, {int(sample["NumLayers"])} layers):')
        for i in range(1, num_layers + 1):
            open_p = sample[f'Layer{i}Open']
            dist = sample[f'Layer{i}Dist']
            mae = sample[f'Layer{i}MAE']
            print(f'    L{i}: Open={open_p:.2f}, Dist={dist:.0f}, MAE={mae:.0f}')

print('\n' + '='*100)
print('FILES CREATED:')
for date in dates:
    print(f'  data/{date}_RecoveryAnalysis.xlsx')
print('='*100)

# Combined stats
print('\nCOMBINED STATISTICS:')
all_data = []
for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis.xlsx')
    all_data.append(df)

df_all = pd.concat(all_data, ignore_index=True)
print(f'Total losses: {len(df_all)}')

recovered_all = df_all[df_all['Recovered'] == 'YES']
print(f'Total recovered: {len(recovered_all)} ({len(recovered_all)/len(df_all)*100:.1f}%)')
print(f'Max layers: {df_all["NumLayers"].max()}')
print(f'Avg layers: {df_all["NumLayers"].mean():.2f}')

# Max MAE
with_layers = df_all[df_all['NumLayers'] > 0]
max_mae = 0
max_mae_row = None
for idx, row in with_layers.iterrows():
    for i in range(1, min(int(row['NumLayers']), 5) + 1):
        mae = row[f'Layer{i}MAE']
        if pd.notna(mae) and mae > max_mae:
            max_mae = mae
            max_mae_row = row

print(f'Max MAE observed: {max_mae:.0f} points')
if max_mae_row is not None:
    print(f'  (Ticket {max_mae_row["Ticket"]} on {max_mae_row["Date"]}, Layer with MAE)')

# MAE by layer count
print('\nMAE by layer count:')
for layer_count in sorted(df_all['NumLayers'].unique()):
    if layer_count == 0:
        continue
    subset = df_all[df_all['NumLayers'] == layer_count]
    maes = []
    for idx, row in subset.iterrows():
        for i in range(1, min(layer_count, 5) + 1):
            mae_col = f'Layer{i}MAE'
            if mae_col in row:
                mae = row[mae_col]
                if pd.notna(mae):
                    maes.append(mae)
    if maes:
        print(f'  {layer_count} layer(s): Mean={sum(maes)/len(maes):.0f}, Max={max(maes):.0f}')
