"""
Recovery Analysis with Tick Data
For each losing position, fetch ticks to determine if/when price returned to OpenPrice
"""
import MetaTrader5 as mt5
import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import time

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

# Load the positions we already identified
df = pd.read_csv('recovery_all_losses.csv')
print(f"\nAnalyzing {len(df)} losing positions for actual recovery...")

# Dates to process
dates = ['2026-03-20', '2026-03-23', '2026-03-24', '2026-03-25']

# For each date, fetch all positions (for opposing count tracking) and ticks
all_positions_by_date = {}

for date_str in dates:
    date = datetime.strptime(date_str, '%Y-%m-%d')
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        continue
    
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    positions = []
    for pid, siblings in deals_by_pos.items():
        entry_deal, exit_deal = None, None
        for s in siblings:
            if s.entry == 0:
                entry_deal = s
            elif s.entry == 1:
                exit_deal = s
        
        if entry_deal and exit_deal:
            open_time = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc)
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            profit = exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap
            
            positions.append({
                "ticket": pid,
                "direction": direction,
                "open_time": open_time,
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": profit,
                "magic": entry_deal.magic
            })
    
    positions.sort(key=lambda x: x["open_time"])
    all_positions_by_date[date_str] = positions

print(f"Loaded position data for {len(all_positions_by_date)} dates")

# Now analyze each losing position
results = []
MAX_RECOVERY_MINUTES = 240

for idx, row in df.iterrows():
    date_str = row['date']
    ticket = row['ticket']
    loss_direction = row['direction']
    loss_open_str = row['open_time']
    target_price = row['open_price']
    
    # Parse times
    loss_time = datetime.strptime(f"{date_str} {loss_open_str}", "%Y-%m-%d %H:%M:%S")
    loss_time = loss_time.replace(tzinfo=timezone.utc)
    
    # Recovery deadline
    deadline = loss_time + timedelta(minutes=MAX_RECOVERY_MINUTES)
    
    # Get all positions for this date
    date_positions = all_positions_by_date.get(date_str, [])
    
    # Find opposing positions opened after this loss
    opposing_direction = "SELL" if loss_direction == "BUY" else "BUY"
    opposing_positions = []
    
    for pos in date_positions:
        if pos['ticket'] == ticket:
            continue
        if pos['open_time'] > loss_time and pos['open_time'] <= deadline:
            if pos['direction'] == opposing_direction:
                opposing_positions.append({
                    'open_time': pos['open_time'],
                    'ticket': pos['ticket']
                })
    
    # Fetch tick data to check for recovery
    # We need ticks from loss_time to deadline
    symbol = "XAUUSD+"
    ticks = mt5.copy_ticks_range(symbol, loss_time, deadline, mt5.COPY_TICKS_ALL)
    
    recovered = False
    recovery_time = None
    opposing_at_recovery = 0
    min_price_diff = float('inf')
    max_price_diff = 0
    
    if ticks is not None and len(ticks) > 0:
        # Check if price ever hit target
        # For BUY: price needs to reach or exceed target_price
        # For SELL: price needs to reach or below target_price
        
        for i in range(len(ticks)):
            tick = ticks[i]
            tick_time = datetime.fromtimestamp(tick['time'], tz=timezone.utc)
            
            # Use bid price for SELL positions, ask for BUY
            if loss_direction == "BUY":
                price = tick['bid']  # For BUY recovery, we look at bid (what we can sell at)
            else:
                price = tick['ask']  # For SELL recovery, we look at ask (what we can buy at)
            
            diff = abs(price - target_price)
            min_price_diff = min(min_price_diff, diff)
            max_price_diff = max(max_price_diff, diff)
            
            if loss_direction == "BUY":
                if price >= target_price:
                    recovered = True
                    recovery_time = tick_time
                    break
            else:
                if price <= target_price:
                    recovered = True
                    recovery_time = tick_time
                    break
    
    # Count opposing positions at recovery time (if recovered) or at deadline
    if recovered and recovery_time:
        opposing_at_recovery = len([p for p in opposing_positions if p['open_time'] <= recovery_time])
        status = "RECOVERED"
        recovery_minutes = (recovery_time - loss_time).total_seconds() / 60
    else:
        opposing_at_recovery = len(opposing_positions)  # Total at deadline
        status = "LOST_TIMEOUT"
        recovery_time = None
        recovery_minutes = None
    
    results.append({
        'date': date_str,
        'ticket': ticket,
        'magic': row['magic'],
        'direction': loss_direction,
        'open_time': loss_open_str,
        'target_price': target_price,
        'close_price': row['close_price'],
        'loss_amount': row['loss_amount'],
        'opposing_60min': row['opposing_60min'],
        'opposing_120min': row['opposing_120min'],
        'opposing_180min': row['opposing_180min'],
        'opposing_240min': row['opposing_240min'],
        'opposing_at_recovery': opposing_at_recovery,
        'status': status,
        'recovery_time': recovery_time.strftime("%H:%M:%S") if recovery_time else None,
        'recovery_minutes': recovery_minutes,
        'min_price_diff': min_price_diff if not recovered else 0,
        'potential_recovery_profit': abs(row['loss_amount']) if recovered else 0
    })
    
    if (idx + 1) % 20 == 0:
        print(f"Processed {idx + 1}/{len(df)} positions...")

mt5.shutdown()

# Create DataFrame
df_results = pd.DataFrame(results)

# Save
df_results.to_csv('recovery_detailed_with_ticks.csv', index=False)

print("\n" + "="*100)
print("RECOVERY ANALYSIS COMPLETE")
print("="*100)

# Summary
recovered_count = len(df_results[df_results['status'] == 'RECOVERED'])
timeout_count = len(df_results[df_results['status'] == 'LOST_TIMEOUT'])

print(f"\nTotal losing positions: {len(df_results)}")
print(f"Recovered: {recovered_count} ({recovered_count/len(df_results)*100:.1f}%)")
print(f"Lost (timeout): {timeout_count} ({timeout_count/len(df_results)*100:.1f}%)")

# Recovery by opposing count (at 60min)
print("\n" + "="*100)
print("RECOVERY BY OPPOSING COUNT (at 60min mark)")
print("="*100)

rec_by_opp = df_results.groupby('opposing_60min').agg({
    'status': lambda x: (x == 'RECOVERED').sum(),
    'ticket': 'count'
}).rename(columns={'status': 'recovered', 'ticket': 'total'})
rec_by_opp['recovery_rate'] = (rec_by_opp['recovered'] / rec_by_opp['total'] * 100).round(1)
print(rec_by_opp.to_string())

# Show recovered positions sample
print("\n" + "="*100)
print("SAMPLE RECOVERED POSITIONS:")
print("="*100)
recovered_df = df_results[df_results['status'] == 'RECOVERED'].head(15)
print(recovered_df[['date', 'ticket', 'magic', 'direction', 'opposing_at_recovery', 'recovery_minutes', 'potential_recovery_profit']].to_string(index=False))

print(f"\nSaved detailed results to recovery_detailed_with_ticks.csv")
