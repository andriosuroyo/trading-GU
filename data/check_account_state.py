"""Check current account state and recent activity"""
import MetaTrader5 as mt5
import os
from datetime import datetime, timezone, timedelta

def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

env_vars = load_env()
terminal_path = env_vars.get('MT5_TERMINAL_VANTAGE')

if not mt5.initialize(path=terminal_path):
    print('MT5 init failed')
    exit(1)

info = mt5.account_info()
print("=" * 60)
print("ACCOUNT STATE")
print("=" * 60)
print(f'Server: {info.server}')
print(f'Account: {info.login}')
print(f'Balance: ${info.balance:.2f}')
print(f'Equity: ${info.equity:.2f}')
print(f'Margin Used: ${info.margin:.2f}')
print(f'Margin Free: ${info.margin_free:.2f}')

# Check open positions
positions = mt5.positions_get()
print(f'\nOpen Positions: {len(positions) if positions else 0}')

if positions:
    for p in positions:
        direction = "BUY" if p.type == 0 else "SELL"
        print(f'  {p.ticket}: {direction} {p.volume} lots {p.symbol} @ {p.price_open:.2f} | P/L: ${p.profit:.2f} | Magic: {p.magic}')

# Check recent deals
now = datetime.now(timezone.utc)
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

# Today's deals
deals_today = mt5.history_deals_get(today_start, now)
print(f"\nToday's Deals: {len(deals_today) if deals_today else 0}")

# Last 14 days
days_back = 14
dates_with_activity = []
for i in range(days_back):
    day = today_start - timedelta(days=i)
    day_end = day + timedelta(days=1)
    deals = mt5.history_deals_get(day, day_end)
    if deals:
        gu_deals = [d for d in deals if str(d.magic).startswith('282603')]
        if gu_deals:
            dates_with_activity.append((day.date(), len(gu_deals)))

print(f"\nRecent GU Activity (last {days_back} days):")
if dates_with_activity:
    for date, count in sorted(dates_with_activity):
        print(f"  {date}: {count} deals")
else:
    print("  No GU activity found")

# Find last trade date
all_gu_deals = []
for i in range(30):  # Check last 30 days
    day = today_start - timedelta(days=i)
    day_end = day + timedelta(days=1)
    deals = mt5.history_deals_get(day, day_end)
    if deals:
        gu_deals = [d for d in deals if str(d.magic).startswith('282603')]
        if gu_deals:
            all_gu_deals.append((day.date(), gu_deals))

if all_gu_deals:
    last_date, last_deals = all_gu_deals[0]
    print(f"\nLast GU Trade Date: {last_date}")
    print(f"Days since last trade: {(today_start.date() - last_date).days}")
else:
    print("\nNo GU trades found in last 30 days")

mt5.shutdown()
print("\n" + "=" * 60)
