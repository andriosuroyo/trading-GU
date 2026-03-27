"""Analyze the March 25 15:27 position - check price recovery and count opposing positions"""
import MetaTrader5 as mt5
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict

def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        env_vars[key.strip()] = val.strip()
    return env_vars

# Connect to MT5
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

info = mt5.account_info()
print(f"Connected to: {info.server} | Account: {info.login}")

# Fetch deals for March 25, 2026
date_from = datetime(2026, 3, 25, 0, 0, 0, tzinfo=timezone.utc)
date_to = datetime(2026, 3, 25, 23, 59, 59, tzinfo=timezone.utc)

deals = mt5.history_deals_get(date_from, date_to)
print(f"\nTotal deals on March 25: {len(deals) if deals else 0}")

if not deals:
    print("No deals found")
    mt5.shutdown()
    exit(0)

# Group by position
deals_by_pos = defaultdict(list)
for d in deals:
    deals_by_pos[d.position_id].append(d)

# Find the 15:27 position (1052996809)
target_ticket = 1052996809
original_position = None

for pid, siblings in deals_by_pos.items():
    if pid != target_ticket:
        continue
        
    entry_deal, exit_deal = None, None
    for s in siblings:
        if s.entry == 0:
            entry_deal = s
        elif s.entry == 1:
            exit_deal = s
    
    if entry_deal and exit_deal:
        open_time = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc)
        close_time = datetime.fromtimestamp(exit_deal.time, tz=timezone.utc)
        direction = "BUY" if entry_deal.type == 0 else "SELL"
        
        original_position = {
            "ticket": pid,
            "direction": direction,
            "open_time": open_time,
            "close_time": close_time,
            "open_price": entry_deal.price,
            "close_price": exit_deal.price,
            "magic": entry_deal.magic
        }
        break

if not original_position:
    print(f"Position {target_ticket} not found")
    mt5.shutdown()
    exit(1)

print("\n" + "="*80)
print("ORIGINAL POSITION")
print("="*80)
print(f"Ticket: {original_position['ticket']}")
print(f"Direction: {original_position['direction']}")
print(f"Open: {original_position['open_time'].strftime('%H:%M:%S')} @ {original_position['open_price']}")
print(f"Close: {original_position['close_time'].strftime('%H:%M:%S')} @ {original_position['close_price']}")
print(f"Target (OpenPrice): {original_position['open_price']}")

# Time range for analysis
window_start = original_position['open_time']  # 15:27
window_end = datetime(2026, 3, 25, 16, 3, 0, tzinfo=timezone.utc)  # 16:03

print("\n" + "="*80)
print(f"ANALYSIS WINDOW: {window_start.strftime('%H:%M:%S')} to {window_end.strftime('%H:%M:%S')}")
print("="*80)

# Count SELL positions opened between 15:27 and 16:03
sell_positions = []
for pid, siblings in deals_by_pos.items():
    entry_deal = None
    for s in siblings:
        if s.entry == 0:
            entry_deal = s
            break
    
    if entry_deal:
        open_time = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc)
        direction = "BUY" if entry_deal.type == 0 else "SELL"
        
        # Check if opened within our window
        if window_start <= open_time <= window_end:
            if direction == "SELL":
                sell_positions.append({
                    "ticket": pid,
                    "open_time": open_time,
                    "price": entry_deal.price,
                    "magic": entry_deal.magic
                })

print(f"\nSELL positions opened between 15:27 and 16:03: {len(sell_positions)}")

# Sort by time
sell_positions.sort(key=lambda x: x['open_time'])

for pos in sell_positions:
    time_str = pos['open_time'].strftime('%H:%M:%S')
    print(f"  {time_str} | Ticket: {pos['ticket']} | Magic: {pos['magic']} | Price: {pos['price']}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Original Position: BUY @ {original_position['open_price']} (Magic {original_position['magic']})")
print(f"Closed at: {original_position['close_price']} (SL hit after 10min)")
print(f"Target for recovery: {original_position['open_price']}")
print(f"\nOpposing (SELL) positions opened in same window: {len(sell_positions)}")

if sell_positions:
    print(f"  First SELL: {sell_positions[0]['open_time'].strftime('%H:%M:%S')} (Magic {sell_positions[0]['magic']})")
    print(f"  Last SELL: {sell_positions[-1]['open_time'].strftime('%H:%M:%S')} (Magic {sell_positions[-1]['magic']})")

mt5.shutdown()
