"""
Investigate:
1. Why ATR doesn't have 60 candles (should pull from previous day if needed)
2. Why Magic6 shows fixed 2500 from 15min onwards
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, date, timezone
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 100)
print("INVESTIGATION: ATR Data Availability & Magic6 Fixed Values")
print("=" * 100)

# Connect to BlackBull
blackbull_path = os.getenv('MT5_TERMINAL_BLACKBULL')
if not mt5.initialize(path=blackbull_path):
    print("Failed to connect to BlackBull")
    exit(1)

print("\n1. CHECKING M1 DATA AVAILABILITY FOR EARLY MARCH 23RD POSITIONS")
print("-" * 100)

# Test times on March 23rd early morning
test_times = [
    datetime(2026, 3, 23, 1, 9, 0, tzinfo=timezone.utc),
    datetime(2026, 3, 23, 1, 12, 0, tzinfo=timezone.utc),
    datetime(2026, 3, 23, 2, 0, 0, tzinfo=timezone.utc),
]

for test_time in test_times:
    print(f"\nTest time: {test_time}")
    
    # Try to get 3 hours of history (should include previous day if needed)
    utc_from = test_time - timedelta(hours=6)  # Extended to 6 hours
    utc_to = test_time + timedelta(minutes=5)
    
    print(f"  Fetching from {utc_from} to {utc_to}")
    rates = mt5.copy_rates_range('XAUUSDp', mt5.TIMEFRAME_M1, utc_from, utc_to)
    
    if rates is not None and len(rates) > 0:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"  Total candles: {len(rates)}")
        print(f"  Time range: {df['time'].min()} to {df['time'].max()}")
        
        # Check if data exists before target time
        target_naive = test_time.replace(tzinfo=None)
        df_before = df[df['time'] <= target_naive]
        print(f"  Candles <= target: {len(df_before)}")
        
        if len(df_before) >= 60:
            # Calculate ATR
            df_calc = df_before.copy()
            df_calc['high_low'] = df_calc['high'] - df_calc['low']
            df_calc['high_close'] = abs(df_calc['high'] - df_calc['close'].shift())
            df_calc['low_close'] = abs(df_calc['low'] - df_calc['close'].shift())
            df_calc['tr'] = df_calc[['high_low', 'high_close', 'low_close']].max(axis=1)
            atr = df_calc['tr'].rolling(60).mean().iloc[-1]
            print(f"  [OK] ATR(60): {atr:.4f}")
        else:
            print(f"  [FAIL] Not enough candles for ATR(60). Have {len(df_before)}, need 60")
            print(f"     Data gap - candles may be missing from previous day")

print("\n" + "=" * 100)
print("2. INVESTIGATING MAGIC6 FIXED 2500 VALUES")
print("-" * 100)

# Read the Excel file and check Magic6 positions
xl = pd.ExcelFile('data/Analysis_20260323_v2.xlsx')
df_result = pd.read_excel(xl, sheet_name='RESULT')

print("\nMagic6 column from RESULT tab:")
print(df_result[['TimeWindow', 'Magic6']].to_string())

print("\n" + "-" * 100)
print("Looking at 15min sheet - Magic6 positions:")
df_15min = pd.read_excel(xl, sheet_name='15min')
magic6_positions = df_15min[df_15min['Magic Number'] == 6]
print(f"\nFound {len(magic6_positions)} Magic6 positions")
print(magic6_positions[['Ticket', 'Magic Number', 'Type', 'Outcome', 'OutcomePoints', 'MFE15Points', 'MAE15Points', 'ATRTP']].head(10).to_string())

# Check the distribution of OutcomePoints for Magic6
print("\n" + "-" * 100)
print("Magic6 OutcomePoints distribution in 15min sheet:")
print(magic6_positions['OutcomePoints'].value_counts().sort_index().head(20).to_string())

# Check 12min vs 15min for Magic6
print("\n" + "-" * 100)
print("Comparing Magic6 in 12min vs 15min sheets:")
df_12min = pd.read_excel(xl, sheet_name='12min')
magic6_12 = df_12min[df_12min['Magic Number'] == 6]['OutcomePoints'].sum()
magic6_15 = magic6_positions['OutcomePoints'].sum()
print(f"12min total: {magic6_12}")
print(f"15min total: {magic6_15}")

# Check individual Magic6 position outcomes across time windows
print("\n" + "-" * 100)
print("Sample Magic6 position across time windows:")
sample_ticket = magic6_positions.iloc[0]['Ticket'] if len(magic6_positions) > 0 else None
if sample_ticket:
    print(f"\nTracking {sample_ticket} across time windows:")
    for tw in ['10min', '12min', '14min', '15min', '20min', '30min']:
        df_tw = pd.read_excel(xl, sheet_name=tw)
        pos = df_tw[df_tw['Ticket'] == sample_ticket]
        if len(pos) > 0:
            print(f"  {tw}: Outcome={pos.iloc[0]['Outcome']}, Points={pos.iloc[0]['OutcomePoints']}, MFE={pos.iloc[0][f'MFE{tw[:-3]}Points']}, ATRTP={pos.iloc[0]['ATRTP']}")

mt5.shutdown()

print("\n" + "=" * 100)
print("INVESTIGATION COMPLETE")
print("=" * 100)
