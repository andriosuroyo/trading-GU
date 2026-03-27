import pandas as pd

df = pd.read_excel('data/20260323_RecoveryAnalysis_v3_fixed.xlsx')

print('VERIFICATION OF FIXED FURTHESTPRICE')
print('='*80)

# Check first few SELL positions
sell_positions = df[df['Direction'] == 'SELL'].head(5)

print('\nFirst 5 SELL positions:')
for idx, row in sell_positions.iterrows():
    print(f"Row {idx}:")
    print(f"  Direction: {row['Direction']}")
    print(f"  ClosePrice (Layer1 entry): {row['ClosePrice']:.2f}")
    print(f"  FurthestPrice: {row['FurthestPrice']:.2f}")
    
    if row['FurthestPrice'] > row['ClosePrice']:
        print(f"  OK: FurthestPrice is HIGHER than ClosePrice")
    else:
        print(f"  ERROR: FurthestPrice should be higher for SELL")
    
    # Show Layer 1 MAE
    mae = row['Layer1MAE']
    print(f"  Layer1MAE: {mae:.0f} points")
    print()

# Check BUY positions too
print('First 3 BUY positions:')
buy_positions = df[df['Direction'] == 'BUY'].head(3)
for idx, row in buy_positions.iterrows():
    print(f"Row {idx}:")
    print(f"  ClosePrice: {row['ClosePrice']:.2f}")
    print(f"  FurthestPrice: {row['FurthestPrice']:.2f}")
    
    if row['FurthestPrice'] < row['ClosePrice']:
        print(f"  OK: FurthestPrice is LOWER than ClosePrice")
    else:
        print(f"  ERROR: FurthestPrice should be lower for BUY")
    print()
