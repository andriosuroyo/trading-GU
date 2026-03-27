"""Investigate carry-over filtering issue."""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict
import os

def load_env():
    env_vars = {}
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars

env_vars = load_env()
mt5.initialize(path=env_vars.get('MT5_TERMINAL_VANTAGE'))

START_DATE = datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
END_DATE = datetime(2026, 3, 27, 23, 59, 59, tzinfo=timezone.utc)
GU_MAGICS = {11, 12, 13, 21, 22, 23, 31, 32, 33}

deals = mt5.history_deals_get(START_DATE, END_DATE)

deals_by_pos = defaultdict(list)
for d in deals:
    deals_by_pos[d.position_id].append(d)

positions = []
for pid, siblings in deals_by_pos.items():
    entry = None
    exit_d = None
    for s in siblings:
        if s.entry == 0:
            entry = s
        elif s.entry == 1:
            exit_d = s
    if entry and exit_d and entry.magic in GU_MAGICS:
        positions.append({
            'ticket': pid,
            'magic': entry.magic,
            'close_time': datetime.fromtimestamp(exit_d.time, tz=timezone.utc),
        })

# Check carry-over filter
print(f"Total GU positions: {len(positions)}")
print("\nClose time analysis (first 30):")
print("-" * 80)

carry_count = 0
for p in positions[:30]:
    magic = p['magic']
    close_hour = p['close_time'].hour
    
    # Session windows
    session = magic % 10
    if session == 1:
        window = (2, 6)  # Asia
        name = "Asia"
    elif session == 2:
        window = (8, 12)  # London
        name = "London"
    elif session == 3:
        window = (17, 21)  # NY
        name = "NY"
    else:
        window = None
        name = "Unknown"
    
    is_carry = False
    if window:
        start, end = window
        if close_hour < start or close_hour > end + 0.5:
            is_carry = True
    
    if is_carry:
        carry_count += 1
    
    print(f"Ticket {p['ticket']}: Magic {magic} ({name}), Close {p['close_time'].strftime('%m-%d %H:%M')} (hour {close_hour}), Carry: {is_carry}")

print("-" * 80)
print(f"Carry-over count in sample: {carry_count}/30")

# Full count
full_carry = 0
for p in positions:
    magic = p['magic']
    close_hour = p['close_time'].hour
    session = magic % 10
    if session == 1:
        window = (2, 6)
    elif session == 2:
        window = (8, 12)
    elif session == 3:
        window = (17, 21)
    else:
        window = None
    
    if window:
        start, end = window
        if close_hour < start or close_hour > end + 0.5:
            full_carry += 1

print(f"Total carry-over positions: {full_carry}/{len(positions)}")
print(f"Remaining after carry filter: {len(positions) - full_carry}")

mt5.shutdown()
