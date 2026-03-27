"""Verify RecoveryAnalysis v3 files"""
import pandas as pd

print('='*100)
print('RECOVERYANALYSIS V3 - VERIFICATION')
print('='*100)

dates = ['20260320', '20260323', '20260324', '20260325']

all_data = []

for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis_v3.xlsx')
    all_data.append(df)
    
    print(f'\n{date}:')
    print(f'  Baskets: {len(df)}')
    print(f'  Recovered: {len(df[df["Recovered"] == "YES"])}')
    print(f'  ATR range: {df["ATRPoints"].min():.0f} - {df["ATRPoints"].max():.0f} (Avg: {df["ATRPoints"].mean():.0f})')
    print(f'  NumPos range: {df["NumPos"].min()} - {df["NumPos"].max()}')
    print(f'  Max layers: {df["NumLayers"].max()}')
    
    # Show sample with multiple positions in basket
    multi_pos = df[df['NumPos'] > 1]
    if len(multi_pos) > 0:
        sample = multi_pos.iloc[0]
        print(f'  Multi-pos basket sample: Basket {sample["Basket"]} has {sample["NumPos"]} positions')
    
    # Show sample with layers
    with_layers = df[df['NumLayers'] > 1]
    if len(with_layers) > 0:
        sample = with_layers.iloc[0]
        print(f'  Layer sample (Ticket {sample["Ticket"]}, {sample["NumLayers"]} layers):')
        for i in range(1, min(int(sample['NumLayers']), 3) + 1):
            price = sample[f'Layer{i}Price']
            pot = sample[f'Layer{i}Potential']
            mae = sample[f'Layer{i}MAE']
            print(f'    L{i}: Price={price:.2f}, Potential={pot:.0f}, MAE={mae:.0f}')
    
    # Show recovered vs not recovered sample
    rec = df[df['Recovered'] == 'YES'].iloc[0] if len(df[df['Recovered'] == 'YES']) > 0 else None
    if rec is not None:
        print(f'  Recovered sample: FurthestPrice={rec["FurthestPrice"]:.2f}')

print('\n' + '='*100)
print('COMBINED STATISTICS')
print('='*100)

df_all = pd.concat(all_data, ignore_index=True)
print(f'Total baskets: {len(df_all)}')
print(f'Total positions: {df_all["NumPos"].sum()}')
print(f'Recovered: {len(df_all[df_all["Recovered"] == "YES"])} ({len(df_all[df_all["Recovered"] == "YES"])/len(df_all)*100:.1f}%)')
print(f'ATR: Min={df_all["ATRPoints"].min():.0f}, Max={df_all["ATRPoints"].max():.0f}, Avg={df_all["ATRPoints"].mean():.0f}')
print(f'Max layers: {df_all["NumLayers"].max()}')
print(f'Avg layers: {df_all["NumLayers"].mean():.2f}')

# Max MAE
max_mae = 0
for idx, row in df_all.iterrows():
    for i in range(1, int(row['NumLayers']) + 1):
        mae = row[f'Layer{i}MAE']
        if pd.notna(mae) and mae > max_mae:
            max_mae = mae
print(f'Max MAE: {max_mae:.0f} points')

print('\n' + '='*100)
print('FILES CREATED:')
for date in dates:
    print(f'  data/{date}_RecoveryAnalysis_v3.xlsx')
