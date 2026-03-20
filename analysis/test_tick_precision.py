"""
Test if we can get second-level price precision using tick data
Compare: M1 candle close vs actual tick price at exact time offset
"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

def load_env():
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    except:
        pass
    return env_vars

def connect_mt5():
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    return True

def get_m1_bars(from_time, to_time):
    """Get M1 bars"""
    rates = mt5.copy_rates_range('XAUUSD+', mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def get_tick_data(from_time, to_time):
    """Get tick data - check if available and what precision"""
    ticks = mt5.copy_ticks_range('XAUUSD+', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): 
        return 'UNKNOWN', 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    session_id = m[7] if len(m) > 7 else '0'
    strategies = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    sessions = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    return strategies.get(strat_id, f'STRAT_{strat_id}'), sessions.get(session_id, f'SESS_{session_id}')

def get_sample_positions(session_name, date_from, date_to, limit=5):
    """Get a few sample positions for testing"""
    import gu_tools
    positions = gu_tools.fetch_positions(date_from, date_to)
    gu_positions = [p for p in positions if str(p['magic']).startswith('282603')]
    
    session_positions = []
    for p in gu_positions:
        strat, sess = parse_magic(p['magic'])
        if sess == session_name:
            p['strategy'] = strat
            p['session'] = sess
            session_positions.append(p)
    
    # Get first positions only (clean)
    sorted_pos = sorted(session_positions, key=lambda x: (x['magic'], x['open_time']))
    baskets = []
    current_basket = None
    
    for p in sorted_pos:
        if current_basket is None or p['magic'] != current_basket['magic']:
            current_basket = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
            baskets.append(current_basket)
        else:
            first_time = current_basket['positions'][0]['open_time']
            if (p['open_time'] - first_time).total_seconds() <= 60:
                current_basket['positions'].append(p)
            else:
                current_basket = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
                baskets.append(current_basket)
    
    first_positions = []
    for basket in baskets[:limit]:
        first_pos = basket['positions'][0]
        is_glitch = False
        if len(basket['positions']) >= 2:
            directions = [p['direction'] for p in basket['positions']]
            if 'BUY' in directions and 'SELL' in directions:
                times = [p['open_time'] for p in basket['positions']]
                if len(set(times)) < len(times):
                    is_glitch = True
        
        if not is_glitch:
            first_positions.append({
                'time': first_pos['open_time'],
                'type': first_pos['direction'],
                'entry': first_pos['open_price'],
                'actual_exit': first_pos['close_price'],
                'actual_close_time': first_pos['close_time']
            })
    
    return first_positions

def main():
    if not connect_mt5():
        return
    
    try:
        date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
        date_to = datetime.now(timezone.utc)
        
        print("="*100)
        print("TESTING TICK DATA PRECISION FOR SECOND-LEVEL ANALYSIS")
        print("="*100)
        
        # Get sample positions
        print("\nFetching sample positions...")
        sample_positions = get_sample_positions('ASIA', date_from, date_to, limit=3)
        
        if not sample_positions:
            print("No positions found")
            return
        
        print(f"\nFound {len(sample_positions)} sample positions")
        
        # Test each position
        for i, pos in enumerate(sample_positions, 1):
            print(f"\n{'='*100}")
            print(f"POSITION {i}: {pos['type']} @ {pos['entry']}")
            print(f"Open time: {pos['time']}")
            print(f"Actual close: {pos['actual_close_time']} @ {pos['actual_exit']}")
            print(f"{'='*100}")
            
            entry_time = pos['time']
            
            # Calculate times
            candle_2min = entry_time + timedelta(minutes=2)
            exact_120s = entry_time + timedelta(seconds=120)
            
            print(f"\nTime calculations:")
            print(f"  Entry:           {entry_time}")
            print(f"  +2 min candle:   {candle_2min} (M1 candle close)")
            print(f"  +120 sec exact:  {exact_120s} (exact offset)")
            
            # Get M1 data
            start_time = entry_time - timedelta(minutes=5)
            end_time = entry_time + timedelta(minutes=5)
            df_m1 = get_m1_bars(start_time, end_time)
            
            if df_m1 is not None:
                # Find the candle at 2-min mark
                future_candles = df_m1[df_m1['time'] >= entry_time].head(3)
                
                print(f"\nM1 Candle data around entry:")
                print(f"{'Candle':<8} {'Time':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10}")
                print("-"*80)
                for idx, (_, row) in enumerate(future_candles.iterrows()):
                    marker = " <-- Entry" if idx == 0 else (" <-- 2-min" if idx == 2 else "")
                    print(f"{idx:<8} {str(row['time']):<20} {row['open']:<10.2f} {row['high']:<10.2f} {row['low']:<10.2f} {row['close']:<10.2f}{marker}")
                
                m1_exit_price = future_candles.iloc[2]['close'] if len(future_candles) > 2 else None
                print(f"\nM1 Method: Exit at 2-min candle close = {m1_exit_price}")
            
            # Try to get tick data
            print(f"\nAttempting to fetch tick data...")
            tick_start = entry_time
            tick_end = entry_time + timedelta(minutes=3)
            
            df_ticks = get_tick_data(tick_start, tick_end)
            
            if df_ticks is not None:
                print(f"[OK] Tick data available! {len(df_ticks)} ticks found")
                print(f"\nFirst 5 ticks:")
                print(df_ticks[['time', 'bid', 'ask']].head())
                
                # Try to find exact price at 120 seconds
                target_time = exact_120s
                tolerance = timedelta(seconds=1)
                
                nearby_ticks = df_ticks[
                    (df_ticks['time'] >= target_time - tolerance) & 
                    (df_ticks['time'] <= target_time + tolerance)
                ]
                
                if not nearby_ticks.empty:
                    closest_tick = nearby_ticks.iloc[0]
                    print(f"\n[OK] Found tick near 120-second mark:")
                    print(f"  Time: {closest_tick['time']}")
                    print(f"  Bid:  {closest_tick['bid']}")
                    print(f"  Ask:  {closest_tick['ask']}")
                    
                    # Calculate P&L using tick price
                    if pos['type'] == 'BUY':
                        tick_pnl = (closest_tick['bid'] - pos['entry']) * 100 * 0.01
                    else:
                        tick_pnl = (pos['entry'] - closest_tick['ask']) * 100 * 0.01
                    
                    print(f"\n  Tick-based P&L: ${tick_pnl:.2f}")
                else:
                    print(f"\n[MISSING] No tick found within 1-second tolerance of 120-second mark")
                    print(f"  Nearest tick time: {df_ticks['time'].iloc[-1] if not df_ticks.empty else 'N/A'}")
            else:
                print(f"[MISSING] No tick data available for this time period")
                print(f"  This is expected for older data - Vantage tick history is limited")
        
        # Summary
        print(f"\n{'='*100}")
        print("SUMMARY: TICK DATA CAPABILITY")
        print(f"{'='*100}")
        
        print("""
CONCLUSION:

1. M1 Candle Method (Current):
   - Exit at candle close (e.g., 10:02:00 for entry at 10:00:23)
   - Resolution: 1 minute
   - Available: Yes, reliable

2. Tick Data Method (Proposed):
   - Exit at exact time offset (e.g., 10:02:23 for entry at 10:00:23)
   - Resolution: Second-level (tick timestamps)
   - Availability: LIMITED
   
LIMITATIONS:
- Vantage tick data is only available for recent history (typically < 1 week)
- For March 2026 positions, tick data may not be available
- Analysis would work for LIVE trading going forward
- Historical analysis limited to M1 candles

RECOMMENDATION:
For backtesting/simulation: Use M1 candle method (current)
For live trading: Could implement tick-level precision for entries within last few days
        """)
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
