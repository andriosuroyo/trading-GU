"""
Analyze specific scenarios:
1. 2800 pts SL across whole dataset (all hours)
2. Asia session major loss breakdown (which trades, dates, hours)
3. Confirm London-NY session figures
"""
import pandas as pd
from datetime import datetime

dates = ['20260320', '20260323', '20260324']

print("=" * 100)
print("SCENARIO ANALYSIS")
print("=" * 100)

# 1. Fixed 2800 SL across all hours
print("\n1. FIXED 2800 SL ACROSS ALL HOURS (All 3 Days)")
print("-" * 100)

total_trades = 0
total_profits = 0
total_losses = 0
total_outcome = 0

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df = pd.read_excel(file_path, sheet_name='15min')
        
        # Simulate 2800 SL
        df['SL_Hit'] = df['MAE15Points'] >= 2800
        df['SimulatedOutcome'] = df.apply(
            lambda row: -2800 if row['SL_Hit'] else row['OutcomePoints'], axis=1
        )
        
        profits = (df['SimulatedOutcome'] > 0).sum()
        losses = (df['SimulatedOutcome'] < 0).sum()
        sl_hits = df['SL_Hit'].sum()
        outcome = df['SimulatedOutcome'].sum()
        
        print(f"{date_str}: {len(df)} trades, {sl_hits} SL hits, Outcome: {outcome:+,.0f} pts")
        
        total_trades += len(df)
        total_profits += profits
        total_losses += losses
        total_outcome += outcome
        
    except Exception as e:
        print(f"{date_str}: Error - {e}")

print(f"\n3-DAY TOTAL with 2800 SL:")
print(f"  Total trades: {total_trades}")
print(f"  Profits: {total_profits}, Losses: {total_losses}")
print(f"  Win rate: {100*total_profits/total_trades:.1f}%")
print(f"  TOTAL OUTCOME: {total_outcome:+,.0f} points")

# 2. Asia session breakdown - which trades caused major losses
print("\n\n2. ASIA SESSION MAJOR LOSS BREAKDOWN (01:00-08:00)")
print("-" * 100)

asia_losses = []

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df = pd.read_excel(file_path, sheet_name='15min')
        df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
        
        # Asia session: 01:00-08:00
        asia = df[(df['Hour'] >= 1) & (df['Hour'] < 8)]
        
        if len(asia) == 0:
            continue
        
        # Find worst trades
        worst = asia.nsmallest(5, 'OutcomePoints')
        
        print(f"\n{date_str} - Asia Session ({len(asia)} trades, Total: {asia['OutcomePoints'].sum():+,.0f}):")
        print("  Worst 5 trades:")
        for _, row in worst.iterrows():
            print(f"    {row['Ticket']} at {row['TimeOpen']}: {row['OutcomePoints']:+,.0f} pts (MAE: {row['MAE15Points']:.0f})")
            asia_losses.append({
                'Date': date_str,
                'Ticket': row['Ticket'],
                'Time': row['TimeOpen'],
                'Hour': row['Hour'],
                'Outcome': row['OutcomePoints'],
                'MAE': row['MAE15Points']
            })
        
        # Hourly breakdown
        print("  Hourly breakdown:")
        for hour in range(1, 8):
            hour_data = asia[asia['Hour'] == hour]
            if len(hour_data) > 0:
                print(f"    {hour:02d}:00 - {len(hour_data)} trades, {hour_data['OutcomePoints'].sum():+,.0f} pts")
        
    except Exception as e:
        print(f"{date_str}: Error - {e}")

# 3. London-NY session confirmation
print("\n\n3. LONDON-NY SESSION CONFIRMATION (08:00-23:00)")
print("-" * 100)

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df = pd.read_excel(file_path, sheet_name='15min')
        df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
        
        # London-NY: 08:00-23:00
        london_ny = df[(df['Hour'] >= 8) & (df['Hour'] < 23)]
        
        # Asia: 01:00-08:00
        asia = df[(df['Hour'] >= 1) & (df['Hour'] < 8)]
        
        print(f"{date_str}:")
        print(f"  Asia (01-08):     {len(asia):3d} trades, {asia['OutcomePoints'].sum():+10,.0f} pts")
        print(f"  London-NY (08-23): {len(london_ny):3d} trades, {london_ny['OutcomePoints'].sum():+10,.0f} pts")
        print(f"  Total:            {len(df):3d} trades, {df['OutcomePoints'].sum():+10,.0f} pts")
        
    except Exception as e:
        print(f"{date_str}: Error - {e}")

# Summary
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print("\nLondon-NY Only (08:00-23:00) vs All Hours:")
print("  Date        | All Hours | London-NY | Difference")
print("  " + "-" * 55)

all_total = 0
ln_total = 0

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df = pd.read_excel(file_path, sheet_name='15min')
        df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
        
        all_outcome = df['OutcomePoints'].sum()
        ln_outcome = df[(df['Hour'] >= 8) & (df['Hour'] < 23)]['OutcomePoints'].sum()
        
        print(f"  {date_str} | {all_outcome:+9,.0f} | {ln_outcome:+9,.0f} | {ln_outcome - all_outcome:+9,.0f}")
        
        all_total += all_outcome
        ln_total += ln_outcome
        
    except:
        pass

print(f"  {'Total':<11} | {all_total:+9,.0f} | {ln_total:+9,.0f} | {ln_total - all_total:+9,.0f}")

print(f"\n[ANSWER] London-NY (08-23) outcome over 3 days: {ln_total:+,.0f} points")
print(f"[ANSWER] Asia session (01-08) outcome: {all_total - ln_total:+,.0f} points")
