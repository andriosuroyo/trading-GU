#!/usr/bin/env python3
"""
MFE/MAE Analysis for Asia Session First Positions
Uses M1 bar data to calculate Maximum Favorable/Adverse Excursion
"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import MetaTrader5 as mt5
import gu_tools
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import pandas as pd

def get_mfe_mae_from_bars(open_price, direction, bars_df, holding_minutes=30):
    """
    Calculate MFE and MAE from M1 bar data for a given holding period.
    
    For BUY:
    - MFE = max(high) - open
    - MAE = open - min(low)
    
    For SELL:
    - MFE = open - min(low)
    - MAE = max(high) - open
    """
    if bars_df.empty:
        return None
    
    # Limit bars to holding period
    start_time = bars_df['time'].iloc[0]
    end_time = start_time + timedelta(minutes=holding_minutes)
    window_bars = bars_df[bars_df['time'] <= end_time].copy()
    
    if window_bars.empty:
        return None
    
    max_high = window_bars['high'].max()
    min_low = window_bars['low'].min()
    close_price = window_bars['close'].iloc[-1]
    
    if direction == 'BUY':
        mfe = max_high - open_price
        mae = open_price - min_low
        pnl_at_close = close_price - open_price
    else:  # SELL
        mfe = open_price - min_low
        mae = max_high - open_price
        pnl_at_close = open_price - close_price
    
    # XAUUSD: 1.0 point = $1.00 on 0.01 lot (confirmed from MT5)
    # Price 2890.50 -> 2890.70 = 0.20 points = $0.20 on 0.01 lot
    point_value = 0.01  # $0.01 per 0.01 lot per 0.01 price move
    # Actually: 1.0 point move = $1.00 on 0.01 lot
    # So multiply by 1.0 (not 0.01)
    
    return {
        'mfe_points': mfe,
        'mae_points': mae,
        'mfe_dollars': mfe * 0.01,  # Convert points to dollars for 0.01 lot
        'mae_dollars': mae * 0.01,
        'close_price': close_price,
        'pnl_at_close': pnl_at_close * 0.01,
        'bars_analyzed': len(window_bars),
        'duration_min': (window_bars['time'].iloc[-1] - start_time).total_seconds() / 60
    }

def fetch_bars_for_position(symbol, open_time, minutes=35, timeframe=mt5.TIMEFRAME_M1):
    """Fetch M1 bar data for a position."""
    from_time = open_time
    to_time = open_time + timedelta(minutes=minutes)
    
    rates = mt5.copy_rates_range(symbol, timeframe, from_time, to_time)
    
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
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

# Identify baskets
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

# Get first positions
first_positions = [b['positions'][0] for b in baskets]

# Filter out glitch baskets (simultaneous BUY/SELL at same timestamp)
glitches = [
    datetime(2026, 3, 12, 5, 2, 15, tzinfo=timezone.utc),
    datetime(2026, 3, 12, 5, 5, 19, tzinfo=timezone.utc),
]
clean_positions = [p for p in first_positions if p['open_time'] not in glitches]

print(f"\nTotal Asia first positions: {len(first_positions)}")
print(f"After removing {len(glitches)} glitch baskets: {len(clean_positions)}")
print("Fetching M1 bar data for MFE/MAE analysis...")

# Calculate MFE/MAE for each position
results = []
atr_values = []  # Store ATR60 values at position open

for i, pos in enumerate(clean_positions, 1):
    print(f"[{i}/{len(clean_positions)}] {pos['open_time']} {pos['strategy']} {pos['direction']} @ {pos['open_price']}")
    
    # Fetch 30+ minutes of M1 bars
    bars_df = fetch_bars_for_position('XAUUSD+', pos['open_time'], minutes=35)
    
    if bars_df.empty:
        print("  [WARNING] No bar data available")
        continue
    
    print(f"  [OK] Got {len(bars_df)} M1 bars")
    
    # Calculate ATR(60) at position open (using previous 60 bars before open)
    atr_from = pos['open_time'] - timedelta(minutes=70)
    atr_to = pos['open_time']
    atr_bars = mt5.copy_rates_range('XAUUSD+', mt5.TIMEFRAME_M1, atr_from, atr_to)
    
    atr_60 = None
    if atr_bars is not None and len(atr_bars) >= 60:
        atr_df = pd.DataFrame(atr_bars)
        # Calculate ATR: average of (high-low) over last 60 bars
        atr_60 = (atr_df['high'] - atr_df['low']).tail(60).mean()
        print(f"  [ATR60] {atr_60:.2f} points (${atr_60*0.01:.2f})")
    
    # Calculate MFE/MAE for different holding periods
    for minutes in range(2, 31):  # 2 to 30 minutes
        stats = get_mfe_mae_from_bars(pos['open_price'], pos['direction'], bars_df, minutes)
        if stats:
            results.append({
                'pos_id': pos['pos_id'],
                'open_time': pos['open_time'],
                'strategy': pos['strategy'],
                'magic': pos['magic'],
                'direction': pos['direction'],
                'open_price': pos['open_price'],
                'actual_pl': pos['net_pl'],
                'atr_60': atr_60,
                'holding_min': minutes,
                'mfe_points': stats['mfe_points'],
                'mae_points': stats['mae_points'],
                'mfe_dollars': stats['mfe_dollars'],
                'mae_dollars': stats['mae_dollars'],
                'pnl_at_exit': stats['pnl_at_close'],
                'close_price': stats['close_price'],
                'bars_count': stats['bars_analyzed']
            })

mt5.shutdown()

# Convert to DataFrame
results_df = pd.DataFrame(results)
results_df.to_csv('asia_mfe_mae_analysis.csv', index=False)
print(f"\n[SAVED] Results saved to asia_mfe_mae_analysis.csv ({len(results_df)} rows)")

# ============================================================================
# SIMULATION 1: Time-based exits for positions failing $0.20 MFE
# ============================================================================
print("\n" + "="*100)
print("SIMULATION 1: Time-Based Exits for Positions Failing $0.20 MFE")
print("="*100)

# For each position, check if it reached $0.20 MFE within holding period
# If not, exit at time limit

sim_results = []
for minutes in range(2, 31):
    # Filter data for this holding period
    period_data = results_df[results_df['holding_min'] == minutes].copy()
    
    if period_data.empty:
        continue
    
    # Determine if position reached $0.20 MFE
    period_data['hit_20mfe'] = period_data['mfe_dollars'] >= 0.20
    
    # For positions that hit $0.20 MFE: assume we take profit at $0.20
    # For positions that don't: exit at time limit (use pnl_at_exit)
    period_data['simulated_pnl'] = period_data.apply(
        lambda row: 0.20 if row['hit_20mfe'] else row['pnl_at_exit'], axis=1
    )
    
    total_pnl = period_data['simulated_pnl'].sum()
    hit_count = period_data['hit_20mfe'].sum()
    total_count = len(period_data)
    
    sim_results.append({
        'time_limit_min': minutes,
        'total_pnl': total_pnl,
        'hit_20mfe': hit_count,
        'missed_20mfe': total_count - hit_count,
        'hit_rate': hit_count / total_count * 100 if total_count > 0 else 0,
        'avg_pnl': total_pnl / total_count if total_count > 0 else 0
    })

sim_df = pd.DataFrame(sim_results)
print("\nTime Limit | Hit $0.20 MFE | Missed | Hit Rate | Total P&L | Avg P&L")
print("-" * 80)
for _, row in sim_df.iterrows():
    print(f"{row['time_limit_min']:>10} | {row['hit_20mfe']:>13} | {row['missed_20mfe']:>6} | "
          f"{row['hit_rate']:>7.1f}% | ${row['total_pnl']:>7.2f} | ${row['avg_pnl']:>6.2f}")

# ============================================================================
# SIMULATION 2: TargetProfitMoney Optimization with ATR60 matching
# ============================================================================
print("\n" + "="*100)
print("SIMULATION 2: TargetProfitMoney vs ATR60 Multiplier")
print("="*100)

# Get unique positions with their ATR60
pos_atr = results_df[results_df['holding_min'] == 30][['pos_id', 'atr_60', 'mfe_dollars']].copy()

# Define TargetProfitMoney values to test ($0.20 to $2.00, $0.10 increments)
tp_values = [x * 0.10 for x in range(2, 21)]  # 0.20, 0.30, ..., 2.00

tp_results = []
for tp in tp_values:
    # For each position, check if MFE >= TP (meaning TP would have been hit)
    hit_count = (pos_atr['mfe_dollars'] >= tp).sum()
    total_count = len(pos_atr)
    
    # Calculate PNL: TP for hits, actual close for misses
    simulated_pnl = pos_atr.apply(
        lambda row: tp if row['mfe_dollars'] >= tp else 
        results_df[(results_df['pos_id'] == row['pos_id']) & (results_df['holding_min'] == 30)]['pnl_at_exit'].iloc[0] 
        if len(results_df[(results_df['pos_id'] == row['pos_id']) & (results_df['holding_min'] == 30)]) > 0 else 0, 
        axis=1
    ).sum()
    
    # Calculate equivalent ATR60 multiplier
    avg_atr = pos_atr['atr_60'].mean()
    atr_multiplier = tp / (avg_atr * 0.01) if avg_atr and avg_atr > 0 else 0
    
    tp_results.append({
        'target_profit': tp,
        'atr_60_points': avg_atr if avg_atr else 0,
        'atr_multiplier': atr_multiplier,
        'hit_count': hit_count,
        'hit_rate': hit_count / total_count * 100 if total_count > 0 else 0,
        'total_pnl': simulated_pnl,
        'avg_pnl': simulated_pnl / total_count if total_count > 0 else 0
    })

tp_df = pd.DataFrame(tp_results)
print("\nTargetProfit | ATR60 Multiplier | Hit Rate | Total P&L | Avg P&L")
print("-" * 80)
for _, row in tp_df.iterrows():
    print(f"${row['target_profit']:>10.2f} | {row['atr_multiplier']:>16.2f}x | "
          f"{row['hit_rate']:>7.1f}% | ${row['total_pnl']:>7.2f} | ${row['avg_pnl']:>6.2f}")

# Best TP by total PNL
best_tp = tp_df.loc[tp_df['total_pnl'].idxmax()]
print(f"\n[OPTIMAL] Best TargetProfit: ${best_tp['target_profit']:.2f}")
print(f"  - ATR60 Multiplier: {best_tp['atr_multiplier']:.2f}x")
print(f"  - Hit Rate: {best_tp['hit_rate']:.1f}%")
print(f"  - Total P&L: ${best_tp['total_pnl']:.2f}")

# Save results
sim_df.to_csv('asia_time_exit_simulation.csv', index=False)
tp_df.to_csv('asia_target_profit_simulation.csv', index=False)
print("\n[SAVED] Simulation results saved to CSV files")
