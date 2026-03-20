#!/usr/bin/env python3
"""Check actual trade durations for Asia positions"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import gu_tools
from datetime import datetime, timezone

# Connect
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    exit(1)

# Get Asia positions
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
positions = gu_tools.fetch_positions(date_from, datetime.now(timezone.utc))
gu_tools.mt5.shutdown()

# Filter Asia
gu_pos = [p for p in positions if str(p['magic']).startswith('282603')]

def parse_sess(magic):
    m = str(int(magic))
    sessions = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    return sessions.get(m[7] if len(m) > 7 else '0', 'UNKNOWN')

asia = [p for p in gu_pos if parse_sess(p['magic']) == 'ASIA']

# Sort by open time
asia_sorted = sorted(asia, key=lambda x: x['open_time'])

print('Sample ASIA positions with durations:')
print(f'{"Time":<20} {"Dir":<6} {"Open":<10} {"Close":<10} {"P/L":<10} {"Duration":<15} {"Lot":<8}')
print('-'*90)

total_dur = 0
for p in asia_sorted[:20]:
    dur = p['close_time'] - p['open_time']
    dur_sec = dur.total_seconds()
    total_dur += dur_sec
    dur_str = f"{int(dur_sec//60)}m {int(dur_sec%60)}s"
    time_str = p['open_time'].strftime('%m-%d %H:%M:%S')
    print(f"{time_str:<20} {p['direction']:<6} {p['open_price']:<10.2f} {p['close_price']:<10.2f} "
          f"{p['net_pl']:>8.2f} {dur_str:<15} {p['lot_size']:<8}")

avg_dur = total_dur / min(20, len(asia_sorted))
print(f"\nAverage duration (first 20): {avg_dur/60:.1f} minutes")

# Check MFE requirements
print("\n" + "="*80)
print("MFE REQUIREMENT ANALYSIS")
print("="*80)
print("\nFor $0.20 profit on 0.01 lot, we need 20 points MFE")
print("For $1.00 profit on 0.01 lot, we need 100 points MFE")
print(f"\nSample position: 2026-03-11 02:07:00 SELL @ 5194.74")
print(f"  Actual P/L: $1.80 (on 0.10 lot) = $0.18 (normalized to 0.01 lot)")
print(f"  Required MFE: ~18 points")
print(f"  Actual MFE (30min): 6.90 points (from tick data)")
print(f"  --> Position was held LONGER than 30 min to capture $0.18")
