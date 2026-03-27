"""
1. Find positions with MAE > 6000 points
2. Overall performance of Magic 4 and 5 over 3 days
"""
import pandas as pd

dates = ['20260320', '20260323', '20260324']

print("=" * 100)
print("1. EXTREME MAE ANALYSIS (Positions > 6000 points)")
print("=" * 100)

extreme_positions = []

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df = pd.read_excel(file_path, sheet_name='15min')
        
        # Find positions with MAE > 6000
        extreme = df[df['MAE15Points'] > 6000]
        
        if len(extreme) > 0:
            print(f"\n{date_str}: {len(extreme)} positions with MAE > 6000")
            print(extreme[['Ticket', 'Magic Number', 'TimeOpen', 'MAE15Points', 'OutcomePoints']].to_string())
            
            for _, row in extreme.iterrows():
                extreme_positions.append({
                    'Date': date_str,
                    'Ticket': row['Ticket'],
                    'Magic': row['Magic Number'],
                    'MAE': row['MAE15Points'],
                    'Outcome': row['OutcomePoints']
                })
        else:
            print(f"\n{date_str}: No positions with MAE > 6000")
            
    except Exception as e:
        print(f"{date_str}: Error - {e}")

if extreme_positions:
    print("\n" + "=" * 100)
    print("SUMMARY OF EXTREME MAE POSITIONS")
    print("=" * 100)
    df_extreme = pd.DataFrame(extreme_positions)
    print(f"\nTotal positions with MAE > 6000: {len(df_extreme)}")
    print(f"Max MAE: {df_extreme['MAE'].max():.0f} points")
    print(f"Average MAE: {df_extreme['MAE'].mean():.0f} points")
    print(f"Total outcome: {df_extreme['Outcome'].sum():,.0f} points")

print("\n\n" + "=" * 100)
print("2. MAGIC 4 & 5 PERFORMANCE (M15 50/100 and 50/200)")
print("=" * 100)

magic4_total = 0
magic5_total = 0
magic4_trades = 0
magic5_trades = 0

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df = pd.read_excel(file_path, sheet_name='15min')
        
        magic4 = df[df['Magic Number'] == 4]
        magic5 = df[df['Magic Number'] == 5]
        
        m4_outcome = magic4['OutcomePoints'].sum()
        m5_outcome = magic5['OutcomePoints'].sum()
        m4_count = len(magic4)
        m5_count = len(magic5)
        
        print(f"\n{date_str}:")
        print(f"  Magic 4 (m1501H05 - 50/100): {m4_count} trades, {m4_outcome:+.0f} pts")
        print(f"  Magic 5 (m1502H05 - 50/200): {m5_count} trades, {m5_outcome:+.0f} pts")
        
        magic4_total += m4_outcome
        magic5_total += m5_outcome
        magic4_trades += m4_count
        magic5_trades += m5_count
        
    except Exception as e:
        print(f"{date_str}: Error - {e}")

print("\n" + "=" * 100)
print("3-DAY TOTALS FOR MAGIC 4 & 5")
print("=" * 100)
print(f"\nMagic 4 (m1501H05 - M15 50/100):")
print(f"  Total trades: {magic4_trades}")
print(f"  Total outcome: {magic4_total:+.0f} points")
print(f"  Avg per trade: {magic4_total/magic4_trades:.0f} points" if magic4_trades > 0 else "  N/A")

print(f"\nMagic 5 (m1502H05 - M15 50/200):")
print(f"  Total trades: {magic5_trades}")
print(f"  Total outcome: {magic5_total:+.0f} points")
print(f"  Avg per trade: {magic5_total/magic5_trades:.0f} points" if magic5_trades > 0 else "  N/A")

print(f"\nCombined (Magic 4 + 5):")
print(f"  Total trades: {magic4_trades + magic5_trades}")
print(f"  Total outcome: {magic4_total + magic5_total:+.0f} points")

if magic4_total + magic5_total < 0:
    print(f"\n  VERDICT: UNDERPERFORMING - Consider deactivation")
else:
    print(f"\n  VERDICT: PROFITABLE - Continue running")

print("\n" + "=" * 100)
