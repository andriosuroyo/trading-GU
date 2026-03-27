"""
Corrected MAE/MFE Analysis with proper point calculations
1 point = 0.01 price movement for XAUUSD
Includes ATR(60) M1 at position open
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
    """Connect to BlackBull for tick and bar data"""
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_BLACKBULL")
    if not mt5.initialize(path=terminal_path):
        print(f"BlackBull init failed: {mt5.last_error()}")
        return False
    return True

def get_atr_m1_60(symbol, target_time):
    """Get ATR(60) value from M1 bars at target time"""
    # Fetch 120 M1 bars ending at target_time to ensure we have enough data for ATR(60)
    from_time = target_time - timedelta(hours=2)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, target_time)
    
    if rates is None or len(rates) < 60:
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    
    # Calculate ATR(60)
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr_60'] = df['tr'].rolling(window=60).mean()
    
    # Find the ATR value at or just before target_time
    df_before = df[df['time'] <= target_time]
    if df_before.empty:
        return None
    
    atr_value = df_before['atr_60'].iloc[-1]
    return atr_value

def get_tick_data_blackbull(from_time, to_time):
    """Get tick data from BlackBull"""
    ticks = mt5.copy_ticks_range('XAUUSDp', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def calculate_mae_mfe_points(tick_df, direction, entry_price, exit_time):
    """
    Calculate MAE and MFE in POINTS (not price units)
    1 point = 0.01 price movement for XAUUSD
    
    For BUY:
    - MFE = (max_ask - entry_price) * 100
    - MAE = (entry_price - min_bid) * 100
    
    For SELL:
    - MFE = (entry_price - min_bid) * 100
    - MAE = (max_ask - entry_price) * 100
    """
    if direction == "BUY":
        # MFE: How high did ask go above entry?
        max_ask = tick_df['ask'].max()
        mfe_points = (max_ask - entry_price) * 100
        
        # MAE: How low did bid go below entry?
        min_bid = tick_df['bid'].min()
        mae_points = (entry_price - min_bid) * 100
        
    else:  # SELL
        # MFE: How low did bid go below entry?
        min_bid = tick_df['bid'].min()
        mfe_points = (entry_price - min_bid) * 100
        
        # MAE: How high did ask go above entry?
        max_ask = tick_df['ask'].max()
        mae_points = (max_ask - entry_price) * 100
    
    return {
        'mfe_points': mfe_points,
        'mae_points': mae_points,
        'max_ask': max_ask if direction == "BUY" else None,
        'min_bid': min_bid if direction == "SELL" else None,
    }

def analyze_position(position):
    """Analyze a single position with corrected point calculations"""
    pos_id = position['pos_id']
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    magic = position['magic']
    
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    
    # 15-minute window
    window_end = open_time + timedelta(minutes=15)
    
    # Fetch ATR at open
    atr_value = get_atr_m1_60('XAUUSDp', open_time)
    if atr_value is None:
        atr_value = 0
    
    # ATR TP = ATR * 0.5 * 100 (convert to points)
    # ATR is in price units (e.g., 4.00), multiply by 100 to get points
    atr_tp_points = (atr_value * 0.5) * 100
    
    # Fetch tick data for 15-minute window
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_end + timedelta(seconds=5)
    
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None
    
    # Filter to 15-minute window
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_end)]
    
    if window_ticks.empty:
        return None
    
    # Calculate MAE/MFE in points
    mae_mfe = calculate_mae_mfe_points(window_ticks, direction, entry_price, close_time)
    
    # Determine outcome
    # Profit if MFE15 > ATRTP (max favorable exceeded target)
    # Loss if MFE15 < ATRTP (didn't reach target)
    mfe15 = mae_mfe['mfe_points']
    mae15 = mae_mfe['mae_points']
    
    if mfe15 > atr_tp_points:
        outcome = "PROFIT"
    else:
        outcome = "LOSS"
    
    # Calculate actual P/L in points
    if direction == "BUY":
        actual_points = (exit_price - entry_price) * 100
    else:
        actual_points = (entry_price - exit_price) * 100
    
    return {
        'TimeOpen': open_time.strftime('%Y-%m-%d %H:%M:%S'),
        'Ticket': pos_id,
        'Type': direction,
        'PriceOpen': entry_price,
        'TimeClose': close_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceClose': exit_price,
        'ATROpen': round(atr_value, 2),
        'ATRTP': round(atr_tp_points, 1),
        'MFE15': round(mfe15, 1),
        'MAE15': round(mae15, 1),
        'Outcome': outcome,
        'Magic': magic,
        'ActualPoints': round(actual_points, 1)
    }

def main():
    print("=" * 80)
    print("MAE/MFE CORRECTED ANALYSIS - March 20, 2026")
    print("Points = Price difference × 100 (XAUUSD standard)")
    print("=" * 80)
    
    # Load positions
    with open('data/gu_positions_vantage.json', 'r') as f:
        data = json.load(f)
    
    # Filter Magic 20 & 30 positions from March 20
    target_positions = []
    for p in data['closed_positions']:
        magic = str(p['magic'])
        if magic in ['20', '30'] and '2026-03-20' in p['open_time']:
            target_positions.append(p)
    
    print(f"Found {len(target_positions)} Magic 20/30 positions on March 20")
    
    if not target_positions:
        return
    
    if not connect_blackbull():
        print("Failed to connect to BlackBull")
        return
    
    try:
        results = []
        
        for i, pos in enumerate(target_positions):
            print(f"\n[{i+1}/{len(target_positions)}] Position {pos['pos_id']} - {pos['direction']} @ {pos['open_time'][11:19]}")
            
            result = analyze_position(pos)
            
            if result:
                results.append(result)
                print(f"  ATR: {result['ATROpen']:.2f} (${result['ATROpen']:.2f}) -> ATRTP: {result['ATRTP']:.1f} points")
                print(f"  MFE15: {result['MFE15']:.1f} points | MAE15: {result['MAE15']:.1f} points")
                print(f"  Outcome: {result['Outcome']}")
            else:
                print(f"  ERROR: Could not analyze")
        
        # Create DataFrame
        if results:
            df = pd.DataFrame(results)
            
            # Reorder columns as requested
            column_order = ['TimeOpen', 'Ticket', 'Type', 'PriceOpen', 'TimeClose', 'PriceClose',
                          'ATROpen', 'ATRTP', 'MFE15', 'MAE15', 'Outcome', 'Magic', 'ActualPoints']
            df = df[column_order]
            
            # Save to CSV
            output_file = 'data/mae_mfe_corrected_march20.csv'
            df.to_csv(output_file, index=False)
            
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Positions analyzed: {len(df)}")
            print(f"\nOutcome Distribution:")
            print(df['Outcome'].value_counts())
            print(f"\nBy Magic Number:")
            print(df.groupby(['Magic', 'Outcome']).size().unstack(fill_value=0))
            
            print(f"\nStatistics:")
            print(f"  Avg ATR: ${df['ATROpen'].mean():.2f}")
            print(f"  Avg ATRTP: {df['ATRTP'].mean():.1f} points")
            print(f"  Avg MFE15: {df['MFE15'].mean():.1f} points")
            print(f"  Avg MAE15: {df['MAE15'].mean():.1f} points")
            print(f"  Win Rate (MFE15 > ATRTP): {(df['Outcome']=='PROFIT').mean()*100:.1f}%")
            
            # Show sample rows
            print("\n" + "=" * 80)
            print("SAMPLE OUTPUT (First 10 rows)")
            print("=" * 80)
            print(df.head(10).to_string(index=False))
            
            print(f"\n\nCSV saved: {output_file}")
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
