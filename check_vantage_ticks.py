import sys
sys.path.append('data')
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, date, timezone, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
vantage_path = os.getenv('MT5_TERMINAL_VANTAGE')

if mt5.initialize(path=vantage_path):
    print("Connected to Vantage")
    
    # Check tick data availability
    target_time = datetime(2026, 3, 23, 1, 10, 0)
    utc_from = target_time - timedelta(minutes=5)
    utc_to = target_time + timedelta(minutes=30)
    
    ticks = mt5.copy_ticks_range('XAUUSD+', utc_from, utc_to, mt5.COPY_TICKS_ALL)
    if ticks is not None and len(ticks) > 0:
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"\nTicks available: {len(df)}")
        print(f"Time range: {df['time'].min()} to {df['time'].max()}")
    else:
        print("No tick data available for this time")
    
    # Check M1 data
    rates = mt5.copy_rates_range('XAUUSD+', mt5.TIMEFRAME_M1, utc_from, utc_to)
    if rates is not None and len(rates) > 0:
        print(f"M1 candles: {len(rates)}")
    else:
        print("No M1 data available")
    
    mt5.shutdown()
else:
    print("Failed to connect to Vantage")
