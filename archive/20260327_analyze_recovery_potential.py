"""
Analyze Recovery Potential: After SL hit, how long until price returns to OpenPrice?
Concept: If signal has merit, price may return to breakeven (OpenPrice) after initial drawdown.
"""
import pandas as pd
import numpy as np

dates = ['20260320', '20260323', '20260324']

print("=" * 100)
print("RECOVERY POTENTIAL ANALYSIS")
print("=" * 100)
print("""
CONCEPT: When a position hits SL (time-based), does price eventually return to OpenPrice?
If yes, we could enter a "Recovery Trade" in the same direction when SL hits,
targeting the original OpenPrice (the "magnet").

Key Questions:
1. What % of losing trades return to OpenPrice within X minutes?
2. How long does recovery typically take?
3. What's the max drawdown during recovery (risk sizing)?
4. Which magic numbers have best recovery rates?
""")

# Time windows to check for recovery (in minutes)
recovery_windows = [5, 10, 15, 20, 30, 60, 120]

all_recovery_data = []

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        # Read 1min data for all windows
        df_1min = pd.read_excel(file_path, sheet_name='1min')
        df_5min = pd.read_excel(file_path, sheet_name='5min')
        df_10min = pd.read_excel(file_path, sheet_name='10min')
        df_15min = pd.read_excel(file_path, sheet_name='15min')
        df_30min = pd.read_excel(file_path, sheet_name='30min')
        
        # Only analyze positions that ended in loss (time-based SL)
        losing_trades = df_10min[df_10min['OutcomePoints'] < 0].copy()
        
        print(f"\n{'='*100}")
        print(f"DATE: {date_str} - {len(losing_trades)} losing trades to analyze")
        print(f"{'='*100}")
        
        for _, trade in losing_trades.iterrows():
            ticket = trade['Ticket']
            magic = trade['Magic Number']
            code = trade['#Code']
            direction = trade['Type']
            open_price = trade['PriceOpen']
            outcome = trade['OutcomePoints']
            
            recovery_info = {
                'Date': date_str,
                'Ticket': ticket,
                'Magic': magic,
                'Code': code,
                'Direction': direction,
                'OpenPrice': open_price,
                'SL_Outcome': outcome
            }
            
            # Check recovery at different time windows
            # Recovery = price returned to OpenPrice (breakeven)
            
            # 5min check
            mfe5 = df_5min[df_5min['Ticket'] == ticket]
            if len(mfe5) > 0:
                mfe5_pts = mfe5['MFE5Points'].values[0]
                recovery_info['MFE_5min'] = mfe5_pts
                recovery_info['Recovered_5min'] = mfe5_pts >= abs(outcome)  # Returned to at least breakeven
            else:
                recovery_info['Recovered_5min'] = False
            
            # 15min check
            mfe15 = df_15min[df_15min['Ticket'] == ticket]
            if len(mfe15) > 0:
                mfe15_pts = mfe15['MFE15Points'].values[0]
                recovery_info['MFE_15min'] = mfe15_pts
                recovery_info['Recovered_15min'] = mfe15_pts >= abs(outcome)
            else:
                recovery_info['Recovered_15min'] = False
            
            # 30min check
            mfe30 = df_30min[df_30min['Ticket'] == ticket]
            if len(mfe30) > 0:
                mfe30_pts = mfe30['MFE30Points'].values[0]
                recovery_info['MFE_30min'] = mfe30_pts
                recovery_info['Recovered_30min'] = mfe30_pts >= abs(outcome)
            else:
                recovery_info['Recovered_30min'] = False
            
            all_recovery_data.append(recovery_info)
            
    except Exception as e:
        print(f"{date_str}: Error - {e}")

# Analysis
df_recovery = pd.DataFrame(all_recovery_data)

if len(df_recovery) > 0:
    print("\n" + "=" * 100)
    print("RECOVERY STATISTICS - ALL LOSING TRADES")
    print("=" * 100)
    
    total_losses = len(df_recovery)
    rec_5min = df_recovery['Recovered_5min'].sum()
    rec_15min = df_recovery['Recovered_15min'].sum()
    rec_30min = df_recovery['Recovered_30min'].sum()
    
    print(f"\nTotal losing trades analyzed: {total_losses}")
    print(f"\nRecovery Rate (price returned to breakeven or better):")
    print(f"  Within 5min:  {rec_5min}/{total_losses} ({rec_5min/total_losses*100:.1f}%)")
    print(f"  Within 15min: {rec_15min}/{total_losses} ({rec_15min/total_losses*100:.1f}%)")
    print(f"  Within 30min: {rec_30min}/{total_losses} ({rec_30min/total_losses*100:.1f}%)")
    
    # Recovery potential profit
    print(f"\n--- Recovery Trade Potential (if entered at SL, targeting OpenPrice) ---")
    
    # For recovered trades, calculate the "recovery profit"
    # If we entered at SL price (OpenPrice + outcome points), targeting OpenPrice
    # Recovery profit = abs(outcome) + the additional MFE
    
    rec_15_trades = df_recovery[df_recovery['Recovered_15min'] == True]
    if len(rec_15_trades) > 0:
        avg_sl_outcome = rec_15_trades['SL_Outcome'].mean()
        avg_mfe_15 = rec_15_trades['MFE_15min'].mean()
        # Recovery profit = distance from SL to OpenPrice + any overshoot
        recovery_profit_per_trade = abs(avg_sl_outcome) + (avg_mfe_15 - abs(avg_sl_outcome))
        print(f"\nTrades recovered by 15min: {len(rec_15_trades)}")
        print(f"  Avg SL loss: {avg_sl_outcome:.0f} pts")
        print(f"  Avg MFE at 15min: {avg_mfe_15:.0f} pts")
        print(f"  Potential recovery profit per trade: ~{recovery_profit_per_trade:.0f} pts")
        print(f"  Total recovery potential: {len(rec_15_trades) * recovery_profit_per_trade:.0f} pts")
    
    # By Magic Number
    print("\n" + "=" * 100)
    print("RECOVERY BY MAGIC NUMBER")
    print("=" * 100)
    
    magic_stats = []
    for magic in sorted(df_recovery['Magic'].unique()):
        magic_df = df_recovery[df_recovery['Magic'] == magic]
        count = len(magic_df)
        rec_15 = magic_df['Recovered_15min'].sum()
        rec_30 = magic_df['Recovered_30min'].sum()
        
        magic_stats.append({
            'Magic': magic,
            'Losses': count,
            'Rec15': rec_15,
            'Rec15%': rec_15/count*100 if count > 0 else 0,
            'Rec30': rec_30,
            'Rec30%': rec_30/count*100 if count > 0 else 0
        })
    
    df_magic_stats = pd.DataFrame(magic_stats)
    print(df_magic_stats.to_string(index=False))
    
    # Save results
    df_recovery.to_csv('recovery_analysis_detailed.csv', index=False)
    df_magic_stats.to_csv('recovery_by_magic.csv', index=False)
    print("\nSaved to recovery_analysis_detailed.csv and recovery_by_magic.csv")

else:
    print("\nNo recovery data collected.")
