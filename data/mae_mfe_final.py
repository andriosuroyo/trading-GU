"""
Final MAE/MFE Analysis - Clean Format
- Full 15-minute window regardless of close time
- All points in proper units (no factor of 100 issues)
- Positive values only for MAE/MFE columns
- Added ATR and Outcome columns
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
    
    # Calculate ATR(60)
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

def analyze_position_full_15min(position):
    """Analyze position with FULL 15-minute window (not truncated by close)"""
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
    
    # ATR TP in points (ATR * 0.5 * 100)
    atr_tp_points = round(atr_value * 0.5 * 100)
    
    # Fetch tick data for FULL 15-minute window
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_15min_end + timedelta(seconds=5)
    
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None
    
    # Filter to EXACTLY 15-minute window (not truncated by close time)
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_15min_end)]
    
    if window_ticks.empty:
        return None
    
    # Calculate MFE15 and MAE15 in points (ALWAYS POSITIVE)
    if direction == "BUY":
        # MFE: How much did ask go above entry (in points)
        max_ask = window_ticks['ask'].max()
        mfe15 = round((max_ask - entry_price) * 100)
        
        # MAE: How much did bid go below entry (in points)
        min_bid = window_ticks['bid'].min()
        mae15 = round((entry_price - min_bid) * 100)
        
        # Actual captured points
        actual_points = round((exit_price - entry_price) * 100)
        
    else:  # SELL
        # MFE: How much did bid go below entry (in points)
        min_bid = window_ticks['bid'].min()
        mfe15 = round((entry_price - min_bid) * 100)
        
        # MAE: How much did ask go above entry (in points)
        max_ask = window_ticks['ask'].max()
        mae15 = round((max_ask - entry_price) * 100)
        
        # Actual captured points
        actual_points = round((entry_price - exit_price) * 100)
    
    # Ensure MFE15 and MAE15 are always positive
    mfe15 = abs(mfe15)
    mae15 = abs(mae15)
    
    # Determine outcome based on whether MFE15 exceeded ATRTP
    if mfe15 > atr_tp_points:
        outcome = "PROFIT"
    else:
        outcome = "LOSS"
    
    return {
        'TimeOpen': open_time.strftime('%Y-%m-%d %H:%M:%S'),
        'Ticket': f"P{pos_id}",  # Add P prefix to prevent scientific notation
        'Type': direction,
        'PriceOpen': entry_price,
        'TimeClose': close_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceClose': exit_price,
        'ATROpen': round(atr_value, 2),
        'ATRTP': atr_tp_points,
        'MFE15': mfe15,  # Always positive, rounded
        'MAE15': mae15,  # Always positive, rounded
        'Outcome': outcome,
        'Magic': magic,
        'ActualPoints': actual_points,
        'Window15End': window_15min_end.strftime('%Y-%m-%d %H:%M:%S')  # Show the full 15-min window end
    }

def main():
    print("=" * 80)
    print("MAE/MFE FINAL ANALYSIS - Clean Format")
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
            print(f"[{i+1}/{len(target_positions)}] Position P{pos['pos_id']} - {pos['direction']} @ {pos['open_time'][11:19]}")
            
            result = analyze_position_full_15min(pos)
            
            if result:
                results.append(result)
            else:
                print(f"  ERROR: Could not analyze")
        
        # Create DataFrame with exact column order requested
        if results:
            df = pd.DataFrame(results)
            
            # Column order as requested
            column_order = ['TimeOpen', 'Ticket', 'Type', 'PriceOpen', 'TimeClose', 'PriceClose',
                          'ATROpen', 'ATRTP', 'MFE15', 'MAE15', 'Outcome', 'Magic', 'ActualPoints']
            df = df[column_order]
            
            # Save to CSV
            output_file = 'data/mae_mfe_final_march20.csv'
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
            print(f"  Avg ATRTP: {df['ATRTP'].mean():.0f} points")
            print(f"  Avg MFE15: {df['MFE15'].mean():.0f} points")
            print(f"  Avg MAE15: {df['MAE15'].mean():.0f} points")
            print(f"  Win Rate (MFE15 > ATRTP): {(df['Outcome']=='PROFIT').mean()*100:.1f}%")
            
            # Verify MFE15 and MAE15 are always positive
            print(f"\nData Validation:")
            print(f"  MFE15 all positive: {(df['MFE15'] >= 0).all()}")
            print(f"  MAE15 all positive: {(df['MAE15'] >= 0).all()}")
            print(f"  MFE15 min: {df['MFE15'].min()}, max: {df['MFE15'].max()}")
            print(f"  MAE15 min: {df['MAE15'].min()}, max: {df['MAE15'].max()}")
            
            # Show sample
            print("\n" + "=" * 80)
            print("SAMPLE (First 10 rows)")
            print("=" * 80)
            print(df.head(10).to_string(index=False))
            
            print(f"\n\nCSV saved: {output_file}")
            print(f"Columns: {list(df.columns)}")
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
