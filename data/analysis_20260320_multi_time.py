"""
Multi-Time Window Analysis for GU Strategy
Creates Excel workbook with 15 tabs (1min to 15min) to find optimal cutoff time
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

def analyze_position_time_window(position, minutes_window):
    """Analyze position for a specific time window (1-15 min)"""
    pos_id = position['pos_id']
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    magic = position['magic']
    
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    
    # Time window end
    window_end = open_time + timedelta(minutes=minutes_window)
    
    # Fetch ATR at open (only once, reuse)
    atr_value = get_atr_m1_60('XAUUSDp', open_time)
    if atr_value is None:
        atr_value = 0
    atr_tp_points = round(atr_value * 0.5 * 100)
    
    # Fetch tick data for the window
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_end + timedelta(seconds=5)
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None
    
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_end)]
    if window_ticks.empty:
        return None
    
    # Calculate MFE and MAE for this time window
    if direction == 'BUY':
        mfe_price = window_ticks['ask'].max()
        mfe_points = round(abs((mfe_price - entry_price) * 100))
        mae_price = window_ticks['bid'].min()
        mae_points = round(abs((entry_price - mae_price) * 100))
        actual_points = round((exit_price - entry_price) * 100)
        # Price at window end
        ticks_at_end = window_ticks[window_ticks['time'] <= window_end]
        price_at_end = ticks_at_end['bid'].iloc[-1] if not ticks_at_end.empty else exit_price
        points_at_end = round((price_at_end - entry_price) * 100)
    else:  # SELL
        mfe_price = window_ticks['bid'].min()
        mfe_points = round(abs((entry_price - mfe_price) * 100))
        mae_price = window_ticks['ask'].max()
        mae_points = round(abs((mae_price - entry_price) * 100))
        actual_points = round((entry_price - exit_price) * 100)
        # Price at window end
        ticks_at_end = window_ticks[window_ticks['time'] <= window_end]
        price_at_end = ticks_at_end['ask'].iloc[-1] if not ticks_at_end.empty else exit_price
        points_at_end = round((entry_price - price_at_end) * 100)
    
    # Ensure positive
    mfe_points = abs(mfe_points)
    mae_points = abs(mae_points)
    
    # Outcome based on MFE vs ATRTP
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
    print("MULTI-TIME WINDOW ANALYSIS - 1min to 15min")
    print("Finding optimal cutoff time for GU Strategy")
    print("=" * 80)
    
    # Load positions
    with open('data/gu_positions_vantage.json', 'r') as f:
        data = json.load(f)
    
    target_positions = [p for p in data['closed_positions'] 
                       if str(p['magic']) in ['20', '30'] and '2026-03-20' in p['open_time']]
    
    print(f"Found {len(target_positions)} Magic 20/30 positions on March 20")
    
    if not connect_blackbull():
        print("Failed to connect to BlackBull")
        return
    
    try:
        # Create Excel writer
        output_file = 'data/Analysis_20260320.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # Process each time window (1-15 minutes)
            for minutes in range(1, 16):
                print(f"\nProcessing {minutes} minute window...")
                
                results = []
                for i, pos in enumerate(target_positions):
                    if i % 20 == 0:
                        print(f"  {i}/{len(target_positions)} positions...")
                    
                    result = analyze_position_time_window(pos, minutes)
                    if result:
                        results.append(result)
                
                if results:
                    df = pd.DataFrame(results)
                    
                    # Column order
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
                    
                    # Sheet name
                    sheet_name = f'{minutes}min'
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Summary stats for this time window
                    profit_count = (df['Outcome'] == 'PROFIT').sum()
                    loss_count = (df['Outcome'] == 'LOSS').sum()
                    total_outcome_points = df['OutcomePoints'].sum()
                    avg_mfe = df[mfe_points_col].mean()
                    avg_mae = df[mae_points_col].mean()
                    
                    print(f"  Sheet '{sheet_name}' created: {len(df)} rows")
                    print(f"    PROFIT: {profit_count}, LOSS: {loss_count}")
                    print(f"    Total OutcomePoints: {total_outcome_points:+,}")
                    print(f"    Avg MFE: {avg_mfe:.0f}, Avg MAE: {avg_mae:.0f}")
        
        mt5.shutdown()
        
        print("\n" + "=" * 80)
        print(f"EXCEL FILE CREATED: {output_file}")
        print("=" * 80)
        print("\nSheets: 1min, 2min, 3min, 4min, 5min, 6min, 7min, 8min, 9min,")
        print("        10min, 11min, 12min, 13min, 14min, 15min")
        print("\nCompare 'OutcomePoints' totals across sheets to find optimal cutoff time.")
        
    except Exception as e:
        mt5.shutdown()
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
