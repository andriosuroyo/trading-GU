"""Verify ATR fix and Magic6 data in v3 file"""
import pandas as pd

file_path = 'data/Analysis_20260323_v3.xlsx'
xl = pd.ExcelFile(file_path)

print("=" * 100)
print("Verifying Analysis_20260323_v3.xlsx")
print("=" * 100)

# Check RESULT tab
result_df = pd.read_excel(xl, sheet_name='RESULT')
print("\nRESULT Tab (showing Magic columns):")
print(result_df[['TimeWindow', 'TotalOutcomePoints', 'Magic6']].to_string())

# Check sample 5min data for ATR values
print("\n" + "=" * 100)
print("Sample 5min Sheet - checking ATR values:")
df_5min = pd.read_excel(xl, sheet_name='5min')
print(df_5min[['Ticket', 'Magic Number', 'ATROpen', 'ATRTP']].head(10).to_string())

print("\nATR Value Distribution:")
print(df_5min['ATROpen'].describe())

# Check Magic6 positions
print("\n" + "=" * 100)
print("Magic6 Positions in 5min sheet:")
magic6 = df_5min[df_5min['Magic Number'] == 6]
print(magic6[['Ticket', 'Outcome', 'OutcomePoints', 'ATROpen', 'ATRTP', 'MFE5Points']].to_string())

# Check 15min for comparison
print("\n" + "=" * 100)
print("Magic6 in 15min sheet:")
df_15min = pd.read_excel(xl, sheet_name='15min')
magic6_15 = df_15min[df_15min['Magic Number'] == 6]
print(magic6_15[['Ticket', 'Outcome', 'OutcomePoints', 'MFE15Points']].to_string())
print(f"\nMagic6 15min total: {magic6_15['OutcomePoints'].sum()}")

# Verify ATR is not 0
print("\n" + "=" * 100)
print("ATR Validation:")
zero_atr = (df_5min['ATROpen'] == 0).sum()
print(f"Positions with ATR=0: {zero_atr}")
print(f"Positions with valid ATR: {(df_5min['ATROpen'] > 0).sum()}")
