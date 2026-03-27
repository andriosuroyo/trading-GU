"""Quick verification of March 24th analysis"""
import pandas as pd

file_path = 'data/Analysis_20260324_v4.xlsx'
xl = pd.ExcelFile(file_path)

print("=" * 100)
print("MARCH 24TH ANALYSIS - QUICK SUMMARY")
print("=" * 100)

# RESULT tab
result_df = pd.read_excel(xl, sheet_name='RESULT')
print("\nRESULT Tab (top 10 time windows):")
print(result_df[['TimeWindow', 'ProfitCount', 'LossCount', 'WinRate', 'TotalOutcomePoints']].head(10).to_string())

# Best time window
best = result_df.loc[result_df['TotalOutcomePoints'].idxmax()]
print(f"\n[OK] Best Time Window: {best['TimeWindow']} with {best['TotalOutcomePoints']:,} points ({best['WinRate']:.1f}% WR)")

# Magic number breakdown
print("\n" + "=" * 100)
print("MAGIC NUMBER PERFORMANCE (Total OutcomePoints across all time windows):")
print("=" * 100)
magic_cols = [c for c in result_df.columns if c.startswith('Magic')]
magic_sums = {col: result_df[col].sum() for col in magic_cols}
sorted_magics = sorted(magic_sums.items(), key=lambda x: x[1], reverse=True)
for magic, total in sorted_magics[:10]:
    status = "NEW" if int(magic.replace('Magic', '')) >= 13 else ""
    print(f"  {magic}: {total:+,} points {status}")

# Sample 10min sheet
print("\n" + "=" * 100)
print("Sample 10min Sheet (first 5 positions):")
print("=" * 100)
df_10 = pd.read_excel(xl, sheet_name='10min')
print(df_10[['#Code', 'Ticket', 'Magic Number', 'Outcome', 'OutcomePoints']].head().to_string())

# New magic numbers check
print("\n" + "=" * 100)
print("NEW MAGIC NUMBERS (13-19) - Position counts in 10min sheet:")
print("=" * 100)
for m in range(13, 20):
    count = len(df_10[df_10['Magic Number'] == m])
    if count > 0:
        code = df_10[df_10['Magic Number'] == m].iloc[0]['#Code'] if count > 0 else 'N/A'
        total = df_10[df_10['Magic Number'] == m]['OutcomePoints'].sum()
        print(f"  Magic {m} ({code}): {count} positions, {total:+} points")
    else:
        print(f"  Magic {m}: No positions yet (may start later in day)")
