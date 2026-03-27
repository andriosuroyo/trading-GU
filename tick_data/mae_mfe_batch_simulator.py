"""
MAE/MFE Batch Simulator for Magic 20 & 30 Positions
Measures 15-minute excursion window from entry
Outputs to CSV with comprehensive metrics
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import os
from collections import defaultdict

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
    """Connect to BlackBull for tick data"""
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_BLACKBULL")
    if not mt5.initialize(path=terminal_path):
        print(f"BlackBull init failed: {mt5.last_error()}")
        return False
    return True

def get_tick_data_blackbull(from_time, to_time):
    """Get tick data from BlackBull"""
    ticks = mt5.copy_ticks_range('XAUUSDp', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def calculate_mae_mfe(tick_df, direction, entry_price):
    """Calculate MAE and MFE from tick data"""
    if direction == "BUY":
        # For BUY: MAE = lowest bid, MFE = highest ask
        mae_idx = tick_df['bid'].idxmin()
        mfe_idx = tick_df['ask'].idxmax()
        mae_price = tick_df.loc[mae_idx, 'bid']
        mfe_price = tick_df.loc[mfe_idx, 'ask']
        mae_points = entry_price - mae_price
        mfe_points = mfe_price - entry_price
    else:  # SELL
        # For SELL: MAE = highest ask, MFE = lowest bid
        mae_idx = tick_df['ask'].idxmax()
        mfe_idx = tick_df['bid'].idxmin()
        mae_price = tick_df.loc[mae_idx, 'ask']
        mfe_price = tick_df.loc[mfe_idx, 'bid']
        mae_points = mae_price - entry_price
        mfe_points = entry_price - mfe_price
    
    mae_time = tick_df.loc[mae_idx, 'time']
    mfe_time = tick_df.loc[mfe_idx, 'time']
    
    return {
        'mae_price': mae_price,
        'mfe_price': mfe_price,
        'mae_points': mae_points,
        'mfe_points': mfe_points,
        'mae_time': mae_time,
        'mfe_time': mfe_time
    }

def detect_session(hour_utc):
    """Detect trading session"""
    if 2 <= hour_utc < 6:
        return "ASIA"
    elif 8 <= hour_utc < 12:
        return "LONDON"
    elif 17 <= hour_utc < 21:
        return "NY"
    else:
        return "OFF_SESSION"

def parse_strategy(magic):
    """Parse magic to strategy name"""
    magic_str = str(int(magic))
    if magic_str in ['10', '11', '12', '13']:
        return 'MH'
    elif magic_str in ['20', '21', '22', '23']:
        return 'HR10'
    elif magic_str in ['30', '31', '32', '33']:
        return 'HR05'
    elif magic_str.startswith('282603'):
        strategy_id = magic_str[6] if len(magic_str) > 6 else '?'
        strategies = {'0': 'TESTS', '1': 'HR10', '2': 'HR05', '3': 'MH'}
        return strategies.get(strategy_id, f'STRAT_{strategy_id}')
    return f'OTHER_{magic_str}'

def simulate_position(position, tick_df):
    """Run full MAE/MFE simulation for a position"""
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    volume = position['volume']
    
    # Calculate 15-minute window
    window_15min = open_time + timedelta(minutes=15)
    analysis_end = min(window_15min, close_time)  # Analyze until position closes or 15 min
    
    # Filter tick data to position lifetime (up to 15 min)
    pos_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= analysis_end)]
    
    if pos_ticks.empty:
        return None
    
    # Get entry/exit tick alignment
    entry_tick_idx = (pos_ticks['time'] - open_time).abs().idxmin()
    exit_tick_idx = (pos_ticks['time'] - close_time).abs().idxmin()
    entry_tick = pos_ticks.loc[entry_tick_idx]
    exit_tick = pos_ticks.loc[exit_tick_idx]
    
    # Calculate MAE/MFE
    mae_mfe = calculate_mae_mfe(pos_ticks, direction, entry_price)
    
    # Calculate actual P/L
    if direction == "BUY":
        actual_points = exit_price - entry_price
    else:
        actual_points = entry_price - exit_price
    
    # Normalized P/L
    net_pl = position['net_pl']
    normalized_net_pl = net_pl / (volume * 100)
    normalized_points = actual_points
    
    # Efficiency metrics
    mfe_capture_pct = (actual_points / mae_mfe['mfe_points'] * 100) if mae_mfe['mfe_points'] > 0 else 0
    mae_exposure_pct = (actual_points / mae_mfe['mae_points'] * 100) if mae_mfe['mae_points'] > 0 else 0
    efficiency_ratio = mae_mfe['mfe_points'] / mae_mfe['mae_points'] if mae_mfe['mae_points'] > 0 else 0
    
    # Time to MAE/MFE
    time_to_mae_sec = (mae_mfe['mae_time'] - open_time).total_seconds()
    time_to_mfe_sec = (mae_mfe['mfe_time'] - open_time).total_seconds()
    
    # Duration checks
    actual_duration_sec = (close_time - open_time).total_seconds()
    reached_2min = actual_duration_sec >= 120
    reached_5min = actual_duration_sec >= 300
    reached_15min = actual_duration_sec >= 900
    
    # Spread metrics
    spread = pos_ticks['ask'] - pos_ticks['bid']
    avg_spread = spread.mean()
    max_spread = spread.max()
    
    # Data quality
    entry_alignment = abs(entry_price - entry_tick['ask']) if direction == "BUY" else abs(entry_price - entry_tick['bid'])
    exit_alignment = abs(exit_price - exit_tick['bid']) if direction == "BUY" else abs(exit_price - exit_tick['ask'])
    
    if entry_alignment < 0.5 and exit_alignment < 0.5:
        data_quality = "High"
    elif entry_alignment < 1.0 and exit_alignment < 1.0:
        data_quality = "Medium"
    else:
        data_quality = "Low"
    
    return {
        # Position ID
        'position_id': position['pos_id'],
        'magic_number': position['magic'],
        'strategy': parse_strategy(position['magic']),
        'symbol': position['symbol'],
        'direction': direction,
        'volume': volume,
        
        # Timing
        'open_time': open_time.isoformat(),
        'close_time': close_time.isoformat(),
        'actual_duration_sec': actual_duration_sec,
        'analysis_window_end': analysis_end.isoformat(),
        
        # Price Data
        'entry_price': entry_price,
        'exit_price': exit_price,
        'tick_entry_bid': entry_tick['bid'],
        'tick_entry_ask': entry_tick['ask'],
        'tick_exit_bid': exit_tick['bid'],
        'tick_exit_ask': exit_tick['ask'],
        
        # MAE/MFE
        'mae_price': mae_mfe['mae_price'],
        'mfe_price': mae_mfe['mfe_price'],
        'mae_points': mae_mfe['mae_points'],
        'mfe_points': mae_mfe['mfe_points'],
        'mae_time': mae_mfe['mae_time'].isoformat(),
        'mfe_time': mae_mfe['mfe_time'].isoformat(),
        'time_to_mae_sec': time_to_mae_sec,
        'time_to_mfe_sec': time_to_mfe_sec,
        
        # P&L
        'actual_gross_pl': position['profit'],
        'actual_net_pl': net_pl,
        'actual_points': actual_points,
        'normalized_net_pl': normalized_net_pl,
        'normalized_points': normalized_points,
        
        # Efficiency
        'mfe_capture_pct': mfe_capture_pct,
        'mae_exposure_pct': mae_exposure_pct,
        'efficiency_ratio': efficiency_ratio,
        
        # Time-based
        'reached_2min': reached_2min,
        'reached_5min': reached_5min,
        'reached_15min': reached_15min,
        
        # Market Context
        'session': detect_session(open_time.hour),
        'hour_utc': open_time.hour,
        'tick_count_15min': len(pos_ticks),
        'avg_spread_15min': avg_spread,
        'max_spread_15min': max_spread,
        
        # Data Quality
        'tick_data_source': 'BlackBull',
        'entry_alignment_pts': entry_alignment,
        'exit_alignment_pts': exit_alignment,
        'data_quality_score': data_quality
    }

def fetch_and_simulate_all():
    """Main function to fetch positions and run simulations"""
    print("=" * 70)
    print("MAE/MFE BATCH SIMULATOR - Magic 20 & 30")
    print("=" * 70)
    
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
        print("No positions to simulate")
        return
    
    # Connect to BlackBull
    if not connect_blackbull():
        print("Failed to connect to BlackBull")
        return
    
    try:
        results = []
        
        for i, pos in enumerate(target_positions):
            open_time = datetime.fromisoformat(pos['open_time'])
            close_time = datetime.fromisoformat(pos['close_time'])
            
            # Fetch 15-minute window of tick data
            fetch_start = open_time - timedelta(seconds=5)
            fetch_end = open_time + timedelta(minutes=15) + timedelta(seconds=5)
            
            print(f"\n[{i+1}/{len(target_positions)}] Position {pos['pos_id']} - {pos['direction']} @ {open_time.strftime('%H:%M:%S')}")
            print(f"  Fetching tick data: {fetch_start.strftime('%H:%M:%S')} to {fetch_end.strftime('%H:%M:%S')}...")
            
            tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
            
            if tick_df is None or tick_df.empty:
                print(f"  ERROR: No tick data available")
                continue
            
            print(f"  Retrieved {len(tick_df)} ticks")
            
            # Run simulation
            result = simulate_position(pos, tick_df)
            
            if result:
                results.append(result)
                print(f"  MAE: -{result['mae_points']:.2f} pts @ {result['mae_time'][11:19]}")
                print(f"  MFE: +{result['mfe_points']:.2f} pts @ {result['mfe_time'][11:19]}")
                print(f"  Captured: {result['actual_points']:+.2f} pts ({result['mfe_capture_pct']:.1f}% of MFE)")
                print(f"  Quality: {result['data_quality_score']}")
            else:
                print(f"  ERROR: Simulation failed")
        
        # Save to CSV
        if results:
            df = pd.DataFrame(results)
            output_file = 'data/mae_mfe_march20_magic20_30.csv'
            df.to_csv(output_file, index=False)
            print(f"\n{'='*70}")
            print(f"SIMULATION COMPLETE")
            print(f"{'='*70}")
            print(f"Positions simulated: {len(results)}")
            print(f"Output file: {output_file}")
            print(f"\nColumns: {len(df.columns)}")
            print(f"Rows: {len(df)}")
            
            # Summary statistics
            print(f"\nSummary:")
            print(f"  Avg MAE: {df['mae_points'].mean():.2f} points")
            print(f"  Avg MFE: {df['mfe_points'].mean():.2f} points")
            print(f"  Avg Efficiency Ratio: {df['efficiency_ratio'].mean():.2f}")
            print(f"  Avg MFE Capture: {df['mfe_capture_pct'].mean():.1f}%")
            print(f"  High Quality Data: {(df['data_quality_score']=='High').sum()}/{len(df)}")
            
            return df
    
    finally:
        mt5.shutdown()
        print("\nDisconnected from BlackBull")

def main():
    fetch_and_simulate_all()

if __name__ == "__main__":
    main()
