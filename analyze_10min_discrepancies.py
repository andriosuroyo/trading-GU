"""
Analyze March 23rd 10min data for discrepancies between ActualPoints and OutcomePoints
Factors to consider:
1. Magic 7 uses PT=0.3x, Magic 8 uses PT=0.7x (not 0.5x)
2. Spread may prevent MFE from being realized
3. Compare MFE10Points vs ATRTP to see if spread gap exists
"""
import pandas as pd
import sys
sys.path.append('C:/Trading_GU')
from magic_code_config import MAGIC_CODES

file_path = 'data/Analysis_20260323_v4.xlsx'
df = pd.read_excel(file_path, sheet_name='10min')

print("=" * 100)
print("MARCH 23RD - 10MIN ANALYSIS: ActualPoints vs OutcomePoints Discrepancies")
print("=" * 100)

# Add PT multiplier info
pt_multipliers = {
    1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0.5, 6: 0.5,
    7: 0.3, 8: 0.7, 9: 0.3, 10: 0.5, 11: 0.5, 12: 0.5
}

df['PT_Mult'] = df['Magic Number'].map(pt_multipliers)
df['Expected_ATRTP'] = (df['ATROpen'] * df['PT_Mult'] * 100).round().astype(int)

print("\n1. PT MULTIPLIER CORRECTION CHECK")
print("-" * 100)
print(f"{'Magic':<6} {'Code':<12} {'PT_Mult':<8} {'ATROpen':<8} {'ATRTP_in_sheet':<12} {'Expected_ATRTP':<12} {'Match?'}")
print("-" * 100)

for magic in [2, 7, 8, 12]:
    sample = df[df['Magic Number'] == magic].iloc[0]
    match = "YES" if sample['ATRTP'] == sample['Expected_ATRTP'] else "NO"
    print(f"{magic:<6} {sample['#Code']:<12} {sample['PT_Mult']:<8} {sample['ATROpen']:<8.2f} {sample['ATRTP']:<12} {sample['Expected_ATRTP']:<12} {match}")

print("\n2. LARGE DISCREPANCIES: ActualPoints vs OutcomePoints")
print("-" * 100)
df['Diff'] = df['ActualPoints'] - df['OutcomePoints']
df['AbsDiff'] = df['Diff'].abs()

# Find largest discrepancies
large_diff = df[df['AbsDiff'] > 500].sort_values('AbsDiff', ascending=False)
print(f"\nPositions with >500 points difference (showing top 20):")
print(large_diff[['Ticket', '#Code', 'Magic Number', 'Type', 'ActualPoints', 'OutcomePoints', 'Diff', 'MFE10Points', 'ATRTP', 'Outcome']].head(20).to_string())

print("\n3. SPREAD ANALYSIS: Why MFE doesn't translate to PROFIT")
print("-" * 100)

# For positions where MFE >= ATRTP but Outcome is LOSS
# This indicates spread prevented TP from being hit
print("\nPositions where MFE10Points >= ATRTP but Outcome = LOSS (spread gap):")
spread_issues = df[(df['MFE10Points'] >= df['ATRTP']) & (df['Outcome'] == 'LOSS')]
print(f"Found {len(spread_issues)} positions")
if len(spread_issues) > 0:
    print(spread_issues[['Ticket', '#Code', 'Magic Number', 'MFE10Points', 'ATRTP', 'MAE10Points', 'OutcomePoints']].head(10).to_string())

# Calculate spread gap
print("\n4. SPREAD GAP CALCULATION")
print("-" * 100)
if len(spread_issues) > 0:
    spread_issues['SpreadGap'] = spread_issues['MFE10Points'] - spread_issues['ATRTP']
    print(f"Average spread gap: {spread_issues['SpreadGap'].mean():.1f} points")
    print(f"Min spread gap: {spread_issues['SpreadGap'].min():.1f} points")
    print(f"Max spread gap: {spread_issues['SpreadGap'].max():.1f} points")

print("\n5. MAGIC 7 & 8 SPECIFIC ANALYSIS (PT=0.3x and 0.7x)")
print("-" * 100)

for magic, pt in [(7, 0.3), (8, 0.7)]:
    magic_df = df[df['Magic Number'] == magic]
    print(f"\nMagic {magic} (PT={pt}x) - {len(magic_df)} positions:")
    print(f"  ATRTP range: {magic_df['ATRTP'].min()} - {magic_df['ATRTP'].max()}")
    print(f"  OutcomePoints sum: {magic_df['OutcomePoints'].sum():,}")
    print(f"  ActualPoints sum: {magic_df['ActualPoints'].sum():,}")
    
    # Check how many hit TP
    hit_tp = (magic_df['MFE10Points'] >= magic_df['ATRTP']).sum()
    print(f"  Positions where MFE >= ATRTP: {hit_tp}/{len(magic_df)}")
    
    # Show sample
    print(f"  Sample position:")
    sample = magic_df.iloc[0]
    print(f"    ATR={sample['ATROpen']:.2f}, ATRTP={sample['ATRTP']}, MFE={sample['MFE10Points']}, Outcome={sample['Outcome']}, Points={sample['OutcomePoints']}")

print("\n6. SUMMARY BY MAGIC NUMBER (10min)")
print("-" * 100)
summary = df.groupby('Magic Number').agg({
    'OutcomePoints': 'sum',
    'ActualPoints': 'sum',
    'Ticket': 'count'
}).rename(columns={'Ticket': 'Count'})
summary['Diff'] = summary['ActualPoints'] - summary['OutcomePoints']
summary['Code'] = summary.index.map(lambda x: MAGIC_CODES.get(x, {}).get('code', 'UNKNOWN'))
print(summary[['Code', 'Count', 'OutcomePoints', 'ActualPoints', 'Diff']].to_string())
