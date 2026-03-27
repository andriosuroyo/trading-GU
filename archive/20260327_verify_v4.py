"""Verify Analysis_20260323_v4.xlsx with #code column"""
import pandas as pd

file_path = 'data/Analysis_20260323_v4.xlsx'
xl = pd.ExcelFile(file_path)

print("=" * 100)
print("Verifying Analysis_20260323_v4.xlsx with #code columns")
print("=" * 100)

# Check sample 5min sheet
print("\n5min Sheet - First 5 rows with #Code column:")
df_5min = pd.read_excel(xl, sheet_name='5min')
print(df_5min[['#Code', 'Ticket', 'Magic Number', 'Type', 'Outcome', 'OutcomePoints']].head().to_string())

print("\n" + "=" * 100)
print("Columns in 5min sheet:")
print("=" * 100)
for i, col in enumerate(df_5min.columns, 1):
    print(f"  {i}. {col}")

print("\n" + "=" * 100)
print("Sample codes for different magic numbers:")
print("=" * 100)
for magic in [1, 2, 7, 8, 12]:
    sample = df_5min[df_5min['Magic Number'] == magic].iloc[0]
    print(f"  Magic {magic}: {sample['#Code']}")
