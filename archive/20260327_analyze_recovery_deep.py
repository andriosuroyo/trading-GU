"""
Deep Recovery Analysis - Extended X values and distributions
"""
import pandas as pd
import numpy as np


dates = ['20260320', '20260323', '20260324']

# Extended opposing thresholds
opposing_thresholds = [5, 8, 10, 12, 15, 20, 25, 30]

print("=" * 120)
print("DEEP RECOVERY ANALYSIS - Extended X Values and Distributions")
print("=" * 120)

# Process each date
all_trades = []

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        df_10min = pd.read_excel(file_path, sheet_name='10min')
        df_30min = pd.read_excel(file_path, sheet_name='30min')
        
        df_10min['TimeOpen'] = pd.to_datetime(df_10min['TimeOpen'])
        
        losing_trades = df_10min[df_10min['OutcomePoints'] < 0].copy()
        
        for _, trade in losing_trades.iterrows():
            ticket = trade['Ticket']
            magic = trade['Magic Number']
            direction = trade['Type']
            open_time = trade['TimeOpen']
            open_price = trade['PriceOpen']
            sl_outcome = trade['OutcomePoints']
            
            trade_info = {
                'Date': date_str,
                'Ticket': ticket,
                'Magic': magic,
                'Direction': direction,
                'OpenTime': open_time,
                'OpenPrice': open_price,
                'SL_Outcome': sl_outcome
            }
            
            # Get recovery status at 30min
            mfe30_row = df_30min[df_30min['Ticket'] == ticket]
            if len(mfe30_row) > 0:
                mfe30 = mfe30_row['MFE30Points'].values[0]
                trade_info['Recovered_30min'] = mfe30 >= abs(sl_outcome)
                trade_info['MFE_30min'] = mfe30
            else:
                trade_info['Recovered_30min'] = False
                trade_info['MFE_30min'] = 0
            
            # Count opposing positions within 60min window (most promising based on previous analysis)
            opposing_direction = 'SELL' if direction == 'BUY' else 'BUY'
            later_trades = df_10min[df_10min['TimeOpen'] > open_time].copy()
            opposing_positions = later_trades[later_trades['Type'] == opposing_direction]
            
            window_end = open_time + pd.Timedelta(minutes=60)
            opposing_in_60min = opposing_positions[opposing_positions['TimeOpen'] <= window_end]
            trade_info['Opposing_60min'] = len(opposing_in_60min)
            
            all_trades.append(trade_info)
            
    except Exception as e:
        print(f"{date_str}: Error - {e}")

# Convert to DataFrame
df_all = pd.DataFrame(all_trades)

if len(df_all) == 0:
    print("\nNo data collected.")
    exit()

print(f"\nTotal losing trades analyzed: {len(df_all)}")

# Distribution of opposing positions in 60min window
print("\n" + "=" * 120)
print("DISTRIBUTION: Opposing Positions within 60min of Loss")
print("=" * 120)
opposing_dist = df_all['Opposing_60min'].value_counts().sort_index()
print(opposing_dist.to_string())
print(f"\nMean opposing positions: {df_all['Opposing_60min'].mean():.1f}")
print(f"Median opposing positions: {df_all['Opposing_60min'].median():.1f}")
print(f"Max opposing positions: {df_all['Opposing_60min'].max()}")

# Recovery rate vs opposing positions
print("\n" + "=" * 120)
print("RECOVERY SUCCESS vs OPPOSING POSITIONS")
print("=" * 120)

recovery_by_opposing = df_all.groupby('Opposing_60min').agg({
    'Recovered_30min': ['count', 'sum', 'mean'],
    'SL_Outcome': 'mean'
}).round(3)
recovery_by_opposing.columns = ['Total_Trades', 'Recoveries', 'Recovery_Rate', 'Avg_SL_Loss']
recovery_by_opposing['Recovery_Rate_Pct'] = recovery_by_opposing['Recovery_Rate'] * 100
print(recovery_by_opposing.to_string())

# Test different X thresholds
print("\n" + "=" * 120)
print("RECOVERY PERFORMANCE BY X THRESHOLD (60min window)")
print("=" * 120)

results = []
for x in opposing_thresholds:
    eligible = df_all[df_all['Opposing_60min'] < x]
    wins = eligible['Recovered_30min'].sum()
    total = len(eligible)
    total_profit = eligible[eligible['Recovered_30min'] == True]['SL_Outcome'].abs().sum()
    lost_opposing = len(df_all[df_all['Opposing_60min'] >= x])
    
    win_rate = (wins / total * 100) if total > 0 else 0
    
    results.append({
        'X_Threshold': x,
        'Eligible_Trades': total,
        'Wins': wins,
        'WinRate': win_rate,
        'Lost_Opposing_Filter': lost_opposing,
        'Total_Profit': total_profit,
        'Avg_Profit_Per_Win': (total_profit / wins) if wins > 0 else 0,
        'Efficiency': total_profit / 158  # Profit per original losing trade
    })
    
    print(f"X={x:2d}: Eligible={total:3}/158 ({total/158*100:5.1f}%) | Wins={wins:2}/{total} ({win_rate:5.1f}%) | "
          f"Profit={total_profit:7,.0f} | Efficiency={total_profit/158:6.1f} pts/trade")

df_results = pd.DataFrame(results)

# Find optimal
best = df_results.loc[df_results['Total_Profit'].idxmax()]
print(f"\nOPTIMAL: X={best['X_Threshold']}")
print(f"  Win Rate: {best['WinRate']:.1f}% ({best['Wins']}/{best['Eligible_Trades']})")
print(f"  Total Profit: {best['Total_Profit']:,.0f} pts")
print(f"  Efficiency: {best['Efficiency']:.1f} pts per original losing trade")

# By Magic Number - which ones have best recovery rates?
print("\n" + "=" * 120)
print("RECOVERY BY MAGIC NUMBER (X=10 threshold)")
print("=" * 120)

magic_recovery = []
for magic in sorted(df_all['Magic'].unique()):
    magic_df = df_all[df_all['Magic'] == magic]
    total_losses = len(magic_df)
    eligible = magic_df[magic_df['Opposing_60min'] < 10]
    wins = eligible['Recovered_30min'].sum()
    win_rate = (wins / len(eligible) * 100) if len(eligible) > 0 else 0
    
    magic_recovery.append({
        'Magic': magic,
        'Total_Losses': total_losses,
        'Eligible': len(eligible),
        'Wins': wins,
        'WinRate': win_rate,
        'Avg_Opposing': magic_df['Opposing_60min'].mean()
    })

df_magic = pd.DataFrame(magic_recovery)
df_magic = df_magic.sort_values('WinRate', ascending=False)
print(df_magic.to_string(index=False))

# Save detailed data
df_all.to_csv('recovery_detailed_trades.csv', index=False)
df_results.to_csv('recovery_x_thresholds.csv', index=False)
df_magic.to_csv('recovery_by_magic.csv', index=False)

print("\n" + "=" * 120)
print("FILES SAVED:")
print("  - recovery_detailed_trades.csv (all trades with opposing counts)")
print("  - recovery_x_thresholds.csv (X threshold comparison)")
print("  - recovery_by_magic.csv (per-magic recovery stats)")
print("=" * 120)
