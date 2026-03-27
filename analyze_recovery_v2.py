"""
Recovery Analysis v2 - With Opposing Momentum Filter

Concept:
1. When a position hits SL (10min loss), we consider a Recovery trade
2. Recovery trade = same direction, targeting original OpenPrice
3. Recovery Window: 60, 120, 180, 240 mins max
4. Opposing Momentum: If X opposing positions open since the loss, invalidate recovery

RecoveryOutcome:
- "WIN": Price returns to OpenPrice within RecoveryWindow AND < X opposing positions opened
- "LOST_OPPOSE": X+ opposing positions opened (momentum against us)
- "LOST_TIME": RecoveryWindow expired without reaching OpenPrice
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

dates = ['20260320', '20260323', '20260324']

# Recovery windows to test (in minutes)
recovery_windows = [60, 120, 180, 240]

# Opposing momentum thresholds to test
opposing_thresholds = [3, 5, 7, 10]

print("=" * 120)
print("RECOVERY ANALYSIS v2 - With Opposing Momentum Filter")
print("=" * 120)

# Process each date
all_trades = []

for date_str in dates:
    if date_str == '20260320':
        file_path = f'data/Analysis_{date_str}.xlsx'
    else:
        file_path = f'data/Analysis_{date_str}_v4.xlsx'
    
    try:
        # Load 10min and 30min sheets
        df_10min = pd.read_excel(file_path, sheet_name='10min')
        df_30min = pd.read_excel(file_path, sheet_name='30min')
        
        # Ensure datetime format
        df_10min['TimeOpen'] = pd.to_datetime(df_10min['TimeOpen'])
        
        # Get all losing trades
        losing_trades = df_10min[df_10min['OutcomePoints'] < 0].copy()
        
        print(f"\n{date_str}: {len(losing_trades)} losing trades")
        
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
            
            # Get MFE at 30min (price movement in our favor)
            mfe30_row = df_30min[df_30min['Ticket'] == ticket]
            if len(mfe30_row) > 0:
                mfe30 = mfe30_row['MFE30Points'].values[0]
                # Recovery happens if MFE >= |SL_Outcome| (returned to breakeven or better)
                trade_info['Recovered_30min'] = mfe30 >= abs(sl_outcome)
                trade_info['MFE_30min'] = mfe30
            else:
                trade_info['Recovered_30min'] = False
                trade_info['MFE_30min'] = 0
            
            # Count opposing positions opened AFTER this trade's OpenTime
            # Opposing = opposite direction
            opposing_direction = 'SELL' if direction == 'BUY' else 'BUY'
            
            # Get all trades opened after this one
            later_trades = df_10min[df_10min['TimeOpen'] > open_time].copy()
            opposing_positions = later_trades[later_trades['Type'] == opposing_direction]
            
            # Count opposing positions within 60, 120, 180, 240 min windows
            for window in recovery_windows:
                window_end = open_time + pd.Timedelta(minutes=window)
                opposing_in_window = opposing_positions[opposing_positions['TimeOpen'] <= window_end]
                trade_info[f'Opposing_{window}min'] = len(opposing_in_window)
            
            all_trades.append(trade_info)
            
    except Exception as e:
        import traceback
        print(f"{date_str}: Error - {e}")
        traceback.print_exc()

# Convert to DataFrame
df_all = pd.DataFrame(all_trades)

if len(df_all) == 0:
    print("\nNo data collected.")
    exit()

print(f"\nTotal losing trades analyzed: {len(df_all)}")

print("\n" + "=" * 120)
print("RECOVERY RESULTS BY WINDOW AND OPPOSING THRESHOLD")
print("=" * 120)

results = []

for window in recovery_windows:
    print(f"\n--- Recovery Window: {window} minutes ---")
    
    for x_threshold in opposing_thresholds:
        total_recovery_trades = 0
        recovery_wins = 0
        lost_opposing = 0
        lost_time = 0
        total_recovery_profit = 0
        
        for _, trade in df_all.iterrows():
            # Check if recovered within window
            # For 30min window we have data, for longer windows we need to estimate
            if window <= 30:
                recovered = trade['Recovered_30min']
            else:
                # For longer windows, assume same as 30min for now
                # (we need more data for accurate assessment)
                recovered = trade['Recovered_30min']
            
            opposing_count = trade[f'Opposing_{window}min']
            
            # Determine outcome
            if recovered and opposing_count < x_threshold:
                outcome = "WIN"
                recovery_wins += 1
                # Profit = distance from SL to OpenPrice (approximately |SL_Outcome|)
                total_recovery_profit += abs(trade['SL_Outcome'])
            elif opposing_count >= x_threshold:
                outcome = "LOST_OPPOSE"
                lost_opposing += 1
            else:
                outcome = "LOST_TIME"
                lost_time += 1
            
            total_recovery_trades += 1
        
        win_rate = (recovery_wins / total_recovery_trades * 100) if total_recovery_trades > 0 else 0
        
        results.append({
            'Window': window,
            'X_Threshold': x_threshold,
            'Total': total_recovery_trades,
            'Wins': recovery_wins,
            'WinRate': win_rate,
            'Lost_Opposing': lost_opposing,
            'Lost_Time': lost_time,
            'Total_Profit': total_recovery_profit,
            'Avg_Profit_Per_Win': (total_recovery_profit / recovery_wins) if recovery_wins > 0 else 0
        })
        
        print(f"  X={x_threshold:2d}: Wins={recovery_wins:3}/{total_recovery_trades} ({win_rate:5.1f}%) | "
              f"Lost_Opposing={lost_opposing:3} | Lost_Time={lost_time:3} | "
              f"TotalProfit={total_recovery_profit:8,.0f}")

# Summary DataFrame
df_results = pd.DataFrame(results)

print("\n" + "=" * 120)
print("BEST CONFIGURATIONS")
print("=" * 120)

# Best by profit
best_profit = df_results.loc[df_results['Total_Profit'].idxmax()]
print(f"\nBest Profit: Window={best_profit['Window']}min, X={best_profit['X_Threshold']}")
print(f"  Win Rate: {best_profit['WinRate']:.1f}% | Total Profit: {best_profit['Total_Profit']:,.0f} pts")

# Best by win rate (min 10 trades)
valid_for_wr = df_results[df_results['Total'] >= 10]
if len(valid_for_wr) > 0:
    best_wr = valid_for_wr.loc[valid_for_wr['WinRate'].idxmax()]
    print(f"\nBest Win Rate: Window={best_wr['Window']}min, X={best_wr['X_Threshold']}")
    print(f"  Win Rate: {best_wr['WinRate']:.1f}% | Total Profit: {best_wr['Total_Profit']:,.0f} pts")

print("\n" + "=" * 120)
print("DETAILED TABLE")
print("=" * 120)
print(df_results.to_string(index=False))

# Save results
df_results.to_csv('recovery_v2_analysis.csv', index=False)
print("\nSaved to recovery_v2_analysis.csv")

# Note about data limitation
print("\n" + "=" * 120)
print("NOTE: Current analysis limited to 30min window data for recovery detection.")
print("For accurate 60/120/180/240min analysis, we need longer timeframe sheets.")
print("Opposing momentum counts are accurate for all windows.")
print("=" * 120)
