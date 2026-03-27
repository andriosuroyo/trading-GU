import sys
sys.path.append('data')
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, date, timezone, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
blackbull_path = os.getenv('MT5_TERMINAL_BLACKBULL')

if mt5.initialize(path=blackbull_path):
    print("Connected to BlackBull")
    
    # Check M1 data availability
    target_time = datetime(2026, 3, 23, 1, 10, 0)
    utc_from = target_time - timedelta(hours=3)
    utc_to = target_time + timedelta(minutes=10)
    
    rates = mt5.copy_rates_range('XAUUSDp', mt5.TIMEFRAME_M1, utc_from, utc_to)
    if rates is not None and len(rates) > 0:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"\nM1 candles available: {len(df)}")
        print(f"Time range: {df['time'].min()} to {df['time'].max()}")
        
        # Try to calculate ATR
        if len(df) >= 60:
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = abs(df['high'] - df['close'].shift())
            df['low_close'] = abs(df['low'] - df['close'].shift())
            df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            atr = df['tr'].rolling(60).mean().iloc[-1]
            print(f"ATR(60): {atr:.4f}")
        else:
            print("Not enough candles for ATR(60)")
    else:
        print("No M1 data available for this time")
    
    mt5.shutdown()
else:
    print("Failed to connect to BlackBull")
