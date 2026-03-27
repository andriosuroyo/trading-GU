"""Analyze March 25 14:01 SELL position - detailed recovery study"""
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

print(f"Connected to: {mt5.account_info().server} | Account: {mt5.account_info().login}")

# Fetch March 25 deals
date_from = datetime(2026, 3, 25, 0, 0, 0, tzinfo=timezone.utc)
date_to = datetime(2026, 3, 25, 23, 59, 59, tzinfo=timezone.utc)

deals = mt5.history_deals_get(date_from, date_to)
print(f"\nTotal deals: {len(deals) if deals else 0}")

# Group by position
deals_by_pos = defaultdict(list)
for d in deals:
    deals_by_pos[d.position_id].append(d)

# Find all positions
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
        direction = "BUY" if entry_deal.type == 0 else "SELL"
        profit = exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap
        duration = (close_time - open_time).total_seconds() / 60
        
        all_positions.append({
            "ticket": pid,
            "direction": direction,
            "open_time": open_time,
            "close_time": close_time,
            "open_price": entry_deal.price,
            "close_price": exit_deal.price,
            "profit": profit,
            "duration_min": duration,
            "magic": entry_deal.magic
        })

all_positions.sort(key=lambda x: x["open_time"])

# Find SELL positions opened around 14:01 that were LOSSES and ~10min duration
target_time = datetime(2026, 3, 25, 14, 1, 0, tzinfo=timezone.utc)
time_window = timedelta(minutes=3)

candidates = []
for pos in all_positions:
    if pos["direction"] == "SELL" and pos["profit"] < 0:  # LOSING SELL positions
        time_diff = abs((pos["open_time"] - target_time).total_seconds())
        if time_diff <= time_window.total_seconds():
            candidates.append(pos)

print(f"\nFound {len(candidates)} LOSING SELL position(s) opened around 14:01")

if not candidates:
    print("\nNo losing SELL positions found around 14:01.")
    print("Listing all SELL positions with losses on March 25:")
    sell_losses = [p for p in all_positions if p["direction"] == "SELL" and p["profit"] < 0]
    for p in sell_losses[:20]:
        print(f"  {p['open_time'].strftime('%H:%M:%S')} | Ticket {p['ticket']} | Magic {p['magic']} | "
              f"Duration {p['duration_min']:.1f}min | P&L ${p['profit']:.2f}")
    mt5.shutdown()
    exit(0)

# Show all candidates
print("\nCandidates:")
for i, pos in enumerate(candidates):
    print(f"  {i+1}. {pos['open_time'].strftime('%H:%M:%S')} | Ticket {pos['ticket']} | Magic {pos['magic']} | "
          f"Duration {pos['duration_min']:.1f}min | P&L ${pos['profit']:.2f}")

# Analyze the first matching position (closest to 14:01)
target_pos = candidates[0]

print("\n" + "="*80)
print("TARGET POSITION")
print("="*80)
print(f"Ticket: {target_pos['ticket']}")
print(f"Direction: {target_pos['direction']}")
print(f"Magic: {target_pos['magic']}")
print(f"Open: {target_pos['open_time'].strftime('%H:%M:%S')} @ {target_pos['open_price']}")
print(f"Close: {target_pos['close_time'].strftime('%H:%M:%S')} @ {target_pos['close_price']}")
print(f"Duration: {target_pos['duration_min']:.1f} min")
print(f"P&L: ${target_pos['profit']:.2f}")
print(f"Target Price (OpenPrice): {target_pos['open_price']}")

# Check if ~10 min duration
if abs(target_pos['duration_min'] - 10) > 2:
    print(f"\nWARNING: Duration is {target_pos['duration_min']:.1f} min, not ~10 min")

# Fetch tick data to find when price returned to OpenPrice
print("\n" + "="*80)
print("FETCHING TICK DATA FOR RECOVERY ANALYSIS")
print("="*80)

loss_close_time = target_pos['close_time']
recovery_search_end = loss_close_time + timedelta(minutes=240)  # 4 hour max

symbol = "XAUUSD+"
ticks = mt5.copy_ticks_range(symbol, loss_close_time, recovery_search_end, mt5.COPY_TICKS_ALL)

print(f"Fetched {len(ticks) if ticks is not None else 0} ticks")
print(f"Time range: {loss_close_time.strftime('%H:%M:%S')} to {recovery_search_end.strftime('%H:%M:%S')}")

target_price = target_pos['open_price']
recovered = False
recovery_time = None
recovery_price = None
min_price_seen = float('inf')
max_price_seen = 0

if ticks is not None and len(ticks) > 0:
    for i in range(len(ticks)):
        tick = ticks[i]
        tick_time = datetime.fromtimestamp(tick['time'], tz=timezone.utc)
        
        # For SELL recovery, we look at ask price (what we can buy at to close)
        price = tick['ask']
        
        min_price_seen = min(min_price_seen, price)
        max_price_seen = max(max_price_seen, price)
        
        # Check if price dropped to or below target (for SELL)
        if price <= target_price:
            recovered = True
            recovery_time = tick_time
            recovery_price = price
            break

print("\n" + "="*80)
print("RECOVERY ANALYSIS")
print("="*80)

if recovered:
    recovery_duration = (recovery_time - loss_close_time).total_seconds() / 60
    print(f"PRICE RETURNED TO OPENPRICE!")
    print(f"   Recovery Time: {recovery_time.strftime('%H:%M:%S')}")
    print(f"   Recovery Price: {recovery_price}")
    print(f"   Target was: {target_price}")
    print(f"   Time to Recover: {recovery_duration:.1f} minutes")
else:
    print(f"Price did NOT return to OpenPrice within 240 minutes")
    print(f"   Min price seen: {min_price_seen}")
    print(f"   Max price seen: {max_price_seen}")
    print(f"   Target was: {target_price}")

# Count opposing (BUY) positions opened between loss and recovery (or 240min)
print("\n" + "="*80)
print("OPPOSING POSITIONS ANALYSIS")
print("="*80)

analysis_end = recovery_time if recovered else recovery_search_end
opposing_count = 0
opposing_positions = []

for pos in all_positions:
    if pos['ticket'] == target_pos['ticket']:
        continue
    if pos['direction'] == "BUY":  # Opposing direction
        if loss_close_time < pos['open_time'] <= analysis_end:
            opposing_count += 1
            opposing_positions.append({
                'time': pos['open_time'].strftime('%H:%M:%S'),
                'ticket': pos['ticket'],
                'magic': pos['magic'],
                'price': pos['open_price']
            })

print(f"\nOpposing (BUY) positions opened between {loss_close_time.strftime('%H:%M:%S')} and {analysis_end.strftime('%H:%M:%S')}:")
print(f"Total count: {opposing_count}")

if opposing_positions:
    print("\nDetailed list (first 30):")
    for opp in opposing_positions[:30]:
        print(f"  {opp['time']} | Ticket {opp['ticket']} | Magic {opp['magic']} | Price {opp['price']}")
    if len(opposing_positions) > 30:
        print(f"  ... and {len(opposing_positions) - 30} more")

# Final summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Original Position: SELL @ {target_pos['open_price']} (Magic {target_pos['magic']})")
print(f"Closed at: {target_pos['close_time'].strftime('%H:%M:%S')} @ {target_pos['close_price']} (SL hit)")
print(f"Target: {target_pos['open_price']}")

if recovered:
    print(f"\n1. Returned to OpenPrice at: {recovery_time.strftime('%H:%M:%S')}")
    print(f"2. Opposing (BUY) positions before recovery: {opposing_count}")
    print(f"3. Recovery time: {recovery_duration:.1f} minutes")
    print(f"\nRecovery Trade Opportunity:")
    print(f"   Entry: {target_pos['close_time'].strftime('%H:%M:%S')} @ ~{target_pos['close_price']}")
    print(f"   Target: {target_pos['open_price']}")
    print(f"   Exit: {recovery_time.strftime('%H:%M:%S')} @ {recovery_price}")
    profit = target_pos['open_price'] - target_pos['close_price']
    print(f"   Profit: ~{profit:.2f} points")
else:
    print(f"\n1. Did NOT return to OpenPrice within 240 minutes")
    print(f"2. Opposing (BUY) positions opened: {opposing_count}")
    print(f"3. Recovery: FAILED")

mt5.shutdown()
