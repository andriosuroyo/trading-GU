"""Verify one miss position manually."""

import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime

def connect_mt5():
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
    
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        return False
    return True

def get_m1_bars(from_time, to_time):
    rates = mt5.copy_rates_range('XAUUSD+', mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

if __name__ == "__main__":
    if not connect_mt5():
        exit(1)
    
    try:
        # Position: 2026-03-11 03:17:00 SELL @ 5195.67
        # Check if TP 200 hit within 20 candles
        entry_time = pd.to_datetime("2026-03-11 03:17:00")
        entry_price = 5195.67
        tp_points = 200
        tp_price = entry_price - tp_points * 0.01  # 5175.67 for SELL
        
        print(f"Position: SELL @ {entry_price} starting {entry_time}")
        print(f"TP Target: {tp_points} points = {tp_price} (SELL)")
        print()
        
        # Get M1 data
        start_time = entry_time - pd.Timedelta(hours=2)
        end_time = entry_time + pd.Timedelta(hours=6)
        df_m1 = get_m1_bars(start_time, end_time)
        
        if df_m1 is not None:
            future = df_m1[df_m1['time'] >= entry_time].head(25)
            
            print(f"{'Candle':<8} {'Time':<20} {'Low':>10} {'TP Hit?':<10} {'Close':>10}")
            print("-" * 70)
            
            tp_hit = False
            hit_candle = None
            
            for i, (_, c) in enumerate(future.iterrows()):
                hit_marker = ""
                if not tp_hit and c['low'] <= tp_price:
                    hit_marker = "YES <--"
                    tp_hit = True
                    hit_candle = i
                
                marker = " <-- Entry" if i == 0 else hit_marker
                if i == 20:
                    marker = " <-- Cutoff" if not marker else marker + " Cutoff"
                
                print(f"{i:<8} {str(c['time']):<20} {c['low']:>10.2f} {hit_marker:<10} {c['close']:>10.2f}{marker}")
            
            print()
            if tp_hit:
                print(f"TP HIT at candle {hit_candle}")
            else:
                candle_20 = future.iloc[20] if len(future) > 20 else None
                if candle_20 is not None:
                    exit_price = candle_20['close']
                    pnl_points = (entry_price - exit_price) * 100
                    pnl_dollars = pnl_points * 0.01
                    print(f"NO TP HIT within 20 candles")
                    print(f"Exit at candle 20 close: {exit_price}")
                    print(f"P&L: {pnl_points:.1f} points = ${pnl_dollars:.2f}")
    finally:
        mt5.shutdown()
