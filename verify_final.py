import pandas as pd

df = pd.read_excel('data/20260323_RecoveryAnalysis_FINAL.xlsx')

print('Row 2 - the one user mentioned:')
print('='*60)
row = df.iloc[2]
print(f"Ticket: {row['Ticket']}")
print(f"Direction: {row['Direction']}")
print(f"OpenPrice (Target): {row['OpenPrice']:.2f}")
print(f"ClosePrice (SL hit): {row['ClosePrice']:.2f}")
print(f"FurthestPrice (worst): {row['FurthestPrice']:.2f}")
print(f"NumLayers: {row['NumLayers']}")
print()
print("Layers:")
for i in range(1, int(row['NumLayers']) + 1):
    price = row[f'Layer{i}Price']
    pot = row[f'Layer{i}Potential']
    mae = row[f'Layer{i}MAE']
    print(f"  L{i}: Price={price:.2f}, Potential={pot:.0f}, MAE={mae:.0f}")
print()
print("Verification:")
if row['Direction'] == 'SELL':
    if row['FurthestPrice'] > row['ClosePrice']:
        print("OK - FurthestPrice is HIGHER than ClosePrice for SELL")
        print(f"MAE calculation: {row['FurthestPrice']:.2f} - {row['ClosePrice']:.2f} = {row['FurthestPrice'] - row['ClosePrice']:.2f} = {(row['FurthestPrice'] - row['ClosePrice'])*100:.0f} points")
    else:
        print("ERROR")
