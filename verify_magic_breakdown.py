"""Verify Analysis_20260323_v2.xlsx with magic number breakdown"""
import pandas as pd

file_path = 'data/Analysis_20260323_v2.xlsx'
xl = pd.ExcelFile(file_path)

print("=" * 100)
print("Analysis_20260323_v2.xlsx - Magic Number Breakdown Verification")
print("=" * 100)

print("\nSheet names:")
for sheet in xl.sheet_names[:10]:
    print(f"  - {sheet}")
print(f"  ... ({len(xl.sheet_names)} total sheets)")

print("\n" + "=" * 100)
print("RESULT Sheet (with Magic Number columns):")
print("=" * 100)
result_df = pd.read_excel(file_path, sheet_name='RESULT')
print(result_df.to_string())

print("\n" + "=" * 100)
print("Sample 10min Sheet (first 5 rows):")
print("=" * 100)
sample_df = pd.read_excel(file_path, sheet_name='10min')
print(sample_df.head().to_string())
print(f"\nColumns: {list(sample_df.columns)}")

print("\n" + "=" * 100)
print("Magic Number Summary (from RESULT tab):")
print("=" * 100)
magic_cols = [c for c in result_df.columns if c.startswith('Magic')]
print(f"Magic columns found: {magic_cols}")
print("\nTotal OutcomePoints by Magic Number (all time windows combined):")
for col in magic_cols:
    total = result_df[col].sum()
    print(f"  {col}: {total:,} points")
