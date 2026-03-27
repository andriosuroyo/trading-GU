"""
Fix ATR calculation for Monday positions (pull from Friday close)
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, date, timezone
from dotenv import load_dotenv
import os

load_dotenv()

def get_atr_with_weekend_handling(target_time):
    """
    Get ATR(60) handling weekend gap.
    For Monday positions, look back to Friday's close.
    """
    symbol = 'XAUUSDp'
    timeframe = mt5.TIMEFRAME_M1
    
    # Check if target_time is Monday
    target_date = target_time.date() if isinstance(target_time, datetime) else target_time
    weekday = target_date.weekday()  # 0=Monday, 6=Sunday
    
    print(f"Target time: {target_time}, Weekday: {weekday} (0=Monday)")
    
    # For Monday positions, we need to look back to Friday
    # Weekend gap: Friday 22:00 UTC to Monday 01:00 UTC (approx 51 hours)
    if weekday == 0:  # Monday
        # Look back 72 hours to ensure we get Friday data
        lookback_hours = 72
    else:
        lookback_hours = 3
    
    # Fetch data
    utc_from = target_time - timedelta(hours=lookback_hours)
    utc_to = target_time + timedelta(minutes=5)
    
    print(f"Fetching from {utc_from} to {utc_to}")
    rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    
    if rates is None or len(rates) == 0:
        print("No rates returned")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f"Total candles: {len(df)}")
    print(f"Time range: {df['time'].min()} to {df['time'].max()}")
    
    # Filter to candles before target time
    target_naive = target_time.replace(tzinfo=None) if target_time.tzinfo else target_time
    df_before = df[df['time'] <= target_naive].copy()
    
    print(f"Candles <= target: {len(df_before)}")
    
    if len(df_before) < 10:
        print("Not enough candles")
        return None
    
    # Calculate ATR
    df_before['high_low'] = df_before['high'] - df_before['low']
    df_before['high_close'] = abs(df_before['high'] - df_before['close'].shift())
    df_before['low_close'] = abs(df_before['low'] - df_before['close'].shift())
    df_before['tr'] = df_before[['high_low', 'high_close', 'low_close']].max(axis=1)
    
    # Use minimum 14 periods, ideally 60
    atr_periods = min(60, len(df_before) - 1)
    if atr_periods < 14:
        atr_periods = 14
    
    atr = df_before['tr'].rolling(atr_periods).mean().iloc[-1]
    
    if pd.isna(atr):
        return None
    
    return atr, len(df_before), atr_periods

# Connect to BlackBull
blackbull_path = os.getenv('MT5_TERMINAL_BLACKBULL')
if not mt5.initialize(path=blackbull_path):
    print("Failed to connect")
    exit(1)

print("=" * 80)
print("TESTING ATR WITH WEEKEND HANDLING")
print("=" * 80)

# Test Monday morning position
test_time = datetime(2026, 3, 23, 1, 9, 0, tzinfo=timezone.utc)
print("\nTest 1: Monday 01:09 (early position)")
result = get_atr_with_weekend_handling(test_time)
if result:
    atr, candles, periods = result
    print(f"[OK] ATR({periods}): {atr:.4f} (from {candles} candles)")
else:
    print("[FAIL] Failed")

# Test Monday later position
test_time2 = datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc)
print("\nTest 2: Monday 10:00 (later position)")
result2 = get_atr_with_weekend_handling(test_time2)
if result2:
    atr, candles, periods = result2
    print(f"✓ ATR({periods}): {atr:.4f} (from {candles} candles)")
else:
    print("✗ Failed")

mt5.shutdown()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
