"""Debug price data for a specific position."""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime

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
        # Test position: 2025-11-03 08:01 BUY @ 5097.62
        entry_time = pd.to_datetime("2025-11-03 08:01")
        entry_price = 5097.62
        
        print(f"Entry: {entry_time} BUY @ {entry_price}")
        print()
        
        # Get M1 data
        start_time = entry_time - pd.Timedelta(hours=2)
        end_time = entry_time + pd.Timedelta(hours=6)
        df_m1 = get_m1_bars(start_time, end_time)
        
        if df_m1 is not None:
            # Show first 25 candles after entry
            future = df_m1[df_m1['time'] >= entry_time].head(25)
            print("First 25 candles after entry:")
            print(f"{'Candle':<8} {'Time':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10}")
            print("-" * 80)
            for i, (_, c) in enumerate(future.iterrows()):
                marker = " <-- Entry" if i == 0 else ""
                if i == 20:
                    marker = " <-- Cutoff"
                print(f"{i:<8} {str(c['time']):<20} {c['open']:>10.2f} {c['high']:>10.2f} {c['low']:>10.2f} {c['close']:>10.2f}{marker}")
            
            # Show candle 20 close
            candle_20 = future.iloc[20] if len(future) > 20 else None
            if candle_20 is not None:
                print()
                print(f"Candle 20 close: {candle_20['close']:.2f}")
                print(f"Entry: {entry_price:.2f}")
                print(f"Price diff: {candle_20['close'] - entry_price:.2f}")
                print(f"Points: {(candle_20['close'] - entry_price) * 100:.1f}")
                print(f"P&L $: {(candle_20['close'] - entry_price) * 100 * 0.01:.2f}")
    finally:
        mt5.shutdown()
