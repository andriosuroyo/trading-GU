"""Investigate why ATR is showing 0.0"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, date, timezone
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to BlackBull
blackbull_path = os.getenv('MT5_TERMINAL_BLACKBULL')
if not mt5.initialize(path=blackbull_path):
    print("Failed to connect to BlackBull")
    exit(1)

print("Connected to BlackBull")

# Test ATR calculation for a sample time
test_time = datetime(2026, 3, 23, 1, 9, 0, tzinfo=timezone.utc)
print(f"\nTesting ATR calculation for: {test_time}")

# Try to get M1 rates
utc_from = test_time - timedelta(hours=3)
utc_to = test_time + timedelta(minutes=5)

print(f"Fetching M1 rates from {utc_from} to {utc_to}")
rates = mt5.copy_rates_range('XAUUSDp', mt5.TIMEFRAME_M1, utc_from, utc_to)

if rates is not None and len(rates) > 0:
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    print(f"\nGot {len(rates)} M1 candles")
    print(f"Time range: {df['time'].min()} to {df['time'].max()}")
    print(f"\nFirst 5 candles:")
    print(df[['time', 'open', 'high', 'low', 'close']].head())
    
    # Check if we have enough data before target_time
    target_time_naive = test_time.replace(tzinfo=None)
    df_filtered = df[df['time'] <= target_time_naive]
    print(f"\nCandles before target time: {len(df_filtered)}")
    
    if len(df_filtered) >= 60:
        # Calculate ATR
        df_filtered['high_low'] = df_filtered['high'] - df_filtered['low']
        df_filtered['high_close'] = abs(df_filtered['high'] - df_filtered['close'].shift())
        df_filtered['low_close'] = abs(df_filtered['low'] - df_filtered['close'].shift())
        df_filtered['tr'] = df_filtered[['high_low', 'high_close', 'low_close']].max(axis=1)
        atr = df_filtered['tr'].rolling(60).mean().iloc[-1]
        print(f"\nATR(60): {atr:.4f}")
    else:
        print(f"\nNot enough candles for ATR(60). Need 60, have {len(df_filtered)}")
        print("This is why ATR is 0.0 - need 3 hours of history but data may start at 01:00")
else:
    print("No M1 rates returned")

mt5.shutdown()
