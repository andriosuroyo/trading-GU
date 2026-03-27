"""
Create complete Analysis_20260320.xlsx with:
- RESULT sheet (at front) with 5 columns
- 30 individual minute sheets (1min-30min)
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

def analyze_position(position, minutes_window, cached_atr):
    """Analyze a single position for a specific time window"""
    pos_id = position['pos_id']
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    magic = position['magic']
    
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    window_end = open_time + timedelta(minutes=minutes_window)
    
    # Use cached ATR
    atr_value = cached_atr if cached_atr is not None else 0
    atr_tp_points = round(atr_value * 0.5 * 100)
    
    # Fetch tick data
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_end + timedelta(seconds=5)
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None
    
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_end)]
    if window_ticks.empty:
        return None
    
    # Calculate MFE/MAE
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
    }

def main():
    print("=" * 80)
    print("CREATING COMPLETE ANALYSIS_20260320.XLSX")
    print("31 sheets: RESULT + 1min-30min")
    print("=" * 80)
    
    # Load positions
    with open('data/gu_positions_vantage.json', 'r') as f:
        data = json.load(f)
    
    target_positions = [p for p in data['closed_positions'] 
                       if str(p['magic']) in ['20', '30'] and '2026-03-20' in p['open_time']]
    
    print(f"Processing {len(target_positions)} positions...")
    
    if not connect_blackbull():
        print("Failed to connect")
        return
    
    try:
        # Pre-fetch ATR for all positions (to avoid repeated calculations)
        print("Fetching ATR values...")
        atr_cache = {}
        for pos in target_positions:
            pos_id = pos['pos_id']
            open_time = datetime.fromisoformat(pos['open_time'])
            atr_val = get_atr_m1_60('XAUUSDp', open_time)
            atr_cache[pos_id] = atr_val if atr_val is not None else 0
        
        # Collect all data for all time windows
        all_data = {}
        summary_data = []
        
        for minutes in range(1, 31):
            print(f"Processing {minutes}min window...")
            results = []
            
            for pos in target_positions:
                pos_id = pos['pos_id']
                cached_atr = atr_cache.get(pos_id, 0)
                result = analyze_position(pos, minutes, cached_atr)
                if result:
                    results.append(result)
            
            if results:
                df = pd.DataFrame(results)
                all_data[minutes] = df
                
                # Calculate summary
                profit_count = (df['Outcome'] == 'PROFIT').sum()
                loss_count = (df['Outcome'] == 'LOSS').sum()
                total_outcome = df['OutcomePoints'].sum()
                win_rate = f"{profit_count/(profit_count+loss_count)*100:.1f}%"
                
                summary_data.append({
                    'TimeWindow': f'{minutes}min',
                    'ProfitCount': profit_count,
                    'LossCount': loss_count,
                    'WinRate': win_rate,
                    'TotalOutcomePoints': total_outcome
                })
                
                print(f"  -> {profit_count} PROFIT, {loss_count} LOSS, Total={total_outcome:+,}")
        
        # Create Excel file
        output_file = 'data/Analysis_20260320.xlsx'
        print(f"\nCreating Excel file: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 1. Write RESULT sheet first (5 columns only)
            result_df = pd.DataFrame(summary_data)
            result_df.to_excel(writer, sheet_name='RESULT', index=False)
            print("  -> RESULT sheet written")
            
            # 2. Write individual minute sheets
            for minutes in range(1, 31):
                if minutes in all_data:
                    df = all_data[minutes]
                    
                    # Reorder columns
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
            
            print(f"  -> 30 minute sheets written")
        
        mt5.shutdown()
        
        print("\n" + "=" * 80)
        print("EXCEL FILE CREATED SUCCESSFULLY")
        print("=" * 80)
        print(f"File: {output_file}")
        print(f"Sheets: 31 total (RESULT + 1min-30min)")
        print("\nRESULT sheet preview:")
        print(result_df.to_string(index=False))
        
    except Exception as e:
        mt5.shutdown()
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
