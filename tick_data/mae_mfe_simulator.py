"""
MAE/MFE Simulator - Reconstruct position lifecycle from tick data
Maximum Adverse Excursion: Worst price against position
Maximum Favorable Excursion: Best price for position
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
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

def get_tick_data_blackbull(from_time, to_time):
    """Get tick data from BlackBull (higher fidelity)"""
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_BLACKBULL")
    
    if not mt5.initialize(path=terminal_path):
        print(f"BlackBull init failed: {mt5.last_error()}")
        return None
    
    try:
        ticks = mt5.copy_ticks_range('XAUUSDp', from_time, to_time, mt5.COPY_TICKS_ALL)
        if ticks is None or len(ticks) == 0:
            return None
        
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        return df
    finally:
        mt5.shutdown()

def calculate_mae_mfe(tick_df, direction, entry_price, exit_price):
    """
    Calculate MAE and MFE from tick data
    For BUY: MAE = lowest bid, MFE = highest ask
    For SELL: MAE = highest ask, MFE = lowest bid
    """
    if direction == "BUY":
        # Worst price is lowest bid (we'd have to sell lower)
        mae_price = tick_df['bid'].min()
        # Best price is highest ask (we could sell higher)
        mfe_price = tick_df['ask'].max()
        
        mae_points = entry_price - mae_price  # How much against us
        mfe_points = mfe_price - entry_price  # How much for us
        
        # Also calculate from exit perspective
        exit_mae_points = exit_price - tick_df['ask'].min() if exit_price > tick_df['ask'].min() else 0
        exit_mfe_points = tick_df['bid'].max() - exit_price if tick_df['bid'].max() > exit_price else 0
        
    else:  # SELL
        # Worst price is highest ask (we'd have to buy higher to cover)
        mae_price = tick_df['ask'].max()
        # Best price is lowest bid (we could buy lower to cover)
        mfe_price = tick_df['bid'].min()
        
        mae_points = mae_price - entry_price  # How much against us
        mfe_points = entry_price - mfe_price  # How much for us
        
        exit_mae_points = tick_df['bid'].max() - exit_price if tick_df['bid'].max() > exit_price else 0
        exit_mfe_points = exit_price - tick_df['ask'].min() if exit_price > tick_df['ask'].min() else 0
    
    return {
        'mae_price': mae_price,
        'mae_points': mae_points,
        'mfe_price': mfe_price,
        'mfe_points': mfe_points,
        'exit_mae_points': exit_mae_points,
        'exit_mfe_points': exit_mfe_points
    }

def simulate_position(open_time, close_time, direction, entry_price, exit_price, volume):
    """Full position lifecycle simulation"""
    
    # Add buffer for tick fetching
    from_time = open_time - timedelta(seconds=5)
    to_time = close_time + timedelta(seconds=5)
    
    print(f"Fetching tick data from BlackBull...")
    print(f"  Time range: {from_time} to {to_time}")
    
    tick_df = get_tick_data_blackbull(from_time, to_time)
    
    if tick_df is None or tick_df.empty:
        print("ERROR: No tick data available")
        return None
    
    print(f"  Retrieved {len(tick_df)} ticks")
    
    # Filter to actual position duration
    position_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= close_time)]
    
    if position_ticks.empty:
        print("ERROR: No ticks during position lifetime")
        return None
    
    print(f"  Ticks during position: {len(position_ticks)}")
    print(f"  Time span: {position_ticks['time'].min()} to {position_ticks['time'].max()}")
    
    # Calculate MAE/MFE
    mae_mfe = calculate_mae_mfe(position_ticks, direction, entry_price, exit_price)
    
    # Calculate actual P/L points
    if direction == "BUY":
        actual_points = exit_price - entry_price
    else:
        actual_points = entry_price - exit_price
    
    # Calculate normalized P/L (per 0.01 lot)
    normalized_pl = (actual_points * 100 * volume) / (volume * 100)  # Points per 0.01 lot equivalent
    
    # Find tick at entry and exit
    entry_tick_idx = (position_ticks['time'] - open_time).abs().idxmin()
    exit_tick_idx = (position_ticks['time'] - close_time).abs().idxmin()
    
    entry_tick = position_ticks.loc[entry_tick_idx]
    exit_tick = position_ticks.loc[exit_tick_idx]
    
    return {
        'tick_count': len(position_ticks),
        'duration_seconds': (close_time - open_time).total_seconds(),
        'entry_price': entry_price,
        'exit_price': exit_price,
        'entry_tick_bid': entry_tick['bid'],
        'entry_tick_ask': entry_tick['ask'],
        'exit_tick_bid': exit_tick['bid'],
        'exit_tick_ask': exit_tick['ask'],
        'mae_price': mae_mfe['mae_price'],
        'mae_points': mae_mfe['mae_points'],
        'mfe_price': mae_mfe['mfe_price'],
        'mfe_points': mae_mfe['mfe_points'],
        'actual_points': actual_points,
        'normalized_pl_points': actual_points,  # Per 0.01 lot
        'volume': volume
    }

def main():
    print("=" * 70)
    print("MAE/MFE SIMULATOR - Position Lifecycle Reconstruction")
    print("=" * 70)
    
    # Position: 2026-03-20 23:32:00, BUY, 0.02 lots
    open_time = datetime(2026, 3, 20, 23, 32, 0, tzinfo=timezone.utc)
    close_time = datetime(2026, 3, 20, 23, 32, 44, tzinfo=timezone.utc)  # 44 seconds
    direction = "BUY"
    entry_price = 4501.77
    exit_price = 4504.25
    volume = 0.02
    
    print(f"\nPosition Details:")
    print(f"  Open: {open_time}")
    print(f"  Close: {close_time}")
    print(f"  Duration: 44 seconds")
    print(f"  Direction: {direction}")
    print(f"  Entry: {entry_price}")
    print(f"  Exit: {exit_price}")
    print(f"  Volume: {volume} lots")
    
    result = simulate_position(open_time, close_time, direction, entry_price, exit_price, volume)
    
    if result:
        print("\n" + "=" * 70)
        print("SIMULATION RESULTS")
        print("=" * 70)
        
        print(f"\nTick Data Alignment:")
        print(f"  Entry tick - Bid: {result['entry_tick_bid']:.2f}, Ask: {result['entry_tick_ask']:.2f}")
        print(f"  Exit tick  - Bid: {result['exit_tick_bid']:.2f}, Ask: {result['exit_tick_ask']:.2f}")
        print(f"  Entry alignment diff: {abs(entry_price - result['entry_tick_ask']):.2f} points")
        print(f"  Exit alignment diff: {abs(exit_price - result['exit_tick_bid']):.2f} points")
        
        print(f"\nPrice Action During Position:")
        print(f"  Highest Ask (MFE): {result['mfe_price']:.2f}")
        print(f"  Lowest Bid (MAE):  {result['mae_price']:.2f}")
        
        print(f"\nExcursion Analysis:")
        print(f"  Maximum Favorable Excursion (MFE): +{result['mfe_points']:.2f} points")
        print(f"  Maximum Adverse Excursion (MAE):   -{result['mae_points']:.2f} points")
        print(f"  Actual Captured:                   {result['actual_points']:+.2f} points")
        
        print(f"\nEfficiency Ratio:")
        if result['mfe_points'] > 0:
            capture_efficiency = (result['actual_points'] / result['mfe_points']) * 100
            print(f"  Capture Efficiency: {capture_efficiency:.1f}% (actual/max favorable)")
        
        print(f"\nRisk Metrics:")
        if result['mae_points'] > 0:
            reward_risk = result['actual_points'] / result['mae_points']
            print(f"  Actual R:R: {reward_risk:.2f} (captured vs adverse)")
        
        print(f"\nP/L Calculation:")
        gross_pl = result['actual_points'] * 100 * volume
        commission = -0.12  # From original data
        net_pl = gross_pl + commission
        normalized = net_pl / (volume * 100)
        print(f"  Gross P/L: ${gross_pl:.2f} ({result['actual_points']:.2f} pts × 100 × {volume} lots)")
        print(f"  Commission: ${commission:.2f}")
        print(f"  Net P/L: ${net_pl:.2f}")
        print(f"  Normalized (per 0.01 lot): ${normalized:.2f}")

if __name__ == "__main__":
    main()
