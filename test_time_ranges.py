"""
Test different time ranges for tick data
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 80)
print("TESTING DIFFERENT TIME RANGES")
print("=" * 80)

blackbull_path = os.getenv('MT5_TERMINAL_BLACKBULL')
if not mt5.initialize(path=blackbull_path):
    print(f"Failed: {mt5.last_error()}")
    exit(1)

print(f"Connected: {mt5.account_info().server}")

# The position opened at 01:09:00 UTC on March 23rd
# Let's test various time windows around that time

base_time = datetime(2026, 3, 23, 1, 9, 0)  # No timezone - naive

print(f"\nBase time (from position): {base_time}")
print(f"Testing different offsets from base time...\n")

for offset_minutes in [-10, -5, 0, 5, 10, 30, 60]:
    test_time = base_time + timedelta(minutes=offset_minutes)
    window_end = test_time + timedelta(minutes=30)
    
    ticks = mt5.copy_ticks_range('XAUUSDp', test_time, window_end, mt5.COPY_TICKS_ALL)
    
    if ticks is not None and len(ticks) > 0:
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"  Offset +{offset_minutes:3d}min: {len(ticks):5d} ticks | {df['time'].min()} to {df['time'].max()}")
    else:
        print(f"  Offset +{offset_minutes:3d}min: NO DATA")

# Try with timezone-aware datetime
print("\n" + "=" * 80)
print("TESTING WITH TIMEZONE-AWARE DATETIME")
print("=" * 80)

base_time_utc = datetime(2026, 3, 23, 1, 9, 0, tzinfo=timezone.utc)

for offset_minutes in [0, 60]:
    test_time = base_time_utc + timedelta(minutes=offset_minutes)
    window_end = test_time + timedelta(minutes=30)
    
    print(f"\n  Testing with tzinfo (offset +{offset_minutes}min):")
    print(f"    From: {test_time} (tz: {test_time.tzinfo})")
    
    ticks = mt5.copy_ticks_range('XAUUSDp', test_time, window_end, mt5.COPY_TICKS_ALL)
    
    if ticks is not None and len(ticks) > 0:
        df = pd.DataFrame(ticks)
        print(f"    SUCCESS: {len(ticks)} ticks")
    else:
        print(f"    NO DATA")

# Check what time range actually has data
print("\n" + "=" * 80)
print("FINDING AVAILABLE TIME RANGE")
print("=" * 80)

# Try a wide range
wide_start = datetime(2026, 3, 23, 0, 0, 0)
wide_end = datetime(2026, 3, 23, 23, 59, 59)

ticks = mt5.copy_ticks_range('XAUUSDp', wide_start, wide_end, mt5.COPY_TICKS_ALL)
if ticks is not None and len(ticks) > 0:
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    print(f"Full day: {len(ticks)} ticks")
    print(f"Time range: {df['time'].min()} to {df['time'].max()}")
else:
    print("No data for full day")

mt5.shutdown()
print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)
