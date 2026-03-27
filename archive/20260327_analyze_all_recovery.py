"""
Comprehensive Recovery Analysis for ALL losing positions
For each loss position:
1. Track opposing positions opened from loss time until recovery OR 240min timeout
2. If recovered: mark status and count opposing positions at recovery time
3. If not recovered within 240min: mark as LOST_TIMEOUT
4. Output detailed data for X threshold analysis
"""
import MetaTrader5 as mt5
import os
import pandas as pd
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

# Dates to analyze
dates = [
    datetime(2026, 3, 20),
    datetime(2026, 3, 23),
    datetime(2026, 3, 24),
    datetime(2026, 3, 25),
]

MAX_RECOVERY_MINUTES = 240

all_results = []

for date in dates:
    date_str = date.strftime('%Y-%m-%d')
    print(f"\n{'='*100}")
    print(f"PROCESSING: {date_str}")
    print(f"{'='*100}")
    
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        print(f"No deals for {date_str}")
        continue
    
    # Group by position
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    # Build list of all positions with details
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
            
            all_positions.append({
                "ticket": pid,
                "direction": direction,
                "open_time": open_time,
                "close_time": close_time,
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": profit,
                "magic": entry_deal.magic,
                "symbol": entry_deal.symbol
            })
    
    # Sort by open time
    all_positions.sort(key=lambda x: x["open_time"])
    
    # Get losing positions (profit < 0)
    losing_positions = [p for p in all_positions if p["profit"] < 0]
    print(f"Total positions: {len(all_positions)}, Losing positions: {len(losing_positions)}")
    
    # For each losing position, analyze recovery
    for loss in losing_positions:
        loss_open = loss["open_time"]
        loss_close = loss["close_time"]
        loss_direction = loss["direction"]
        target_price = loss["open_price"]  # We want price to return here
        
        opposing_direction = "SELL" if loss_direction == "BUY" else "BUY"
        
        # Recovery window: up to 240 minutes from open time
        recovery_deadline = loss_open + timedelta(minutes=MAX_RECOVERY_MINUTES)
        
        # Count opposing positions opened between loss_open and recovery_deadline
        # Also check if price ever returned to target
        opposing_positions = []
        recovered = False
        recovery_time = None
        recovery_opposing_count = 0
        
        for pos in all_positions:
            # Skip the loss position itself
            if pos["ticket"] == loss["ticket"]:
                continue
                
            pos_open = pos["open_time"]
            
            # Check if this position opened within our window
            if loss_open < pos_open <= recovery_deadline:
                # Check if it's opposing direction
                if pos["direction"] == opposing_direction:
                    opposing_positions.append({
                        "ticket": pos["ticket"],
                        "open_time": pos_open,
                        "magic": pos["magic"]
                    })
        
        # Now check if price recovered (we need tick data for accurate assessment)
        # For now, we'll use position close prices as proxy
        # If any position closed at or beyond target price in our direction, consider it recovered
        
        # Simplified recovery check: look at positions that opened after our loss
        # and see if price moved in our favor
        # Actually, we need tick data to know exactly when price hit target
        # For now, mark as "NEEDS_TICK_DATA"
        
        # Count opposing positions at different time markers
        opposing_60 = len([p for p in opposing_positions if p["open_time"] <= loss_open + timedelta(minutes=60)])
        opposing_120 = len([p for p in opposing_positions if p["open_time"] <= loss_open + timedelta(minutes=120)])
        opposing_180 = len([p for p in opposing_positions if p["open_time"] <= loss_open + timedelta(minutes=180)])
        opposing_240 = len([p for p in opposing_positions if p["open_time"] <= loss_open + timedelta(minutes=240)])
        
        all_results.append({
            "date": date_str,
            "ticket": loss["ticket"],
            "magic": loss["magic"],
            "direction": loss_direction,
            "open_time": loss_open.strftime("%H:%M:%S"),
            "close_time": loss_close.strftime("%H:%M:%S"),
            "open_price": loss["open_price"],
            "close_price": loss["close_price"],
            "loss_amount": loss["profit"],
            "opposing_60min": opposing_60,
            "opposing_120min": opposing_120,
            "opposing_180min": opposing_180,
            "opposing_240min": opposing_240,
            "recovery_status": "NEEDS_TICK_DATA",  # To be determined
            "recovery_time": None,
            "opposing_at_recovery": None
        })

mt5.shutdown()

# Create DataFrame and save
df = pd.DataFrame(all_results)

print("\n" + "="*100)
print(f"TOTAL LOSING POSITIONS ANALYZED: {len(df)}")
print("="*100)

# Summary by date
print("\nBy Date:")
for date in df['date'].unique():
    count = len(df[df['date'] == date])
    print(f"  {date}: {count} losing positions")

# Show sample
print("\n" + "="*100)
print("SAMPLE DATA (first 10):")
print("="*100)
print(df.head(10).to_string(index=False))

# Save to CSV
df.to_csv('recovery_all_losses.csv', index=False)
print(f"\nSaved {len(df)} records to recovery_all_losses.csv")

# Summary stats
print("\n" + "="*100)
print("OPPOSING POSITIONS DISTRIBUTION (at 60min mark):")
print("="*100)
dist_60 = df['opposing_60min'].value_counts().sort_index()
print(dist_60.to_string())

print("\n" + "="*100)
print("OPPOSING POSITIONS DISTRIBUTION (at 240min mark):")
print("="*100)
dist_240 = df['opposing_240min'].value_counts().sort_index()
print(dist_240.to_string())
