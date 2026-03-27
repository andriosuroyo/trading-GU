"""
Analyze which magic numbers caused:
1. March 24 Asia loss
2. March 23 London-NY loss
"""
import pandas as pd

print("=" * 100)
print("LOSS BREAKDOWN BY MAGIC NUMBER")
print("=" * 100)

# Magic code mapping
magic_codes = {
    1: 'm1082805 (DISCONTINUED)',
    2: 'm1104005 (ACTIVE)',
    3: 'm1208005 (ACTIVE)',
    4: 'm1501H05 (ACTIVE)',
    5: 'm1502H05 (ACTIVE)',
    6: 'm1H2H05 (ACTIVE)',
    7: 'm1104003 (DEACTIVATED)',
    8: 'm1104007 (DEACTIVATED)',
    9: 'm5082803 (DEACTIVATED)',
    10: 'm5082805 (DEACTIVATED)',
    11: 'm2082805 (DEACTIVATED)',
    12: 'm2104005 (ACTIVE)',
}

# 1. March 24 Asia Loss Breakdown
print("\n1. MARCH 24TH ASIA SESSION LOSS BREAKDOWN (01:00-08:00)")
print("-" * 100)

try:
    df = pd.read_excel('data/Analysis_20260324_v4.xlsx', sheet_name='15min')
    df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
    
    asia = df[(df['Hour'] >= 1) & (df['Hour'] < 8)]
    
    print(f"Total Asia trades: {len(asia)}, Total loss: {asia['OutcomePoints'].sum():,.0f} pts\n")
    
    # By magic number
    print("By Magic Number:")
    magic_summary = asia.groupby('Magic Number').agg({
        'Ticket': 'count',
        'OutcomePoints': 'sum',
        'MAE15Points': 'mean'
    }).rename(columns={'Ticket': 'Count'}).sort_values('OutcomePoints')
    
    for magic, row in magic_summary.iterrows():
        code = magic_codes.get(magic, 'UNKNOWN')
        status = "DEACT" if "DEACTIVATED" in code else "ACTIVE"
        print(f"  Magic {magic:2d} ({status:6s}): {row['Count']:3d} trades, {row['OutcomePoints']:+8,.0f} pts, MAE: {row['MAE15Points']:.0f}")
    
    # Worst trades
    print("\nTop 10 Worst Trades:")
    worst = asia.nsmallest(10, 'OutcomePoints')
    for _, row in worst.iterrows():
        magic = int(row['Magic Number'])
        code = magic_codes.get(magic, 'UNKNOWN')
        status = "DEACT" if "DEACTIVATED" in code else "ACTIVE"
        print(f"  {row['Ticket']} | {row['TimeOpen']} | Magic {magic} ({status}) | {row['OutcomePoints']:+6,.0f} pts | {code}")
    
    # Check if losses were from deactivated sets
    deactivated_magics = [1, 7, 8, 9, 10, 11]
    active_magics = [2, 3, 4, 5, 6, 12]
    
    deact_loss = asia[asia['Magic Number'].isin(deactivated_magics)]['OutcomePoints'].sum()
    active_loss = asia[asia['Magic Number'].isin(active_magics)]['OutcomePoints'].sum()
    
    print(f"\nLoss Attribution:")
    print(f"  Deactivated sets (1,7,8,9,10,11): {deact_loss:+8,.0f} pts")
    print(f"  Active sets (2,3,4,5,6,12):       {active_loss:+8,.0f} pts")
    
except Exception as e:
    print(f"Error: {e}")

# 2. March 23 London-NY Loss Breakdown
print("\n\n2. MARCH 23RD LONDON-NY SESSION LOSS BREAKDOWN (08:00-23:00)")
print("-" * 100)

try:
    if '20260323' == '20260320':
        file_path = 'data/Analysis_20260323.xlsx'
    else:
        file_path = 'data/Analysis_20260323_v4.xlsx'
    
    df = pd.read_excel(file_path, sheet_name='15min')
    df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
    
    london_ny = df[(df['Hour'] >= 8) & (df['Hour'] < 23)]
    
    print(f"Total London-NY trades: {len(london_ny)}, Total: {london_ny['OutcomePoints'].sum():,.0f} pts\n")
    
    # By magic number
    print("By Magic Number:")
    magic_summary = london_ny.groupby('Magic Number').agg({
        'Ticket': 'count',
        'OutcomePoints': 'sum',
        'MAE15Points': 'mean'
    }).rename(columns={'Ticket': 'Count'}).sort_values('OutcomePoints')
    
    for magic, row in magic_summary.iterrows():
        code = magic_codes.get(magic, 'UNKNOWN')
        status = "DEACT" if "DEACTIVATED" in code else "ACTIVE"
        print(f"  Magic {magic:2d} ({status:6s}): {row['Count']:3d} trades, {row['OutcomePoints']:+8,.0f} pts, MAE: {row['MAE15Points']:.0f}")
    
    # Worst trades
    print("\nTop 10 Worst Trades:")
    worst = london_ny.nsmallest(10, 'OutcomePoints')
    for _, row in worst.iterrows():
        magic = int(row['Magic Number'])
        code = magic_codes.get(magic, 'UNKNOWN')
        status = "DEACT" if "DEACTIVATED" in code else "ACTIVE"
        print(f"  {row['Ticket']} | {row['TimeOpen']} | Magic {magic} ({status}) | {row['OutcomePoints']:+6,.0f} pts | {code}")
    
    # Attribution
    deact_loss = london_ny[london_ny['Magic Number'].isin(deactivated_magics)]['OutcomePoints'].sum()
    active_loss = london_ny[london_ny['Magic Number'].isin(active_magics)]['OutcomePoints'].sum()
    
    print(f"\nLoss Attribution:")
    print(f"  Deactivated sets (1,7,8,9,10,11): {deact_loss:+8,.0f} pts")
    print(f"  Active sets (2,3,4,5,6,12):       {active_loss:+8,.0f} pts")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 100)
