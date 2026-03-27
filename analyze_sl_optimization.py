"""
Test different Fixed SL values across sessions
3000, 3500, 4000, 4500, 5000
"""
import pandas as pd

dates = ['20260320', '20260323', '20260324']
sl_values = [2800, 3000, 3500, 4000, 4500, 5000]
sessions = {
    'Asia': (1, 8),      # 01:00-08:00
    'London': (8, 16),   # 08:00-16:00
    'NY': (16, 23),      # 16:00-23:00
}

print("=" * 100)
print("FIXED SL OPTIMIZATION ACROSS SESSIONS")
print("=" * 100)

results = []

for sl in sl_values:
    print(f"\n--- Testing SL = {sl} pts ---")
    
    for session_name, (start_hour, end_hour) in sessions.items():
        total_outcome = 0
        total_trades = 0
        total_sl_hits = 0
        
        for date_str in dates:
            if date_str == '20260320':
                file_path = f'data/Analysis_{date_str}.xlsx'
            else:
                file_path = f'data/Analysis_{date_str}_v4.xlsx'
            
            try:
                df = pd.read_excel(file_path, sheet_name='15min')
                df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
                
                # Filter by session
                session_df = df[(df['Hour'] >= start_hour) & (df['Hour'] < end_hour)]
                
                if len(session_df) == 0:
                    continue
                
                # Simulate SL
                mae_col = 'MAE15Points'
                sl_hits = (session_df[mae_col] >= sl).sum()
                simulated = session_df.apply(
                    lambda row: -sl if row[mae_col] >= sl else row['OutcomePoints'], axis=1
                )
                
                total_outcome += simulated.sum()
                total_trades += len(session_df)
                total_sl_hits += sl_hits
                
            except Exception as e:
                pass
        
        results.append({
            'SL': sl,
            'Session': session_name,
            'Trades': total_trades,
            'SL_Hits': total_sl_hits,
            'Hit_Rate': 100 * total_sl_hits / total_trades if total_trades > 0 else 0,
            'Outcome': total_outcome
        })
        
        print(f"  {session_name:7s}: {total_trades:3d} trades, {total_sl_hits:3d} SL hits ({100*total_sl_hits/total_trades:4.1f}%), Outcome: {total_outcome:+8,.0f} pts")

# Summary table
print("\n" + "=" * 100)
print("SUMMARY: Best SL by Session")
print("=" * 100)

df_results = pd.DataFrame(results)

for session in ['Asia', 'London', 'NY']:
    print(f"\n{session} Session:")
    session_data = df_results[df_results['Session'] == session].sort_values('Outcome', ascending=False)
    print(session_data[['SL', 'Trades', 'SL_Hits', 'Hit_Rate', 'Outcome']].to_string(index=False))
    
    best = session_data.iloc[0]
    print(f"  [BEST] SL = {best['SL']} pts: {best['Outcome']:+,.0f} pts ({best['Hit_Rate']:.1f}% hit rate)")

print("\n" + "=" * 100)
print("RECOMMENDED SESSION-BASED SL:")
print("=" * 100)

for session in ['Asia', 'London', 'NY']:
    session_data = df_results[df_results['Session'] == session]
    best = session_data.loc[session_data['Outcome'].idxmax()]
    print(f"  {session:7s}: {best['SL']} pts ({best['Outcome']:+,.0f} pts)")
