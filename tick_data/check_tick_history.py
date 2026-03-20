"""
Check how far back Vantage tick data is available
Test different time periods: 1 hour, 6 hours, 12 hours, 24 hours, 48 hours, 72 hours, 7 days
"""

import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

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
    info = mt5.account_info()
    if info:
        print(f"Connected: {info.server} | {info.login}")
    return True

def get_tick_data(from_time, to_time):
    """Get tick data"""
    ticks = mt5.copy_ticks_range('XAUUSD+', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None, 0
    return ticks, len(ticks)

def main():
    if not connect_mt5():
        return
    
    try:
        now = datetime.now(timezone.utc)
        
        # Test different time periods
        test_periods = [
            ("Last 1 hour", now - timedelta(hours=1), now),
            ("Last 6 hours", now - timedelta(hours=6), now),
            ("Last 12 hours", now - timedelta(hours=12), now),
            ("Last 24 hours", now - timedelta(hours=24), now),
            ("Last 48 hours", now - timedelta(hours=48), now),
            ("Last 72 hours", now - timedelta(hours=72), now),
            ("Last 5 days", now - timedelta(days=5), now),
            ("Last 7 days", now - timedelta(days=7), now),
            ("Last 14 days", now - timedelta(days=14), now),
        ]
        
        print("\n" + "="*100)
        print("VANTAGE TICK DATA AVAILABILITY TEST")
        print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("="*100)
        
        print(f"\n{'Period':<20} {'From':<20} {'To':<20} {'Status':<15} {'Tick Count':<15}")
        print("-"*100)
        
        for name, from_time, to_time in test_periods:
            ticks, count = get_tick_data(from_time, to_time)
            
            if ticks is not None:
                status = "AVAILABLE"
                # Get time range of returned data
                first_tick_time = datetime.fromtimestamp(ticks[0][0], tz=timezone.utc)
                last_tick_time = datetime.fromtimestamp(ticks[-1][0], tz=timezone.utc)
                age_hours = (now - first_tick_time).total_seconds() / 3600
                
                print(f"{name:<20} {from_time.strftime('%m-%d %H:%M'):<20} {to_time.strftime('%m-%d %H:%M'):<20} {status:<15} {count:<15,}")
                print(f"  -> Actual data from: {first_tick_time.strftime('%Y-%m-%d %H:%M:%S')} ({age_hours:.1f} hours ago)")
            else:
                status = "NOT AVAILABLE"
                print(f"{name:<20} {from_time.strftime('%m-%d %H:%M'):<20} {to_time.strftime('%m-%d %H:%M'):<20} {status:<15} {'0':<15}")
        
        # Try to find exact boundary
        print("\n" + "="*100)
        print("FINDING EXACT BOUNDARY")
        print("="*100)
        
        # Binary search for the boundary
        print("\nSearching for the oldest available tick data...")
        
        test_hours = [1, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120, 168]
        last_available = None
        first_unavailable = None
        
        for hours in test_hours:
            from_time = now - timedelta(hours=hours)
            ticks, count = get_tick_data(from_time, now)
            
            if ticks is not None and count > 100:  # Require meaningful amount of data
                oldest_tick = datetime.fromtimestamp(ticks[0][0], tz=timezone.utc)
                age = (now - oldest_tick).total_seconds() / 3600
                print(f"  {hours:>3} hours back: AVAILABLE (oldest tick: {age:.1f} hours ago)")
                last_available = hours
            else:
                print(f"  {hours:>3} hours back: NOT AVAILABLE")
                if first_unavailable is None:
                    first_unavailable = hours
        
        print("\n" + "="*100)
        print("CONCLUSION")
        print("="*100)
        
        if last_available:
            print(f"\nVantage tick data is available for approximately {last_available} hours ({last_available/24:.1f} days)")
        else:
            print("\nCould not determine exact boundary")
            
        if first_unavailable:
            print(f"Tick data is NOT available beyond {first_unavailable} hours")
        
        print(f"\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Oldest available tick data: approximately {(now - timedelta(hours=last_available)).strftime('%Y-%m-%d %H:%M') if last_available else 'N/A'} UTC")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
