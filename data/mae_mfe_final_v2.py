"""
Final MAE/MFE Analysis - Exact Format Specification
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import os

def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def connect_blackbull():
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_BLACKBULL")
    if not mt5.initialize(path=terminal_path):
        print(f"BlackBull init failed: {mt5.last_error()}")
        return False
    return True

def get_atr_m1_60(symbol, target_time):
    """Get ATR(60) value from M1 bars at target time"""
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
    """Get tick data from BlackBull"""
    ticks = mt5.copy_ticks_range('XAUUSDp', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def analyze_position(position):
    """Analyze position with exact format requirements"""
    pos_id = position['pos_id']
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    magic = position['magic']
    
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    
    # FULL 15-minute window from open
    window_15min_end = open_time + timedelta(minutes=15)
    
    # Fetch ATR at open
    atr_value = get_atr_m1_60('XAUUSDp', open_time)
    if atr_value is None:
        atr_value = 0
    
    # ATR TP in points
    atr_tp_points = round(atr_value * 0.5 * 100)
    
    # Fetch tick data for FULL 15-minute window
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_15min_end + timedelta(seconds=5)
    
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None
    
    # Filter to EXACTLY 15-minute window
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_15min_end)]
    
    if window_ticks.empty:
        return None
    
    # Find MFE and MAE prices and calculate points
    if direction == "BUY":
        # MFE: max ask price
        mfe15_price = window_ticks['ask'].max()
        mfe15_points = round((mfe15_price - entry_price) * 100)
        
        # MAE: min bid price
        mae15_price = window_ticks['bid'].min()
        mae15_points = round((entry_price - mae15_price) * 100)
        
        # Actual points captured
        actual_points = round((exit_price - entry_price) * 100)
        
        # 15min close price (bid at 15min mark or last available)
        ticks_at_15min = window_ticks[window_ticks['time'] <= window_15min_end]
        if not ticks_at_15min.empty:
            price_15min = ticks_at_15min['bid'].iloc[-1]
        else:
            price_15min = exit_price
        points_15min_close = round((price_15min - entry_price) * 100)
        
    else:  # SELL
        # MFE: min bid price
        mfe15_price = window_ticks['bid'].min()
        mfe15_points = round((entry_price - mfe15_price) * 100)
        
        # MAE: max ask price
        mae15_price = window_ticks['ask'].max()
        mae15_points = round((mae15_price - entry_price) * 100)
        
        # Actual points captured
        actual_points = round((entry_price - exit_price) * 100)
        
        # 15min close price (ask at 15min mark or last available)
        ticks_at_15min = window_ticks[window_ticks['time'] <= window_15min_end]
        if not ticks_at_15min.empty:
            price_15min = ticks_at_15min['ask'].iloc[-1]
        else:
            price_15min = exit_price
        points_15min_close = round((entry_price - price_15min) * 100)
    
    # Ensure MFE and MAE points are positive
    mfe15_points = abs(mfe15_points)
    mae15_points = abs(mae15_points)
    
    # Determine outcome
    if mfe15_points > atr_tp_points:
        outcome = "PROFIT"
        outcome_points = atr_tp_points
    else:
        outcome = "LOSS"
        outcome_points = points_15min_close
    
    return {
        'Ticket': f"P{pos_id}",
        'Magic Number': magic,
        'Type': direction,
        'TimeOpen': open_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceOpen': entry_price,
        'TimeClose': close_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceClose': exit_price,
        'ActualPoints': actual_points,
        'ATROpen': round(atr_value, 2),
        'ATRTP': atr_tp_points,
        'MFE15Price': round(mfe15_price, 2),
        'MFE15Points': mfe15_points,
        'MAE15Price': round(mae15_price, 2),
        'MAE15Points': mae15_points,
        'Outcome': outcome,
        'OutcomePoints': outcome_points
    }

def main():
    print("=" * 80)
    print("MAE/MFE FINAL ANALYSIS - Exact Format")
    print("=" * 80)
    
    with open('data/gu_positions_vantage.json', 'r') as f:
        data = json.load(f)
    
    target_positions = []
    for p in data['closed_positions']:
        magic = str(p['magic'])
        if magic in ['20', '30'] and '2026-03-20' in p['open_time']:
            target_positions.append(p)
    
    print(f"Found {len(target_positions)} Magic 20/30 positions on March 20")
    
    if not target_positions:
        return
    
    if not connect_blackbull():
        return
    
    try:
        results = []
        
        for i, pos in enumerate(target_positions):
            result = analyze_position(pos)
            if result:
                results.append(result)
        
        if results:
            df = pd.DataFrame(results)
            
            # Exact column order as requested
            column_order = [
                'Ticket', 'Magic Number', 'Type', 'TimeOpen', 'PriceOpen',
                'TimeClose', 'PriceClose', 'ActualPoints', 'ATROpen', 'ATRTP',
                'MFE15Price', 'MFE15Points', 'MAE15Price', 'MAE15Points',
                'Outcome', 'OutcomePoints'
            ]
            df = df[column_order]
            
            output_file = 'data/mae_mfe_final_march20.csv'
            df.to_csv(output_file, index=False)
            
            print(f"\nCSV saved: {output_file}")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")
            
            print("\n" + "=" * 80)
            print("SAMPLE (First 5 rows)")
            print("=" * 80)
            print(df.head(5).to_string(index=False))
            
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Total: {len(df)} positions")
            print(f"PROFIT: {(df['Outcome']=='PROFIT').sum()}")
            print(f"LOSS: {(df['Outcome']=='LOSS').sum()}")
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
