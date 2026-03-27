"""
Analyze March 20, 23, 24 data to validate 01:00-23:00 trading window
Exclude first hour (00:00-01:00) and last hour (23:00-00:00)
"""
import pandas as pd
from datetime import datetime

dates = ['20260320', '20260323', '20260324']

print("=" * 100)
print("TRADING HOURS ANALYSIS: Full Day vs 01:00-23:00 Window")
print("=" * 100)

all_results = []

for date_str in dates:
    # Handle different file naming conventions
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'  # Original file
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df = pd.read_excel(file_path, sheet_name='15min')  # Use 15min as standard
        
        # Parse TimeOpen to extract hour
        df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
        
        # Full day stats
        full_day = df['OutcomePoints'].sum()
        full_count = len(df)
        
        # 01:00-23:00 only (exclude 00:00 and 23:00)
        filtered = df[(df['Hour'] >= 1) & (df['Hour'] <= 22)]
        window_total = filtered['OutcomePoints'].sum()
        window_count = len(filtered)
        
        # What we excluded
        excluded = df[(df['Hour'] == 0) | (df['Hour'] == 23)]
        excluded_total = excluded['OutcomePoints'].sum()
        excluded_count = len(excluded)
        
        all_results.append({
            'Date': date_str,
            'Full_Day_Total': full_day,
            'Full_Day_Count': full_count,
            'Window_Total': window_total,
            'Window_Count': window_count,
            'Excluded_Total': excluded_total,
            'Excluded_Count': excluded_count
        })
        
        print(f"\n{date_str}:")
        print(f"  Full Day (24h):   {full_day:+10,} pts | {full_count} positions")
        print(f"  01:00-23:00:      {window_total:+10,} pts | {window_count} positions")
        print(f"  Excluded (0h/23h): {excluded_total:+10,} pts | {excluded_count} positions")
        
        if excluded_total < 0:
            print(f"  [OK] Excluding first/last hour AVOIDED {abs(excluded_total):,} pts of losses")
        elif excluded_total > 0:
            print(f"  [WARNING] Excluding first/last hour SACRIFICED {excluded_total:,} pts of gains")
            
    except Exception as e:
        print(f"\n{date_str}: Error - {e}")

# Summary
print("\n" + "=" * 100)
print("3-DAY SUMMARY")
print("=" * 100)

if all_results:
    df_summary = pd.DataFrame(all_results)
    
    total_full = df_summary['Full_Day_Total'].sum()
    total_window = df_summary['Window_Total'].sum()
    total_excluded = df_summary['Excluded_Total'].sum()
    
    print(f"\nCombined 3 Days:")
    print(f"  Full Day (24h):    {total_full:+12,} points")
    print(f"  01:00-23:00:       {total_window:+12,} points")
    print(f"  Excluded Hours:    {total_excluded:+12,} points")
    print(f"\n  Improvement by excluding 0h/23h: {total_window - total_full:+12,} points")
    
    if total_excluded < 0:
        print(f"\n[VERDICT] Excluding first/last hour AVOIDS {abs(total_excluded):,} points of losses")
        print("    RECOMMENDATION: Trade 01:00-23:00 only")
    else:
        print(f"\n[WARNING VERDICT] Excluding first/last hour SACRIFICES {total_excluded:,} points")
        print("    RECOMMENDATION: Keep trading 24h")

print("\n" + "=" * 100)
