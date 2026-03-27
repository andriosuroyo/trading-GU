"""Find March 25 position opened at 15:27"""
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

print(f"Unique positions: {len(deals_by_pos)}")

# Find position opened at ~15:27
target_time = datetime(2026, 3, 25, 15, 27, 0, tzinfo=timezone.utc)
time_window = timedelta(minutes=2)  # +/- 2 minutes

found_positions = []

for pid, siblings in deals_by_pos.items():
    entry_deal, exit_deal = None, None
    for s in siblings:
        if s.entry == 0:
            entry_deal = s
        elif s.entry == 1:
            exit_deal = s
    
    if entry_deal and exit_deal:
        open_time = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc)
        close_time = datetime.fromtimestamp(exit_deal.time, tz=timezone.utc)
        duration = (close_time - open_time).total_seconds() / 60  # minutes
        
        # Check if opened around 15:27
        time_diff = abs((open_time - target_time).total_seconds())
        
        if time_diff <= time_window.total_seconds():
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            profit = exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap
            
            found_positions.append({
                "ticket": pid,
                "direction": direction,
                "open_time": open_time.strftime("%Y-%m-%d %H:%M:%S"),
                "close_time": close_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_min": duration,
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": profit,
                "magic": entry_deal.magic,
                "symbol": entry_deal.symbol
            })

print("\n" + "="*80)
print(f"Positions opened around 15:27 on March 25:")
print("="*80)

if found_positions:
    for pos in found_positions:
        print(f"\nTicket: {pos['ticket']}")
        print(f"  Direction: {pos['direction']}")
        print(f"  Open: {pos['open_time']} @ {pos['open_price']}")
        print(f"  Close: {pos['close_time']} @ {pos['close_price']}")
        print(f"  Duration: {pos['duration_min']:.1f} min")
        print(f"  P&L: ${pos['profit']:.2f}")
        print(f"  Magic: {pos['magic']}")
        print(f"  Symbol: {pos['symbol']}")
else:
    print("No positions found around 15:27")
    
    # Let's list all positions with their open times to debug
    print("\n" + "="*80)
    print("All positions on March 25 (first 30):")
    print("="*80)
    
    all_positions = []
    for pid, siblings in deals_by_pos.items():
        entry_deal, exit_deal = None, None
        for s in siblings:
            if s.entry == 0:
                entry_deal = s
            elif s.entry == 1:
                exit_deal = s
        
        if entry_deal and exit_deal:
            open_time = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc)
            close_time = datetime.fromtimestamp(exit_deal.time, tz=timezone.utc)
            duration = (close_time - open_time).total_seconds() / 60
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            profit = exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap
            
            all_positions.append({
                "open_time": open_time,
                "ticket": pid,
                "direction": direction,
                "duration": duration,
                "profit": profit
            })
    
    # Sort by open time
    all_positions.sort(key=lambda x: x["open_time"])
    
    for pos in all_positions[:30]:
        print(f"{pos['open_time'].strftime('%H:%M:%S')} | {pos['ticket']} | {pos['direction']} | "
              f"{pos['duration']:5.1f}min | ${pos['profit']:7.2f}")

mt5.shutdown()
