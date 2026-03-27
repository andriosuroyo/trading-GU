"""
Troubleshoot BlackBull tick data availability for March 23rd
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()
blackbull_path = os.getenv('MT5_TERMINAL_BLACKBULL')

print("=" * 80)
print("TROUBLESHOOTING BLACKBULL TICK DATA")
print("=" * 80)
print(f"\nTerminal path: {blackbull_path}")
print(f"Path exists: {os.path.exists(blackbull_path) if blackbull_path else 'N/A'}")

# Initialize MT5
if not mt5.initialize(path=blackbull_path):
    print(f"\nFailed to initialize MT5: {mt5.last_error()}")
    exit(1)

print(f"\nConnected to: {mt5.account_info().server}")
print(f"Account: {mt5.account_info().login}")

# Check available symbols
print("\n" + "=" * 80)
print("CHECKING AVAILABLE SYMBOLS")
print("=" * 80)

symbols_to_check = ['XAUUSDp', 'XAUUSD', 'GOLD', 'XAUUSD+']
for sym in symbols_to_check:
    selected = mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    if info:
        print(f"\n{sym}:")
        print(f"  Available: {info is not None}")
        print(f"  Visible: {info.visible if info else 'N/A'}")
        print(f"  Trade allowed: {info.trade_mode if info else 'N/A'}")
    else:
        print(f"\n{sym}: NOT AVAILABLE")

# Try to get tick data for March 23rd with different time ranges
print("\n" + "=" * 80)
print("CHECKING TICK DATA FOR MARCH 23RD")
print("=" * 80)

target_date = datetime(2026, 3, 23, 1, 10, 0, tzinfo=timezone.utc)

for symbol in ['XAUUSDp', 'XAUUSD']:
    print(f"\n--- Testing {symbol} ---")
    
    # Try different time ranges
    for hours_back in [1, 6, 12, 24, 48]:
        utc_from = target_date - timedelta(hours=hours_back)
        utc_to = target_date + timedelta(hours=1)
        
        ticks = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_ALL)
        
        if ticks is not None and len(ticks) > 0:
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            print(f"  Range -{hours_back}h to +1h: {len(ticks)} ticks")
            print(f"    Time range: {df['time'].min()} to {df['time'].max()}")
            break
        else:
            print(f"  Range -{hours_back}h to +1h: NO DATA")

# Check terminal time vs UTC
print("\n" + "=" * 80)
print("TERMINAL TIME INFO")
print("=" * 80)

time_info = mt5.symbol_info_tick('XAUUSDp')
if time_info:
    print(f"Last tick time: {datetime.fromtimestamp(time_info.time)}")
    print(f"Current UTC: {datetime.now(timezone.utc)}")
else:
    print("No tick info available")

# Check history availability
print("\n" + "=" * 80)
print("CHECKING M1 HISTORY AVAILABILITY")
print("=" * 80)

for symbol in ['XAUUSDp', 'XAUUSD']:
    for hours_back in [1, 6, 12, 24, 48, 72, 168]:
        utc_from = target_date - timedelta(hours=hours_back)
        utc_to = target_date + timedelta(hours=1)
        
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, utc_from, utc_to)
        
        if rates is not None and len(rates) > 0:
            print(f"{symbol}: M1 data found with -{hours_back}h offset ({len(rates)} candles)")
            break
    else:
        print(f"{symbol}: NO M1 DATA FOUND")

mt5.shutdown()
print("\n" + "=" * 80)
print("TROUBLESHOOTING COMPLETE")
print("=" * 80)
