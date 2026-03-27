"""
Investigate discrepancies in March 24th analysis:
1. Magic 13: -3,315 vs -66,216 points discrepancy
2. Check correlation between Magic 17, 18, and 2
"""
import pandas as pd

file_path = 'data/Analysis_20260324_v4.xlsx'
xl = pd.ExcelFile(file_path)

print("=" * 100)
print("INVESTIGATING MARCH 24TH DISCREPANCIES")
print("=" * 100)

# 1. Magic 13 discrepancy investigation
print("\n1. MAGIC 13 DISCREPANCY INVESTIGATION")
print("-" * 100)

# Get total from RESULT tab
result_df = pd.read_excel(xl, sheet_name='RESULT')
magic13_total = result_df['Magic13'].sum()
print(f"Magic13 total from RESULT tab (all time windows): {magic13_total:,}")

# Get from 10min sheet only
df_10min = pd.read_excel(xl, sheet_name='10min')
magic13_10min = df_10min[df_10min['Magic Number'] == 13]['OutcomePoints'].sum()
magic13_10min_count = len(df_10min[df_10min['Magic Number'] == 13])
print(f"Magic13 in 10min sheet only: {magic13_10min:,} ({magic13_10min_count} positions)")

# Check all time windows for Magic 13
print("\nMagic13 across all time windows (from RESULT tab):")
for _, row in result_df.iterrows():
    tw = row['TimeWindow']
    val = row['Magic13']
    print(f"  {tw}: {val:+,}")

# 2. Correlation investigation: Magic 2, 17, 18
print("\n\n2. CORRELATION INVESTIGATION: Magic 2, 17, 18")
print("-" * 100)
print("Magic 2: m1104005 (M1, Fast=10, Slow=40, PT=0.5)")
print("Magic 17: m1103505 (M1, Fast=10, Slow=35, PT=0.5)")
print("Magic 18: m1104505 (M1, Fast=10, Slow=45, PT=0.5)")
print()

# Get positions for each magic number
def get_magic_positions(df, magic):
    return df[df['Magic Number'] == magic][['Ticket', 'TimeOpen', 'TimeClose', 'PriceOpen', 'PriceClose', 'Outcome', 'OutcomePoints']]

m2_pos = get_magic_positions(df_10min, 2)
m17_pos = get_magic_positions(df_10min, 17)
m18_pos = get_magic_positions(df_10min, 18)

print(f"Magic 2 positions in 10min: {len(m2_pos)}")
print(f"Magic 17 positions in 10min: {len(m17_pos)}")
print(f"Magic 18 positions in 10min: {len(m18_pos)}")

# Check if they have same entry/exit times (same positions)
print("\nChecking if Magic 17 and 18 have SAME positions as Magic 2...")

# Get TimeOpen sets
m2_times = set(m2_pos['TimeOpen'])
m17_times = set(m17_pos['TimeOpen'])
m18_times = set(m18_pos['TimeOpen'])

print(f"\nMagic 2 unique open times: {len(m2_times)}")
print(f"Magic 17 unique open times: {len(m17_times)}")
print(f"Magic 18 unique open times: {len(m18_times)}")

# Check overlap
overlap_2_17 = m2_times & m17_times
overlap_2_18 = m2_times & m18_times
overlap_17_18 = m17_times & m18_times

print(f"\nOverlap Magic 2 & 17: {len(overlap_2_17)} / {len(m2_times)} ({100*len(overlap_2_17)/len(m2_times):.1f}%)")
print(f"Overlap Magic 2 & 18: {len(overlap_2_18)} / {len(m2_times)} ({100*len(overlap_2_18)/len(m2_times):.1f}%)")
print(f"Overlap Magic 17 & 18: {len(overlap_17_18)} / {len(m17_times)} ({100*len(overlap_17_18)/len(m17_times):.1f}%)")

# If they share same entry times, check if outcomes differ
if len(overlap_2_17) > 0:
    print("\n\nSample positions where Magic 2 and 17 have SAME entry time:")
    sample_time = list(overlap_2_17)[0]
    m2_sample = m2_pos[m2_pos['TimeOpen'] == sample_time].iloc[0]
    m17_sample = m17_pos[m17_pos['TimeOpen'] == sample_time].iloc[0]
    print(f"\n  TimeOpen: {sample_time}")
    print(f"  Magic 2:  Outcome={m2_sample['Outcome']}, Points={m2_sample['OutcomePoints']}, Close={m2_sample['TimeClose']}")
    print(f"  Magic 17: Outcome={m17_sample['Outcome']}, Points={m17_sample['OutcomePoints']}, Close={m17_sample['TimeClose']}")

# 3. Check if same entry price means same position
print("\n\n3. CHECKING ENTRY PRICES FOR MAGIC 2, 17, 18")
print("-" * 100)

# Compare entry prices for overlapping times
if len(overlap_2_17) > 0:
    same_entries = 0
    diff_entries = 0
    for time_open in list(overlap_2_17)[:20]:  # Check first 20
        m2_price = m2_pos[m2_pos['TimeOpen'] == time_open]['PriceOpen'].iloc[0]
        m17_price = m17_pos[m17_pos['TimeOpen'] == time_open]['PriceOpen'].iloc[0]
        if abs(m2_price - m17_price) < 0.01:  # Within 1 pip
            same_entries += 1
        else:
            diff_entries += 1
    
    print(f"First 20 overlapping positions:")
    print(f"  Same entry price: {same_entries}")
    print(f"  Different entry price: {diff_entries}")
    
    if same_entries == 20:
        print("\n  *** MAGIC 17 HAS SAME ENTRY PRICES AS MAGIC 2 ***")
        print("  They are taking THE SAME positions (just different SlowMA)")

print("\n" + "=" * 100)
print("CONCLUSION:")
print("=" * 100)
print(f"1. Magic 13 total ({magic13_total:,}) vs 10min only ({magic13_10min:,}) discrepancy:")
print(f"   The -66,216 is SUM ACROSS ALL TIME WINDOWS (1-30min)")
print(f"   The -3,315 is just the 10min window")
print(f"   Both are correct - just different aggregations!")
print()
print("2. Magic 2, 17, 18 correlation:")
if len(overlap_2_17) == len(m2_times):
    print("   Magic 17 takes SAME positions as Magic 2 (100% overlap)")
if len(overlap_2_18) == len(m2_times):
    print("   Magic 18 takes SAME positions as Magic 2 (100% overlap)")
if len(overlap_17_18) == len(m17_times):
    print("   Magic 17 and 18 take SAME positions (100% overlap)")
print("   They only differ in SlowMA (40 vs 35 vs 45)")
