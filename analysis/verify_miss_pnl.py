"""
Verify actual P&L for "miss" positions - those that don't hit TP within cutoff.
This calculates the real loss if we exit at candle close on the cutoff minute.
"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timezone

def load_env():
    """Load paths from .env file."""
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        env_vars[key.strip()] = val.strip()
    except:
        pass
    return env_vars


def connect_mt5():
    """Connect to MT5 terminal."""
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    
    if not terminal_path:
        print("Error: MT5_TERMINAL_VANTAGE not set in .env")
        return False
        
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize() failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
        
    info = mt5.account_info()
    if info:
        print(f"Connected to: {info.server} | Account: {info.login}")
        return True
    return False


def get_m1_bars(from_time, to_time):
    """Get M1 bars from MT5."""
    symbol = 'XAUUSD+'
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


# Asia session first positions data - CORRECTED from March 2026
# Excluding 2 glitch baskets (simultaneous BUY/SELL at same time)
positions_data = [
    {"time": "2026-03-11 02:07:00", "type": "SELL", "entry": 5194.74},
    {"time": "2026-03-11 02:17:00", "type": "BUY", "entry": 5189.78},
    {"time": "2026-03-11 02:21:30", "type": "SELL", "entry": 5195.52},
    {"time": "2026-03-11 02:44:00", "type": "BUY", "entry": 5192.12},
    {"time": "2026-03-11 02:57:00", "type": "SELL", "entry": 5194.68},
    {"time": "2026-03-11 03:06:00", "type": "BUY", "entry": 5189.41},
    {"time": "2026-03-11 03:17:00", "type": "SELL", "entry": 5195.67},
    {"time": "2026-03-11 04:44:00", "type": "BUY", "entry": 5214.20},
    {"time": "2026-03-11 04:48:00", "type": "SELL", "entry": 5216.71},
    {"time": "2026-03-11 05:39:00", "type": "SELL", "entry": 5205.72},
    {"time": "2026-03-12 02:28:00", "type": "SELL", "entry": 5156.10},
    {"time": "2026-03-12 02:35:00", "type": "BUY", "entry": 5150.55},
    {"time": "2026-03-12 03:21:00", "type": "SELL", "entry": 5143.66},
    {"time": "2026-03-12 05:35:00", "type": "BUY", "entry": 5165.53},
    {"time": "2026-03-12 05:36:54", "type": "BUY", "entry": 5162.85},
    {"time": "2026-03-12 05:43:00", "type": "BUY", "entry": 5156.21},
    {"time": "2026-03-12 08:41:00", "type": "SELL", "entry": 5152.55},
    {"time": "2026-03-11 02:04:00", "type": "SELL", "entry": 5192.19},
    {"time": "2026-03-11 02:16:00", "type": "BUY", "entry": 5188.96},
    {"time": "2026-03-11 02:21:00", "type": "SELL", "entry": 5195.53},
    {"time": "2026-03-11 02:41:00", "type": "BUY", "entry": 5193.02},
    {"time": "2026-03-11 02:55:00", "type": "SELL", "entry": 5193.70},
    {"time": "2026-03-11 03:05:00", "type": "BUY", "entry": 5190.47},
    {"time": "2026-03-11 03:16:00", "type": "SELL", "entry": 5195.60},
    {"time": "2026-03-11 04:10:00", "type": "BUY", "entry": 5213.66},
    {"time": "2026-03-11 04:13:39", "type": "SELL", "entry": 5215.59},
    {"time": "2026-03-11 04:25:00", "type": "BUY", "entry": 5215.07},
    {"time": "2026-03-11 04:34:00", "type": "SELL", "entry": 5217.50},
    {"time": "2026-03-11 04:41:00", "type": "BUY", "entry": 5215.00},
    {"time": "2026-03-11 05:20:00", "type": "SELL", "entry": 5204.67},
    {"time": "2026-03-12 02:14:00", "type": "SELL", "entry": 5153.53},
    {"time": "2026-03-12 02:35:00", "type": "BUY", "entry": 5150.55},
    {"time": "2026-03-12 03:13:00", "type": "SELL", "entry": 5140.44},
    {"time": "2026-03-12 03:49:00", "type": "BUY", "entry": 5151.25},
    {"time": "2026-03-12 04:00:00", "type": "BUY", "entry": 5153.13},
    {"time": "2026-03-12 04:09:00", "type": "BUY", "entry": 5154.86},
    {"time": "2026-03-12 04:15:00", "type": "SELL", "entry": 5157.22},
    {"time": "2026-03-12 04:19:00", "type": "SELL", "entry": 5158.33},
    {"time": "2026-03-12 04:31:00", "type": "BUY", "entry": 5157.01},
    {"time": "2026-03-12 04:35:00", "type": "SELL", "entry": 5158.26},
    {"time": "2026-03-12 05:24:00", "type": "BUY", "entry": 5169.32},
    {"time": "2026-03-11 02:06:00", "type": "SELL", "entry": 5193.31},
    {"time": "2026-03-11 02:07:15", "type": "SELL", "entry": 5195.67},
    {"time": "2026-03-11 02:17:00", "type": "BUY", "entry": 5189.78},
    {"time": "2026-03-11 02:21:30", "type": "SELL", "entry": 5195.52},
    {"time": "2026-03-11 02:42:00", "type": "BUY", "entry": 5191.95},
    {"time": "2026-03-11 02:56:00", "type": "SELL", "entry": 5193.70},
    {"time": "2026-03-11 03:06:00", "type": "BUY", "entry": 5189.41},
    {"time": "2026-03-11 03:17:00", "type": "SELL", "entry": 5195.67},
    {"time": "2026-03-11 04:26:00", "type": "BUY", "entry": 5212.19},
    {"time": "2026-03-11 04:35:00", "type": "SELL", "entry": 5219.89},
    {"time": "2026-03-11 04:41:00", "type": "BUY", "entry": 5215.00},
    {"time": "2026-03-11 05:26:00", "type": "SELL", "entry": 5205.62},
    {"time": "2026-03-12 02:17:00", "type": "SELL", "entry": 5153.85},
    {"time": "2026-03-12 02:36:00", "type": "BUY", "entry": 5149.72},
    {"time": "2026-03-12 03:15:00", "type": "SELL", "entry": 5138.86},
    {"time": "2026-03-12 04:16:00", "type": "BUY", "entry": 5154.57},
    {"time": "2026-03-12 04:19:15", "type": "SELL", "entry": 5159.11},
    {"time": "2026-03-12 04:32:00", "type": "BUY", "entry": 5155.19},
    {"time": "2026-03-12 04:35:04", "type": "SELL", "entry": 5158.00},
    {"time": "2026-03-12 05:27:00", "type": "BUY", "entry": 5171.01},
    {"time": "2026-03-12 05:28:58", "type": "BUY", "entry": 5168.47},
]

def check_tp_hit(position, df_m1, tp_points):
    """Check if TP is hit within candles. Returns (hit, candle_num, mfe)"""
    entry_time = pd.to_datetime(position['time'])
    entry_price = position['entry']
    pos_type = position['type']
    
    # Calculate TP price
    if pos_type == 'BUY':
        tp_price = entry_price + tp_points * 0.01
    else:
        tp_price = entry_price - tp_points * 0.01
    
    # Get candles after entry
    future_candles = df_m1[df_m1['time'] >= entry_time].head(30)
    
    if future_candles.empty:
        return False, None, 0
    
    max_mfe = 0  # in points
    
    for i, (_, candle) in enumerate(future_candles.iterrows()):
        # Check if TP hit in this candle
        if pos_type == 'BUY':
            # For BUY: TP hit if high >= tp_price
            candle_high = (candle['high'] - entry_price) * 100
            if candle_high > max_mfe:
                max_mfe = candle_high
            if candle['high'] >= tp_price:
                return True, i, max_mfe
        else:
            # For SELL: TP hit if low <= tp_price
            candle_low = (entry_price - candle['low']) * 100
            if candle_low > max_mfe:
                max_mfe = candle_low
            if candle['low'] <= tp_price:
                return True, i, max_mfe
    
    return False, None, max_mfe


def get_exit_pnl(position, df_m1, cutoff_candles):
    """Get P&L in DOLLARS if exiting at cutoff candle close."""
    entry_time = pd.to_datetime(position['time'])
    entry_price = position['entry']
    pos_type = position['type']
    
    # Get candle at cutoff
    future_candles = df_m1[df_m1['time'] >= entry_time].head(cutoff_candles + 1)
    
    if len(future_candles) < cutoff_candles + 1:
        return None  # Not enough data
    
    exit_candle = future_candles.iloc[cutoff_candles]
    exit_price = exit_candle['close']
    
    # Calculate P&L in dollars directly
    # 1 point = $0.01 (for 0.01 lot)
    if pos_type == 'BUY':
        pnl = (exit_price - entry_price) * 100 * 0.01  # price diff -> points -> dollars
    else:
        pnl = (entry_price - exit_price) * 100 * 0.01  # price diff -> points -> dollars
    
    return pnl


def main():
    if not connect_mt5():
        return
    
    try:
        # Settings
        tp_points = 200
        cutoff = 20
        
        print(f"\n{'='*80}")
        print(f"VERIFY MISS P&L - TP {tp_points} points, Cutoff {cutoff} candles")
        print(f"Positions: {len(positions_data)} Asia session first positions")
        print(f"{'='*80}\n")
        
        # Track positions
        tp_hits = []
        misses = []
        
        for pos in positions_data:
            entry_time = pd.to_datetime(pos['time'])
            
            # Get M1 data
            start_time = entry_time - pd.Timedelta(hours=2)
            end_time = entry_time + pd.Timedelta(hours=6)
            df_m1 = get_m1_bars(start_time, end_time)
            
            if df_m1 is None or df_m1.empty:
                continue
            
            # Check if TP hit
            hit, hit_candle, mfe = check_tp_hit(pos, df_m1, tp_points)
            
            if hit and hit_candle is not None and hit_candle < cutoff:
                tp_hits.append({
                    'time': pos['time'],
                    'type': pos['type'],
                    'entry': pos['entry'],
                    'hit_candle': hit_candle,
                    'mfe': mfe
                })
            else:
                # This is a miss - calculate exit P&L at cutoff
                exit_pnl = get_exit_pnl(pos, df_m1, cutoff)
                if exit_pnl is not None:
                    misses.append({
                        'time': pos['time'],
                        'type': pos['type'],
                        'entry': pos['entry'],
                        'exit_pnl': exit_pnl,
                        'mfe_before_cutoff': mfe
                    })
        
        print(f"TP HITS: {len(tp_hits)}/{len(positions_data)}")
        print(f"MISSES: {len(misses)}/{len(positions_data)}\n")
        
        if misses:
            print("-" * 80)
            print("MISS POSITIONS - Exit P&L at 20th candle close:")
            print("-" * 80)
            print(f"{'Time':<20} {'Type':<6} {'Entry':>10} {'Exit PnL (pts)':>15} {'Exit PnL ($)':>12}")
            print("-" * 80)
            
            total_miss_loss = 0
            for m in misses:
                pnl_dollars = m['exit_pnl']  # Already in dollars
                total_miss_loss += pnl_dollars
                exit_pnl_points = m['exit_pnl'] * 100  # Convert back to points for display
                print(f"{m['time']:<20} {m['type']:<6} {m['entry']:>10.2f} {exit_pnl_points:>15.1f} ${pnl_dollars:>11.2f}")
            
            print("-" * 80)
            print(f"{'TOTAL MISS LOSS:':<42} ${total_miss_loss:>25.2f}")
            print(f"{'Average per miss:':<42} ${total_miss_loss/len(misses):>25.2f}")
            
            print("\n")
            print("=" * 80)
            print("PROFITABILITY CALCULATION:")
            print("=" * 80)
            tp_profit = len(tp_hits) * tp_points * 0.01
            print(f"TP Hits: {len(tp_hits)} x {tp_points} pts x $0.01 = ${tp_profit:.2f}")
            print(f"Miss Losses: ${total_miss_loss:.2f}")
            print(f"NET P&L: ${tp_profit + total_miss_loss:.2f}")
    
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
