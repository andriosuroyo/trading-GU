"""
Extended Multi-Time Window Analysis for GU Strategy
1min to 30min with RESULT summary sheet at front
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import json

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

def analyze_position_time_window(position, minutes_window, cached_atr=None):
    """Analyze position for a specific time window (1-30 min)"""
    pos_id = position['pos_id']
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    magic = position['magic']
    
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    
    window_end = open_time + timedelta(minutes=minutes_window)
    
    # Use cached ATR if available
    if cached_atr is not None:
        atr_value = cached_atr
    else:
        atr_value = get_atr_m1_60('XAUUSDp', open_time)
        if atr_value is None:
            atr_value = 0
    
    atr_tp_points = round(atr_value * 0.5 * 100)
    
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_end + timedelta(seconds=5)
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None, atr_value
    
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_end)]
    if window_ticks.empty:
        return None, atr_value
    
    if direction == 'BUY':
        mfe_price = window_ticks['ask'].max()
        mfe_points = round(abs((mfe_price - entry_price) * 100))
        mae_price = window_ticks['bid'].min()
        mae_points = round(abs((entry_price - mae_price) * 100))
        actual_points = round((exit_price - entry_price) * 100)
        ticks_at_end = window_ticks[window_ticks['time'] <= window_end]
        price_at_end = ticks_at_end['bid'].iloc[-1] if not ticks_at_end.empty else exit_price
        points_at_end = round((price_at_end - entry_price) * 100)
    else:
        mfe_price = window_ticks['bid'].min()
        mfe_points = round(abs((entry_price - mfe_price) * 100))
        mae_price = window_ticks['ask'].max()
        mae_points = round(abs((mae_price - entry_price) * 100))
        actual_points = round((entry_price - exit_price) * 100)
        ticks_at_end = window_ticks[window_ticks['time'] <= window_end]
        price_at_end = ticks_at_end['ask'].iloc[-1] if not ticks_at_end.empty else exit_price
        points_at_end = round((entry_price - price_at_end) * 100)
    
    mfe_points = abs(mfe_points)
    mae_points = abs(mae_points)
    
    if mfe_points > atr_tp_points:
        outcome = 'PROFIT'
        outcome_points = atr_tp_points
    else:
        outcome = 'LOSS'
        outcome_points = points_at_end
    
    return {
        'Ticket': f'P{pos_id}',
        'Magic Number': magic,
        'Type': direction,
        'TimeOpen': open_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceOpen': entry_price,
        'TimeClose': close_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceClose': exit_price,
        'ActualPoints': actual_points,
        'ATROpen': round(atr_value, 2),
        'ATRTP': atr_tp_points,
        f'MFE{minutes_window:02d}Price': round(mfe_price, 2),
        f'MFE{minutes_window:02d}Points': mfe_points,
        f'MAE{minutes_window:02d}Price': round(mae_price, 2),
        f'MAE{minutes_window:02d}Points': mae_points,
        'Outcome': outcome,
        'OutcomePoints': outcome_points
    }, atr_value

def main():
    print("=" * 80)
    print("EXTENDED MULTI-TIME WINDOW ANALYSIS - 1min to 30min")
    print("Finding optimal cutoff time for GU Strategy")
    print("=" * 80)
    
    with open('data/gu_positions_vantage.json', 'r') as f:
        data = json.load(f)
    
    target_positions = [p for p in data['closed_positions'] 
                       if str(p['magic']) in ['20', '30'] and '2026-03-20' in p['open_time']]
    
    print(f"Found {len(target_positions)} Magic 20/30 positions on March 20")
    
    if not connect_blackbull():
        print("Failed to connect to BlackBull")
        return
    
    try:
        output_file = 'data/Analysis_20260320.xlsx'
        
        # First pass: collect all data and build summary
        all_results = {}
        summary_data = []
        
        for minutes in range(1, 31):
            print(f"\nProcessing {minutes} minute window...")
            
            results = []
            atr_cache = {}  # Cache ATR by position ID
            
            for i, pos in enumerate(target_positions):
                pos_id = pos['pos_id']
                
                # Use cached ATR if available
                cached_atr = atr_cache.get(pos_id)
                
                result, atr_val = analyze_position_time_window(pos, minutes, cached_atr)
                
                # Cache ATR for future use
                if pos_id not in atr_cache and atr_val is not None:
                    atr_cache[pos_id] = atr_val
                
                if result:
                    results.append(result)
            
            if results:
                df = pd.DataFrame(results)
                all_results[minutes] = df
                
                # Calculate summary stats
                profit_count = (df['Outcome'] == 'PROFIT').sum()
                loss_count = (df['Outcome'] == 'LOSS').sum()
                total_outcome = df['OutcomePoints'].sum()
                avg_outcome = df['OutcomePoints'].mean()
                
                mfe_col = f'MFE{minutes:02d}Points'
                mae_col = f'MAE{minutes:02d}Points'
                avg_mfe = df[mfe_col].mean()
                avg_mae = df[mae_col].mean()
                
                summary_data.append({
                    'TimeWindow': f'{minutes}min',
                    'Profit': profit_count,
                    'Loss': loss_count,
                    'WinRate': f"{profit_count/(profit_count+loss_count)*100:.1f}%",
                    'TotalOutcomePts': total_outcome,
                    'AvgOutcomePts': round(avg_outcome, 1),
                    'AvgMFE': round(avg_mfe, 0),
                    'AvgMAE': round(avg_mae, 0)
                })
                
                print(f"  {minutes}min: PROFIT={profit_count}, LOSS={loss_count}, Total={total_outcome:+,}")
        
        # Create Excel with RESULT sheet first
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write RESULT summary sheet first
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='RESULT', index=False)
            
            # Write individual minute sheets
            for minutes in range(1, 31):
                if minutes in all_results:
                    df = all_results[minutes]
                    
                    mfe_col = f'MFE{minutes:02d}Price'
                    mfe_points_col = f'MFE{minutes:02d}Points'
                    mae_col = f'MAE{minutes:02d}Price'
                    mae_points_col = f'MAE{minutes:02d}Points'
                    
                    column_order = [
                        'Ticket', 'Magic Number', 'Type', 'TimeOpen', 'PriceOpen',
                        'TimeClose', 'PriceClose', 'ActualPoints', 'ATROpen', 'ATRTP',
                        mfe_col, mfe_points_col, mae_col, mae_points_col,
                        'Outcome', 'OutcomePoints'
                    ]
                    df = df[column_order]
                    
                    sheet_name = f'{minutes}min'
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        mt5.shutdown()
        
        # Print final summary
        print("\n" + "=" * 80)
        print(f"EXCEL FILE CREATED: {output_file}")
        print("=" * 80)
        
        print("\n" + "=" * 80)
        print("COMPLETE SUMMARY - All Time Windows")
        print("=" * 80)
        print(summary_df.to_string(index=False))
        
        # Find best performers
        best_total = summary_df.loc[summary_df['TotalOutcomePts'].idxmax()]
        best_avg = summary_df.loc[summary_df['AvgOutcomePts'].idxmax()]
        best_winrate = summary_df.loc[summary_df['WinRate'].apply(lambda x: float(x.replace('%',''))).idxmax()]
        
        print("\n" + "=" * 80)
        print("OPTIMAL CUTOFF FINDINGS")
        print("=" * 80)
        print(f"Best Total Outcome: {best_total['TimeWindow']} with {best_total['TotalOutcomePts']:,} points")
        print(f"Best Avg per Trade: {best_avg['TimeWindow']} with {best_avg['AvgOutcomePts']:.1f} points")
        print(f"Best Win Rate: {best_winrate['TimeWindow']} with {best_winrate['WinRate']}")
        
        # Highlight 15min vs extended
        min15 = summary_df[summary_df['TimeWindow'] == '15min'].iloc[0]
        min30 = summary_df[summary_df['TimeWindow'] == '30min'].iloc[0]
        
        print("\n" + "=" * 80)
        print("15MIN vs 30MIN COMPARISON")
        print("=" * 80)
        print(f"15min: Total={min15['TotalOutcomePts']:,}, WinRate={min15['WinRate']}, Avg={min15['AvgOutcomePts']}")
        print(f"30min: Total={min30['TotalOutcomePts']:,}, WinRate={min30['WinRate']}, Avg={min30['AvgOutcomePts']}")
        
        if min30['TotalOutcomePts'] > min15['TotalOutcomePts']:
            print(f"\n15min was NOT an outlier - 30min shows even better performance (+{min30['TotalOutcomePts'] - min15['TotalOutcomePts']:,} points)")
        else:
            print(f"\n15min may have been a local peak - 30min shows {min30['TotalOutcomePts'] - min15['TotalOutcomePts']:,} point difference")
        
    except Exception as e:
        mt5.shutdown()
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
