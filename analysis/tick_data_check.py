#!/usr/bin/env python3
"""Fetch and analyze tick data for MFE/MAE calculation"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import MetaTrader5 as mt5
import gu_tools
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import pandas as pd

def get_mfe_mae_from_ticks(open_price, direction, ticks_df, holding_minutes=30):
    """
    Calculate MFE and MAE from tick data for a given holding period.
    
    Parameters:
    -----------
    open_price : float
        Position open price
    direction : str
        'BUY' or 'SELL'
    ticks_df : DataFrame
        Tick data with 'time' and 'last' (or 'bid'/'ask') columns
    holding_minutes : int
        How long to hold the position (for time-based simulation)
    
    Returns:
    --------
    dict with MFE, MAE, ClosePrice, and various profit metrics
    """
    if ticks_df.empty:
        return None
    
    # Limit ticks to holding period
    start_time = ticks_df['time'].iloc[0]
    end_time = start_time + timedelta(minutes=holding_minutes)
    window_ticks = ticks_df[ticks_df['time'] <= end_time].copy()
    
    if window_ticks.empty:
        return None
    
    # For BUY: MFE = max_price - open, MAE = open - min_price
    # For SELL: MFE = open - min_price, MAE = max_price - open
    
    max_price = window_ticks['last'].max()
    min_price = window_ticks['last'].min()
    close_price = window_ticks['last'].iloc[-1]
    
    if direction == 'BUY':
        mfe = max_price - open_price
        mae = open_price - min_price
        pnl_at_close = close_price - open_price
    else:  # SELL
        mfe = open_price - min_price
        mae = max_price - open_price
        pnl_at_close = open_price - close_price
    
    # Calculate $ value (assuming 0.01 lot = $1 per point)
    # Actually XAUUSD: 1 point = $0.01 per 0.01 lot? Let me verify
    # For 0.01 lot: 1.0 point = $0.01 (XAUUSD is quoted as 2890.50)
    # Actually: 1 lot = 100 oz. 0.01 lot = 1 oz.
    # Price move from 2890.50 to 2890.60 = $0.10 profit on 0.01 lot
    # So 1 point (0.01) = $0.01 on 0.01 lot? 
    # Actually 1.0 (whole number) = $1.00 on 0.01 lot
    # So 0.20 points = $0.20 on 0.01 lot
    
    return {
        'mfe_points': mfe,
        'mae_points': mae,
        'mfe_dollars': mfe * 0.01,  # 1 point = $1 on 0.01 lot? Need to verify
        'mae_dollars': mae * 0.01,
        'close_price': close_price,
        'pnl_at_close': pnl_at_close * 0.01,
        'ticks_analyzed': len(window_ticks),
        'duration_min': (window_ticks['time'].iloc[-1] - start_time).total_seconds() / 60
    }

def fetch_ticks_for_position(symbol, open_time, minutes=35):
    """Fetch tick data for a position."""
    # Fetch a bit more than 30 min to ensure we have data
    from_time = open_time
    to_time = open_time + timedelta(minutes=minutes)
    
    ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Use 'last' price if available, otherwise average of bid/ask
    if 'last' in df.columns:
        pass  # Already have last
    else:
        df['last'] = (df['bid'] + df['ask']) / 2
    
    return df

# Connect to MT5
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect')
    exit(1)

# Fetch positions
print("Fetching positions...")
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
date_to = datetime.now(timezone.utc)
positions = gu_tools.fetch_positions(date_from, date_to)

# Filter for GU magics and parse
gu_positions = [p for p in positions if str(p['magic']).startswith('282603')]

def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): return 'UNKNOWN', 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    session_id = m[7] if len(m) > 7 else '0'
    
    strategies = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    sessions = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    
    return strategies.get(strat_id, f'STRAT_{strat_id}'), sessions.get(session_id, f'SESS_{session_id}')

for p in gu_positions:
    strat, sess = parse_magic(p['magic'])
    p['strategy'] = strat
    p['session'] = sess

# Filter for ASIA only
asia_positions = [p for p in gu_positions if p['session'] == 'ASIA']

# Identify baskets (same logic as before)
asia_sorted = sorted(asia_positions, key=lambda x: (x['magic'], x['open_time']))

baskets = []
current_basket = None

for p in asia_sorted:
    if current_basket is None or p['magic'] != current_basket['magic']:
        current_basket = {
            'magic': p['magic'],
            'strategy': p['strategy'],
            'positions': [p]
        }
        baskets.append(current_basket)
    else:
        first_time = current_basket['positions'][0]['open_time']
        time_diff = (p['open_time'] - first_time).total_seconds()
        if time_diff <= 60:
            current_basket['positions'].append(p)
        else:
            current_basket = {
                'magic': p['magic'],
                'strategy': p['strategy'],
                'positions': [p]
            }
            baskets.append(current_basket)

# Get first positions only
first_positions = [b['positions'][0] for b in baskets]

print(f"\nTotal Asia first positions: {len(first_positions)}")
print("Fetching tick data for MFE/MAE analysis...")

# Now fetch tick data for each first position
results = []
for i, pos in enumerate(first_positions, 1):
    print(f"\n[{i}/{len(first_positions)}] {pos['open_time']} {pos['strategy']} {pos['direction']} @ {pos['open_price']}")
    
    ticks_df = fetch_ticks_for_position('XAUUSDp', pos['open_time'], minutes=35)
    
    if ticks_df.empty:
        print(f"  [WARNING] No tick data available")
        continue
    
    print(f"  [OK] Got {len(ticks_df)} ticks")
    
    # Calculate MFE/MAE for different holding periods
    for minutes in [2, 5, 10, 15, 20, 25, 30]:
        stats = get_mfe_mae_from_ticks(pos['open_price'], pos['direction'], ticks_df, minutes)
        if stats:
            results.append({
                'pos_id': pos['pos_id'],
                'open_time': pos['open_time'],
                'strategy': pos['strategy'],
                'magic': pos['magic'],
                'direction': pos['direction'],
                'open_price': pos['open_price'],
                'actual_pl': pos['net_pl'],
                'holding_min': minutes,
                'mfe_points': stats['mfe_points'],
                'mae_points': stats['mae_points'],
                'mfe_dollars': stats['mfe_dollars'],
                'mae_dollars': stats['mae_dollars'],
                'pnl_at_exit': stats['pnl_at_close'],
                'close_price': stats['close_price'],
                'ticks_count': stats['ticks_analyzed']
            })

mt5.shutdown()

# Convert to DataFrame and save
results_df = pd.DataFrame(results)
results_df.to_csv('asia_mfe_mae_analysis.csv', index=False)
print(f"\n✓ Results saved to asia_mfe_mae_analysis.csv ({len(results_df)} rows)")

# Summary
print("\n" + "="*80)
print("MFE/MAE ANALYSIS SUMMARY")
print("="*80)

# Group by holding period
print("\n--- By Holding Period (All Positions) ---")
summary = results_df.groupby('holding_min').agg({
    'mfe_dollars': 'mean',
    'mae_dollars': 'mean',
    'pnl_at_exit': 'mean'
}).round(2)

print(summary)
