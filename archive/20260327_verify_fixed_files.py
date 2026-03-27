"""Verify the fixed RecoveryAnalysis files"""
import pandas as pd

print('='*100)
print('VERIFICATION OF FIXED RECOVERYANALYSIS FILES')
print('='*100)

dates = ['20260320', '20260323', '20260324', '20260325']

all_data = []

for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis.xlsx')
    all_data.append(df)
    
    print(f'\n{date}:')
    print(f'  Total: {len(df)}')
    print(f'  Recovered: {len(df[df["Recovered"] == "YES"])}')
    print(f'  Columns: {len(df.columns)}')
    
    # Check Ticket format
    sample_ticket = df['Ticket'].iloc[0]
    print(f'  Sample Ticket: {sample_ticket}')
    
    # Check ATR range
    print(f'  ATR range: {df["ATRPoints"].min():.0f} - {df["ATRPoints"].max():.0f}')
    
    # Check OpposingCount range
    print(f'  OpposingCount range: {df["OpposingCount"].min()} - {df["OpposingCount"].max()}')
    
    # Show a sample row with layers
    with_layers = df[df['NumLayers'] > 0].iloc[0] if len(df[df['NumLayers'] > 0]) > 0 else None
    if with_layers is not None:
        print(f'  Sample (Ticket {with_layers["Ticket"]}, {with_layers["NumLayers"]} layers):')
        print(f'    Direction: {with_layers["Direction"]}')
        print(f'    OpenPrice: {with_layers["OpenPrice"]}')
        print(f'    LostPrice: {with_layers["LostPrice"]}')
        for i in range(1, min(int(with_layers['NumLayers']), 3) + 1):
            price = with_layers[f'Layer{i}Price']
            pot = with_layers[f'Layer{i}Potential']
            mae = with_layers[f'Layer{i}MAE']
            print(f'    L{i}: Price={price}, Potential={pot}, MAE={mae}')
    
    # Show a failed recovery sample
    failed = df[df['Recovered'] == 'NO'].iloc[0] if len(df[df['Recovered'] == 'NO']) > 0 else None
    if failed is not None:
        print(f'  Failed sample (Ticket {failed["Ticket"]}):')
        print(f'    LostPrice: {failed["LostPrice"]}')
        if failed['NumLayers'] > 0:
            for i in range(1, min(int(failed['NumLayers']), 2) + 1):
                price = failed[f'Layer{i}Price']
                pot = failed[f'Layer{i}Potential']
                mae = failed[f'Layer{i}MAE']
                print(f'    L{i}: Price={price}, Potential={pot}, MAE={mae}')

print('\n' + '='*100)
print('COMBINED STATISTICS')
print('='*100)

df_all = pd.concat(all_data, ignore_index=True)
print(f'Total losses: {len(df_all)}')
print(f'Total recovered: {len(df_all[df_all["Recovered"] == "YES"])} ({len(df_all[df_all["Recovered"] == "YES"])/len(df_all)*100:.1f}%)')
print(f'Max layers: {df_all["NumLayers"].max()}')
print(f'Avg ATR: {df_all["ATRPoints"].mean():.0f}')
print(f'Avg OpposingCount: {df_all["OpposingCount"].mean():.1f}')

print('\n' + '='*100)
print('FILES CREATED:')
for date in dates:
    print(f'  data/{date}_RecoveryAnalysis.xlsx')
