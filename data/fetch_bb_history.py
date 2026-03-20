"""Fetch BlackBull MT5 GU_ positions with full open/close data.
Entry deals have GU_ comments; exit deals have blank comments but share position_id.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict

TERMINAL_PATH = r"C:\Program Files\MetaTrader 5_1\terminal64.exe"

if not mt5.initialize(path=TERMINAL_PATH):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

info = mt5.account_info()
print(f"Connected to: {info.server}  |  Account: {info.login}  |  Name: {info.name}")
print(f"Balance: {info.balance}  |  Equity: {info.equity}")

date_from = datetime(2020, 1, 1, tzinfo=timezone.utc)
date_to   = datetime(2030, 1, 1, tzinfo=timezone.utc)

deals = mt5.history_deals_get(date_from, date_to)

# Index all deals by position_id
deals_by_pos = defaultdict(list)
for d in deals:
    deals_by_pos[d.position_id].append(d)

# Find GU_ entries and pair with exits
gu_entries = [d for d in deals if d.comment and d.comment.startswith("GU_")]
print(f"\nTotal GU_ entry deals: {len(gu_entries)}")

complete = []
still_open = []

for entry in gu_entries:
    pid = entry.position_id
    siblings = deals_by_pos[pid]
    
    # Find the exit deal (entry==1) in the same position_id group
    exit_deal = None
    for s in siblings:
        if s.entry == 1:  # DEAL_ENTRY_OUT
            exit_deal = s
            break
    
    if exit_deal:
        direction = "BUY" if entry.type == 0 else "SELL"
        open_time  = datetime.fromtimestamp(entry.time).strftime("%Y-%m-%d %H:%M:%S")
        close_time = datetime.fromtimestamp(exit_deal.time).strftime("%Y-%m-%d %H:%M:%S")
        complete.append({
            "pos_id":      pid,
            "comment":     entry.comment,
            "symbol":      entry.symbol,
            "direction":   direction,
            "volume":      entry.volume,
            "open_time":   open_time,
            "close_time":  close_time,
            "open_price":  entry.price,
            "close_price": exit_deal.price,
            "profit":      exit_deal.profit,
            "swap":        exit_deal.swap,
            "commission":  entry.commission + exit_deal.commission,
        })
    else:
        direction = "BUY" if entry.type == 0 else "SELL"
        open_time = datetime.fromtimestamp(entry.time).strftime("%Y-%m-%d %H:%M:%S")
        still_open.append({
            "pos_id":    pid,
            "comment":   entry.comment,
            "direction": direction,
            "volume":    entry.volume,
            "open_time": open_time,
            "open_price": entry.price,
        })

complete.sort(key=lambda x: x["open_time"])
still_open.sort(key=lambda x: x["open_time"])

# ── Summary ──────────────────────────────────────────────────────────────
print(f"Closed positions: {len(complete)}")
print(f"Still open:       {len(still_open)}")

if complete:
    total_profit = sum(p["profit"] for p in complete)
    total_comm   = sum(p["commission"] for p in complete)
    total_swap   = sum(p["swap"] for p in complete)
    net_pl       = total_profit + total_comm + total_swap
    winners      = sum(1 for p in complete if p["profit"] > 0)
    losers       = sum(1 for p in complete if p["profit"] < 0)
    flat         = sum(1 for p in complete if p["profit"] == 0)

    print(f"\n--- Summary ---")
    print(f"Gross Profit: {total_profit:.2f}")
    print(f"Commission:   {total_comm:.2f}")
    print(f"Swap:         {total_swap:.2f}")
    print(f"Net P/L:      {net_pl:.2f}")
    print(f"Winners: {winners}  |  Losers: {losers}  |  Flat: {flat}")
    if len(complete) > 0:
        print(f"Win rate: {winners/len(complete)*100:.1f}%")

    # ── Closed positions table ────────────────────────────────────────────
    print(f"\n{'PosID':<12} {'Comment':<22} {'Dir':<5} {'Vol':<6} {'Open Time':<20} {'Close Time':<20} {'Open Price':<12} {'Close Price':<12} {'Profit':<10} {'Comm':<8} {'Swap':<8}")
    print("-" * 155)
    for p in complete:
        print(f"{p['pos_id']:<12} {p['comment']:<22} {p['direction']:<5} {p['volume']:<6} {p['open_time']:<20} {p['close_time']:<20} {p['open_price']:<12.5f} {p['close_price']:<12.5f} {p['profit']:<10.2f} {p['commission']:<8.2f} {p['swap']:<8.2f}")

# ── Still open ────────────────────────────────────────────────────────────
if still_open:
    print(f"\n--- Still Open ---")
    print(f"{'PosID':<12} {'Comment':<22} {'Dir':<5} {'Vol':<6} {'Open Time':<20} {'Open Price':<12}")
    print("-" * 85)
    for p in still_open:
        print(f"{p['pos_id']:<12} {p['comment']:<22} {p['direction']:<5} {p['volume']:<6} {p['open_time']:<20} {p['open_price']:<12.5f}")

mt5.shutdown()
print("\nDone.")
