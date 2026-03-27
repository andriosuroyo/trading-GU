"""
Analyze MAE by trading session for Fixed SL recommendations
Sessions: Asia (01:00-08:00), London (08:00-16:00), NY (16:00-23:00)
Overlaps: Asia-London (08:00), London-NY (16:00)
"""
import pandas as pd
from datetime import datetime

dates = ['20260320', '20260323', '20260324']

def get_session(hour):
    """Return session name based on hour (UTC)"""
    if 1 <= hour < 8:
        return 'Asia'
    elif 8 <= hour < 16:
        return 'London'
    elif 16 <= hour <= 22:
        return 'NY'
    elif hour == 23 or hour == 0:
        return 'Transition'  # Hour to avoid
    elif hour == 8:
        return 'Asia-London'
    elif hour == 16:
        return 'London-NY'
    else:
        return 'Other'

print("=" * 100)
print("MAE ANALYSIS BY TRADING SESSION")
print("Sessions: Asia (01-08), London (08-16), NY (16-23)")
print("=" * 100)

all_mae_data = []

for date_str in dates:
    # Handle different file naming conventions
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        # Use multiple time windows for comprehensive view
        for window in [5, 10, 15]:
            df = pd.read_excel(file_path, sheet_name=f'{window}min')
            
            # Parse time and assign session
            df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
            df['Session'] = df['Hour'].apply(get_session)
            
            # Get MAE column
            mae_col = f'MAE{window}Points'
            if mae_col not in df.columns:
                continue
            
            # Group by session
            for session in ['Asia', 'London', 'NY', 'Asia-London', 'London-NY']:
                session_df = df[df['Session'] == session]
                if len(session_df) == 0:
                    continue
                
                all_mae_data.append({
                    'Date': date_str,
                    'Window': f'{window}min',
                    'Session': session,
                    'Count': len(session_df),
                    'MAE_Mean': session_df[mae_col].mean(),
                    'MAE_Median': session_df[mae_col].median(),
                    'MAE_75th': session_df[mae_col].quantile(0.75),
                    'MAE_90th': session_df[mae_col].quantile(0.90),
                    'MAE_95th': session_df[mae_col].quantile(0.95),
                    'MAE_Max': session_df[mae_col].max(),
                    'Outcome': session_df['OutcomePoints'].sum()
                })
    except Exception as e:
        print(f"{date_str}: Error - {e}")

# Analysis
if all_mae_data:
    df_mae = pd.DataFrame(all_mae_data)
    
    print("\n" + "=" * 100)
    print("MAE STATISTICS BY SESSION (Combined 3 Days)")
    print("=" * 100)
    
    for session in ['Asia', 'London', 'NY', 'Asia-London', 'London-NY']:
        session_data = df_mae[df_mae['Session'] == session]
        if len(session_data) == 0:
            continue
        
        print(f"\n{session} Session:")
        print(f"  Positions: {session_data['Count'].sum()}")
        print(f"  MAE Mean:    {session_data['MAE_Mean'].mean():6.1f} pts")
        print(f"  MAE Median:  {session_data['MAE_Median'].mean():6.1f} pts")
        print(f"  MAE 75th:    {session_data['MAE_75th'].mean():6.1f} pts")
        print(f"  MAE 90th:    {session_data['MAE_90th'].mean():6.1f} pts")
        print(f"  MAE 95th:    {session_data['MAE_95th'].mean():6.1f} pts")
        print(f"  MAE Max:     {session_data['MAE_Max'].max():6.0f} pts")
        print(f"  Total Outcome: {session_data['Outcome'].sum():+8,} pts")
    
    # Fixed SL recommendations
    print("\n" + "=" * 100)
    print("FIXED SL RECOMMENDATIONS (Data-Driven)")
    print("=" * 100)
    
    print("\nBased on 90th percentile MAE (allows 90% of trades to breathe):")
    
    for session in ['Asia', 'London', 'NY']:
        session_data = df_mae[df_mae['Session'] == session]
        if len(session_data) == 0:
            continue
        
        p90 = session_data['MAE_90th'].mean()
        p95 = session_data['MAE_95th'].mean()
        
        # Round to nearest 50 for practical use
        sl_recommendation = round(p90 / 50) * 50
        
        print(f"\n  {session}:")
        print(f"    MAE 90th percentile: {p90:.0f} pts")
        print(f"    MAE 95th percentile: {p95:.0f} pts")
        print(f"    [OK] Recommended Fixed SL: {sl_recommendation} pts")
    
    # Compare overlaps
    print("\n" + "=" * 100)
    print("SESSION OVERLAP ANALYSIS")
    print("=" * 100)
    
    for overlap in ['Asia-London', 'London-NY']:
        overlap_data = df_mae[df_mae['Session'] == overlap]
        if len(overlap_data) == 0:
            continue
        
        print(f"\n{overlap} Overlap (single hour):")
        print(f"  Positions: {overlap_data['Count'].sum()}")
        print(f"  MAE 90th: {overlap_data['MAE_90th'].mean():.0f} pts")
        print(f"  Outcome: {overlap_data['Outcome'].sum():+,.0f} pts")
    
    print("\n" + "=" * 100)
