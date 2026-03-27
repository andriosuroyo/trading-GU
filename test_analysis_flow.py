"""
Test the exact flow used in risk_adjusted_analysis.py
"""
import sys
sys.path.append('C:/Trading_GU')
sys.path.append('C:/Trading_GU/data')

from fetch_all_gu_positions import fetch_all_positions, connect_mt5
from datetime import datetime, date, timezone, timedelta
import MetaTrader5 as mt5
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 80)
print("TESTING ANALYSIS FLOW")
print("=" * 80)

target_date = date(2026, 3, 23)

# Step 1: Connect to Vantage
print("\n1. Connecting to Vantage...")
if not connect_mt5("MT5_TERMINAL_VANTAGE"):
    print("Failed")
    exit(1)

# Step 2: Fetch positions
print("\n2. Fetching positions...")
positions_all = fetch_all_positions(
    datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc),
    datetime.combine(target_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
)
print(f"   Found {len(positions_all)} total positions")

positions = [p for p in positions_all if p.get('is_gu')]
print(f"   Found {len(positions)} GU positions")

# Show first position details
if positions:
    p = positions[0]
    print(f"\n   First position:")
    print(f"     ID: {p['pos_id']}")
    print(f"     Open time: {p['open_time']} (type: {type(p['open_time'])})")
    print(f"     Direction: {p['direction']}")
    print(f"     Entry price: {p['open_price']}")

# Step 3: Shutdown Vantage
print("\n3. Shutting down Vantage connection...")
mt5.shutdown()

# Step 4: Connect to BlackBull
print("\n4. Connecting to BlackBull...")
blackbull_path = os.getenv('MT5_TERMINAL_BLACKBULL')
if not mt5.initialize(path=blackbull_path):
    print(f"   Failed: {mt5.last_error()}")
    exit(1)
print(f"   Connected: {mt5.account_info().server}")

# Step 5: Try to get tick data for first position
if positions:
    p = positions[0]
    open_time = p['open_time']
    
    print(f"\n5. Testing tick data fetch for position {p['pos_id']}...")
    print(f"   Original open_time: {open_time}")
    
    # Handle timezone
    if open_time.tzinfo is not None:
        open_time = open_time.replace(tzinfo=None)
        print(f"   After tz removal: {open_time}")
    
    window_end = open_time + timedelta(minutes=30)
    print(f"   Window: {open_time} to {window_end}")
    
    # Try to fetch ticks
    ticks = mt5.copy_ticks_range('XAUUSDp', open_time, window_end, mt5.COPY_TICKS_ALL)
    
    if ticks is not None and len(ticks) > 0:
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"   SUCCESS: Got {len(ticks)} ticks")
        print(f"   Time range: {df['time'].min()} to {df['time'].max()}")
        
        # Test ATR calculation
        print(f"\n6. Testing ATR calculation...")
        atr_time = p['open_time']
        if atr_time.tzinfo is not None:
            atr_time = atr_time.replace(tzinfo=None)
        
        utc_from = atr_time - timedelta(hours=3)
        utc_to = atr_time + timedelta(minutes=5)
        
        rates = mt5.copy_rates_range('XAUUSDp', mt5.TIMEFRAME_M1, utc_from, utc_to)
        if rates is not None and len(rates) >= 60:
            df_rates = pd.DataFrame(rates)
            df_rates['time'] = pd.to_datetime(df_rates['time'], unit='s')
            df_rates = df_rates[df_rates['time'] <= atr_time]
            
            if len(df_rates) >= 60:
                df_rates['high_low'] = df_rates['high'] - df_rates['low']
                df_rates['high_close'] = abs(df_rates['high'] - df_rates['close'].shift())
                df_rates['low_close'] = abs(df_rates['low'] - df_rates['close'].shift())
                df_rates['tr'] = df_rates[['high_low', 'high_close', 'low_close']].max(axis=1)
                atr = df_rates['tr'].rolling(60).mean().iloc[-1]
                print(f"   SUCCESS: ATR(60) = {atr:.4f}")
            else:
                print(f"   FAILED: Only {len(df_rates)} candles available (need 60)")
        else:
            print(f"   FAILED: No M1 rates available (got {len(rates) if rates is not None else 0})")
    else:
        print(f"   FAILED: No tick data (result: {ticks})")

mt5.shutdown()
print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
