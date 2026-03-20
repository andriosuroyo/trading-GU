"""
Multi-TP Simulation with CORRECTED position data (March 2026)
Excludes 2 glitch baskets with simultaneous BUY/SELL
"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime


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
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize() failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    if info:
        print(f"Connected to: {info.server} | Account: {info.login}")
        return True
    return False

def get_m1_bars(from_time, to_time):
    """Get M1 bars from MT5."""
    rates = mt5.copy_rates_range('XAUUSD+', mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


# Asia session first positions - CORRECTED (March 2026, 62 positions, no glitch baskets)
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


def find_tp_hit(position, df_m1, tp_points):
    """Find which candle TP is hit (if any). Returns candle number or None."""
    entry_time = pd.to_datetime(position['time'])
    entry_price = position['entry']
    pos_type = position['type']
    
    if pos_type == 'BUY':
        tp_price = entry_price + tp_points * 0.01
    else:
        tp_price = entry_price - tp_points * 0.01
    
    future_candles = df_m1[df_m1['time'] >= entry_time].head(30)
    
    for i, (_, candle) in enumerate(future_candles.iterrows()):
        if pos_type == 'BUY':
            if candle['high'] >= tp_price:
                return i
        else:
            if candle['low'] <= tp_price:
                return i
    return None


def get_exit_pnl(position, df_m1, cutoff_candles):
    """Get P&L in dollars if exiting at cutoff candle close."""
    entry_time = pd.to_datetime(position['time'])
    entry_price = position['entry']
    pos_type = position['type']
    
    future_candles = df_m1[df_m1['time'] >= entry_time].head(cutoff_candles + 1)
    
    if len(future_candles) < cutoff_candles + 1:
        return None
    
    exit_price = future_candles.iloc[cutoff_candles]['close']
    
    if pos_type == 'BUY':
        return (exit_price - entry_price) * 100 * 0.01
    else:
        return (entry_price - exit_price) * 100 * 0.01


def simulate_tp_level(tp_points, cutoff_candles, positions_cache):
    """Simulate a specific TP level and cutoff time."""
    tp_hits = 0
    misses = 0
    total_pnl = 0.0
    sum_exit_pnl = 0.0
    max_candle = 0
    
    for pos in positions_data:
        pos_time = pd.to_datetime(pos['time'])
        
        # Get cached M1 data or fetch
        cache_key = pos['time'][:10]  # Use date as key
        if cache_key not in positions_cache:
            start_time = pos_time - pd.Timedelta(hours=2)
            end_time = pos_time + pd.Timedelta(hours=6)
            df_m1 = get_m1_bars(start_time, end_time)
            positions_cache[cache_key] = df_m1
        else:
            df_m1 = positions_cache[cache_key]
        
        if df_m1 is None or df_m1.empty:
            continue
        
        # Check TP hit
        hit_candle = find_tp_hit(pos, df_m1, tp_points)
        
        if hit_candle is not None and hit_candle < cutoff_candles:
            # TP hit within cutoff
            tp_hits += 1
            total_pnl += tp_points * 0.01
            if hit_candle > max_candle:
                max_candle = hit_candle
        else:
            # Miss - exit at cutoff
            exit_pnl = get_exit_pnl(pos, df_m1, cutoff_candles)
            if exit_pnl is not None:
                misses += 1
                sum_exit_pnl += exit_pnl
                total_pnl += exit_pnl
    
    return {
        'tp_points': tp_points,
        'tp_dollars': tp_points * 0.01,
        'cutoff': cutoff_candles,
        'tp_hits': tp_hits,
        'misses': misses,
        'win_rate': tp_hits / (tp_hits + misses) * 100 if (tp_hits + misses) > 0 else 0,
        'tp_pnl': tp_hits * tp_points * 0.01,
        'miss_pnl': sum_exit_pnl,
        'total_pnl': total_pnl,
        'avg_miss_pnl': sum_exit_pnl / misses if misses > 0 else 0,
        'max_candle': max_candle
    }


def main():
    if not connect_mt5():
        return
    
    try:
        print(f"\n{'='*100}")
        print("MULTI-TP SIMULATION - CORRECTED DATA (March 2026, 62 positions)")
        print(f"{'='*100}\n")
        
        # Cache for M1 data
        positions_cache = {}
        
        # Parameters
        tp_levels = list(range(30, 310, 10))  # 30, 40, 50, ... 300
        cutoffs = [2, 3, 5, 10, 15, 20, 30]
        
        all_results = []
        
        for cutoff in cutoffs:
            print(f"Processing cutoff {cutoff} minutes...")
            
            best_pnl = -999999
            best_result = None
            
            for tp in tp_levels:
                result = simulate_tp_level(tp, cutoff, positions_cache)
                all_results.append(result)
                
                if result['total_pnl'] > best_pnl:
                    best_pnl = result['total_pnl']
                    best_result = result
            
            print(f"  Best for cutoff {cutoff}: TP {best_result['tp_points']}pts = ${best_result['total_pnl']:.2f}")
        
        # Summary table
        print(f"\n{'='*100}")
        print("SUMMARY - BEST RESULTS BY CUTOFF TIME")
        print(f"{'='*100}\n")
        
        summary_data = []
        for cutoff in cutoffs:
            cutoff_results = [r for r in all_results if r['cutoff'] == cutoff]
            best = max(cutoff_results, key=lambda x: x['total_pnl'])
            summary_data.append([
                cutoff,
                f"{best['tp_points']} (${best['tp_dollars']:.2f})",
                f"{best['tp_hits']}/{best['tp_hits']+best['misses']}",
                f"{best['win_rate']:.1f}%",
                f"${best['tp_pnl']:.2f}",
                f"${best['miss_pnl']:.2f}",
                f"${best['total_pnl']:.2f}",
                f"${best['avg_miss_pnl']:.2f}"
            ])
        
        print(f"{'Cutoff':<8} {'Best TP':<18} {'Hits/Misses':<12} {'Win%':<8} {'TP Profit':<12} {'Miss Loss':<12} {'NET P&L':<12} {'Avg Miss':<10}")
        print("-" * 110)
        for row in summary_data:
            print(f"{row[0]:<8} {row[1]:<18} {row[2]:<12} {row[3]:<8} {row[4]:<12} {row[5]:<12} {row[6]:<12} {row[7]:<10}")
        
        # Best overall
        best_overall = max(all_results, key=lambda x: x['total_pnl'])
        print(f"\n{'='*100}")
        print("BEST OVERALL CONFIGURATION:")
        print(f"{'='*100}")
        print(f"TP Level: {best_overall['tp_points']} points (${best_overall['tp_dollars']:.2f})")
        print(f"Cutoff Time: {best_overall['cutoff']} candles")
        print(f"Win Rate: {best_overall['win_rate']:.1f}% ({best_overall['tp_hits']}/{best_overall['tp_hits']+best_overall['misses']})")
        print(f"TP Profit: ${best_overall['tp_pnl']:.2f}")
        print(f"Miss Loss: ${best_overall['miss_pnl']:.2f}")
        print(f"NET P&L: ${best_overall['total_pnl']:.2f}")
        print(f"{'='*100}\n")
        
        # Detailed breakdown for best config
        print("DETAILED BREAKDOWN (Best Configuration):")
        print(f"For TP {best_overall['tp_points']} with {best_overall['cutoff']} minute cutoff:")
        print(f"  - TP Hits: {best_overall['tp_hits']} positions x ${best_overall['tp_dollars']:.2f} = ${best_overall['tp_pnl']:.2f}")
        print(f"  - Misses: {best_overall['misses']} positions, avg loss ${best_overall['avg_miss_pnl']:.2f} each = ${best_overall['miss_pnl']:.2f}")
        print(f"  - Total: ${best_overall['total_pnl']:.2f}")
        
        # Save full results to CSV
        df_results = pd.DataFrame(all_results)
        df_results.to_csv('multi_tp_corrected_results.csv', index=False)
        print(f"\nFull results saved to multi_tp_corrected_results.csv")
        
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
