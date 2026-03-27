import pandas as pd

# Show the specific row the user mentioned (row 2)
df = pd.read_excel('data/20260323_RecoveryAnalysis_v3_fixed.xlsx')

print('Row 2 (the one user mentioned):')
row = df.iloc[2]
print(f"  Ticket: {row['Ticket']}")
print(f"  Direction: {row['Direction']}")
print(f"  OpenPrice (Target): {row['OpenPrice']:.2f}")
print(f"  ClosePrice (SL hit): {row['ClosePrice']:.2f}")
print(f"  FurthestPrice (worst): {row['FurthestPrice']:.2f}")
print(f"  NumLayers: {row['NumLayers']}")
print()
print("  Layers:")
for i in range(1, int(row['NumLayers']) + 1):
    price = row[f'Layer{i}Price']
    pot = row[f'Layer{i}Potential']
    mae = row[f'Layer{i}MAE']
    print(f"    L{i}: Price={price:.2f}, Potential={pot:.0f}, MAE={mae:.0f}")
