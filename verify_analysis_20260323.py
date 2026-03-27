"""Verify Analysis_20260323.xlsx structure"""
import pandas as pd

file_path = 'data/Analysis_20260323.xlsx'
xl = pd.ExcelFile(file_path)

print("=" * 80)
print("Analysis_20260323.xlsx Structure Verification")
print("=" * 80)

print("\nSheet names ({} total):".format(len(xl.sheet_names)))
for i, sheet in enumerate(xl.sheet_names):
    print(f"  {i+1}. {sheet}")

print("\n" + "=" * 80)
print("RESULT Sheet:")
print("=" * 80)
result_df = pd.read_excel(file_path, sheet_name='RESULT')
print(result_df.to_string())
print(f"\nColumns: {list(result_df.columns)}")

print("\n" + "=" * 80)
print("Sample 5min Sheet (first 5 rows):")
print("=" * 80)
sample_df = pd.read_excel(file_path, sheet_name='5min')
print(sample_df.head().to_string())
print(f"\nColumns ({len(sample_df.columns)} total):")
for i, col in enumerate(sample_df.columns):
    print(f"  {i+1}. {col}")
print(f"\nTotal rows: {len(sample_df)}")

print("\n" + "=" * 80)
print("Sample 30min Sheet (first 3 rows):")
print("=" * 80)
sample_30 = pd.read_excel(file_path, sheet_name='30min')
print(sample_30.head(3).to_string())
