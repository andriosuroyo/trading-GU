"""
Comprehensive Analysis: Time Window × ATR Multiplier Matrix
6 timeframes (5, 10, 15, 20, 25, 30 min) × 9 multipliers (0.2-1.0)
Total: 54 combinations + RESULT summary
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import numpy as np

def load_env():
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def connect_blackbull():
    env_vars = load_env()
    terminal_path = env_vars.get('MT5_TERMINAL_BLACKBULL')
    if not mt5.initialize(path=terminal_path):
        return False
    return True

def get_atr_m1_60(symbol, target_time):
    from_time = target_time - timedelta(hours=2)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, target_time)
    if rates is None or len(rates) < 60:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr_60'] = df['tr'].rolling(window=60).mean()
    df_before = df[df['time'] <= target_time]
    if df_before.empty:
        return None
    return df_before['atr_60'].iloc[-1]

def get_tick_data_blackbull(from_time, to_time):
    ticks = mt5.copy_ticks_range('XAUUSDp', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def analyze_all_timeframes(position, time_windows, multipliers):
    """
    Analyze a position across all time windows and multipliers
    Returns nested dict: results[time_window][multiplier] = result
    """
    pos_id = position['pos_id']
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    magic = position['magic']
    
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    
    # Fetch ATR
    atr_value = get_atr_m1_60('XAUUSDp', open_time)
    if atr_value is None:
        atr_value = 0
    
    # Fetch max tick data (30min + buffer)
    max_window = max(time_windows)
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = open_time + timedelta(minutes=max_window) + timedelta(seconds=5)
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None
    
    # Pre-calculate MFE/MAE for each time window
    window_data = {}
    for minutes in time_windows:
        window_end = open_time + timedelta(minutes=minutes)
        window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_end)]
        
        if window_ticks.empty:
            continue
        
        if direction == 'BUY':
            mfe_price = window_ticks['ask'].max()
            mfe_points = round(abs((mfe_price - entry_price) * 100))
            mae_price = window_ticks['bid'].min()
            mae_points = round(abs((entry_price - mae_price) * 100))
            ticks_at_end = window_ticks[window_ticks['time'] <= window_end]
            price_at_end = ticks_at_end['bid'].iloc[-1] if not ticks_at_end.empty else exit_price
            points_at_end = round((price_at_end - entry_price) * 100)
        else:
            mfe_price = window_ticks['bid'].min()
            mfe_points = round(abs((entry_price - mfe_price) * 100))
            mae_price = window_ticks['ask'].max()
            mae_points = round(abs((mae_price - entry_price) * 100))
            ticks_at_end = window_ticks[window_ticks['time'] <= window_end]
            price_at_end = ticks_at_end['ask'].iloc[-1] if not ticks_at_end.empty else exit_price
            points_at_end = round((entry_price - price_at_end) * 100)
        
        actual_points = round((exit_price - entry_price) * 100) if direction == 'BUY' else round((entry_price - exit_price) * 100)
        
        window_data[minutes] = {
            'mfe_points': abs(mfe_points),
            'mae_points': abs(mae_points),
            'points_at_end': points_at_end,
            'actual_points': actual_points,
            'mfe_price': mfe_price if direction == 'BUY' else mfe_price,
            'mae_price': mae_price if direction == 'BUY' else mae_price,
        }
    
    if not window_data:
        return None
    
    # Calculate results for each (time, multiplier) combination
    results = {}
    for minutes in time_windows:
        if minutes not in window_data:
            continue
        
        results[minutes] = {}
        w_data = window_data[minutes]
        
        for mult in multipliers:
            atr_tp_points = round(atr_value * mult * 100)
            
            if w_data['mfe_points'] > atr_tp_points:
                outcome = 'PROFIT'
                outcome_points = atr_tp_points
            else:
                outcome = 'LOSS'
                outcome_points = w_data['points_at_end']
            
            results[minutes][mult] = {
                'Ticket': f'P{pos_id}',
                'Magic Number': magic,
                'Type': direction,
                'TimeOpen': open_time.strftime('%Y-%m-%d %H:%M:%S'),
                'PriceOpen': entry_price,
                'TimeClose': close_time.strftime('%Y-%m-%d %H:%M:%S'),
                'PriceClose': exit_price,
                'ActualPoints': w_data['actual_points'],
                'ATROpen': round(atr_value, 2),
                'TimeWindow': minutes,
                'Multiplier': mult,
                'ATRTP': atr_tp_points,
                f'MFE{minutes:02d}Price': round(w_data['mfe_price'], 2),
                f'MFE{minutes:02d}Points': w_data['mfe_points'],
                f'MAE{minutes:02d}Price': round(w_data['mae_price'], 2),
                f'MAE{minutes:02d}Points': w_data['mae_points'],
                'Outcome': outcome,
                'OutcomePoints': outcome_points
            }
    
    return results

def main(target_date_str='2026-03-20'):
    print("=" * 90)
    print("COMPREHENSIVE ANALYSIS: Time Window × ATR Multiplier")
    print("6 timeframes × 9 multipliers = 54 combinations")
    print("=" * 90)
    
    # Fetch positions dynamically for the target date
    from fetch_all_gu_positions import fetch_all_positions, connect_mt5 as connect_vantage
    from datetime import date
    
    print(f"\nFetching positions for {target_date_str}...")
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    
    if not connect_vantage("MT5_TERMINAL_VANTAGE"):
        print("Failed to connect to Vantage")
        return
    
    date_from = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    date_to = date_from + timedelta(days=1)
    
    all_positions = fetch_all_positions(date_from, date_to)
    
    # Filter for all GU positions (any magic number)
    target_positions = [p for p in all_positions if p.get('is_gu')]
    
    # Convert to expected format
    formatted_positions = []
    for p in target_positions:
        formatted_positions.append({
            'pos_id': p['pos_id'],
            'magic': str(p['magic']),
            'direction': p['direction'],
            'open_time': p['open_time'].isoformat() if hasattr(p['open_time'], 'isoformat') else p['open_time'],
            'close_time': p['close_time'].isoformat() if hasattr(p['close_time'], 'isoformat') else p['close_time'],
            'open_price': p['open_price'],
            'close_price': p['close_price']
        })
    
    target_positions = formatted_positions
    mt5.shutdown()
    
    print(f"Processing {len(target_positions)} positions...")
    
    if not connect_blackbull():
        print("Failed to connect")
        return
    
    time_windows = [5, 10, 15, 20, 25, 30]
    multipliers = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    try:
        # Collect all results
        all_results = {}
        for minutes in time_windows:
            all_results[minutes] = {mult: [] for mult in multipliers}
        
        # Process each position
        for i, pos in enumerate(target_positions):
            if i % 10 == 0:
                print(f"Processing position {i+1}/{len(target_positions)}...")
            
            pos_results = analyze_all_timeframes(pos, time_windows, multipliers)
            
            if pos_results:
                for minutes in time_windows:
                    if minutes in pos_results:
                        for mult in multipliers:
                            if mult in pos_results[minutes]:
                                all_results[minutes][mult].append(pos_results[minutes][mult])
        
        print("\nAll positions processed. Creating summary...")
        
        # Build summary table
        summary_rows = []
        for minutes in time_windows:
            for mult in multipliers:
                if all_results[minutes][mult]:
                    df = pd.DataFrame(all_results[minutes][mult])
                    profit_count = (df['Outcome'] == 'PROFIT').sum()
                    loss_count = (df['Outcome'] == 'LOSS').sum()
                    total_outcome = df['OutcomePoints'].sum()
                    avg_outcome = df['OutcomePoints'].mean()
                    win_rate = profit_count / (profit_count + loss_count) * 100
                    avg_atrtp = df['ATRTP'].mean()
                    
                    summary_rows.append({
                        'Config': f'{minutes}min_{mult}x',
                        'TimeWindow': minutes,
                        'Multiplier': mult,
                        'ATRTP_Avg': round(avg_atrtp, 0),
                        'ProfitCount': profit_count,
                        'LossCount': loss_count,
                        'WinRate': f'{win_rate:.1f}%',
                        'TotalOutcomePts': total_outcome,
                        'AvgOutcomePts': round(avg_outcome, 1)
                    })
        
        summary_df = pd.DataFrame(summary_rows)
        
        # Find best configuration
        best_idx = summary_df['TotalOutcomePts'].idxmax()
        best_row = summary_df.iloc[best_idx]
        
        print(f"\nBest Configuration: {best_row['Config']}")
        print(f"  Total Outcome: {best_row['TotalOutcomePts']:,} points")
        print(f"  Win Rate: {best_row['WinRate']}")
        print(f"  Avg per Trade: {best_row['AvgOutcomePts']} points")
        
        # Create Excel file
        output_file = 'data/Comprehensive_Analysis_20260320.xlsx'
        print(f"\nCreating Excel file: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # RESULT sheet with highlighting
            summary_df.to_excel(writer, sheet_name='RESULT', index=False)
            print("  -> RESULT sheet written")
            
            # Individual combination sheets
            sheet_count = 0
            for minutes in time_windows:
                for mult in multipliers:
                    if all_results[minutes][mult]:
                        df = pd.DataFrame(all_results[minutes][mult])
                        
                        # Reorder columns
                        mfe_col = f'MFE{minutes:02d}Price'
                        mfe_points_col = f'MFE{minutes:02d}Points'
                        mae_col = f'MAE{minutes:02d}Price'
                        mae_points_col = f'MAE{minutes:02d}Points'
                        
                        column_order = [
                            'Ticket', 'Magic Number', 'Type', 'TimeOpen', 'PriceOpen',
                            'TimeClose', 'PriceClose', 'ActualPoints', 'ATROpen', 
                            'TimeWindow', 'Multiplier', 'ATRTP',
                            mfe_col, mfe_points_col, mae_col, mae_points_col,
                            'Outcome', 'OutcomePoints'
                        ]
                        df = df[column_order]
                        
                        sheet_name = f'{minutes}min_{mult}x'.replace('.', '_')
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        sheet_count += 1
            
            print(f"  -> {sheet_count} combination sheets written")
        
        mt5.shutdown()
        
        print("\n" + "=" * 90)
        print("EXCEL FILE CREATED SUCCESSFULLY")
        print("=" * 90)
        print(f"File: {output_file}")
        print(f"Total sheets: {sheet_count + 1} (RESULT + {sheet_count} combinations)")
        
        print("\n" + "=" * 90)
        print("RESULT SUMMARY - All 54 Configurations")
        print("=" * 90)
        print(summary_df.to_string(index=False))
        
        print("\n" + "=" * 90)
        print("TOP 10 CONFIGURATIONS (by Total Outcome)")
        print("=" * 90)
        top10 = summary_df.nlargest(10, 'TotalOutcomePts')[['Config', 'WinRate', 'TotalOutcomePts', 'AvgOutcomePts']]
        print(top10.to_string(index=False))
        
        print("\n" + "=" * 90)
        print("OPTIMAL CONFIGURATION IDENTIFIED")
        print("=" * 90)
        print(f"Configuration: {best_row['Config']}")
        print(f"  Time Window: {best_row['TimeWindow']} minutes")
        print(f"  ATR Multiplier: {best_row['Multiplier']}x")
        print(f"  Avg TP Target: {best_row['ATRTP_Avg']:.0f} points")
        print(f"  Win Rate: {best_row['WinRate']}")
        print(f"  Total Outcome: {best_row['TotalOutcomePts']:,} points")
        print(f"  Avg per Trade: {best_row['AvgOutcomePts']:.1f} points")
        
    except Exception as e:
        mt5.shutdown()
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default='2026-03-20', help='Date to analyze (YYYY-MM-DD)')
    args = parser.parse_args()
    main(args.date)
