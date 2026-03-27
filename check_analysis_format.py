"""Check the structure of existing Analysis file"""
import pandas as pd

# Read the Excel file to see sheet names and structure
file_path = 'data/Analysis_20260320.xlsx'
xl = pd.ExcelFile(file_path)

print("Sheet names:")
for sheet in xl.sheet_names:
    print(f"  - {sheet}")

print("\n" + "="*80)
print("RESULT sheet:")
result_df = pd.read_excel(file_path, sheet_name='RESULT')
print(result_df.head(10).to_string())
print(f"\nColumns: {list(result_df.columns)}")

print("\n" + "="*80)
print("Sample 15min sheet:")
sample_df = pd.read_excel(file_path, sheet_name='15min')
print(sample_df.head(3).to_string())
print(f"\nColumns: {list(sample_df.columns)}")
print(f"\nTotal rows: {len(sample_df)}")
