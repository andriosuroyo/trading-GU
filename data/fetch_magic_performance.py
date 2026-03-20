"""Fetch BlackBull MT5 closed positions by Magic Number and report performance.
Targets: 28260301 and 28260302 (active from 2026-03-10).
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict

TERMINAL_PATH = r"C:\Program Files\MetaTrader 5_1\terminal64.exe"
MAGIC_NUMBERS = [28260301, 28260302]

if not mt5.initialize(path=TERMINAL_PATH):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

info = mt5.account_info()
print(f"Connected to: {info.server}  |  Account: {info.login}  |  Name: {info.name}")
print(f"Balance: {info.balance}  |  Equity: {info.equity}")

date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
date_to   = datetime(2030, 1, 1, tzinfo=timezone.utc)

deals = mt5.history_deals_get(date_from, date_to)
if deals is None or len(deals) == 0:
    print("No deals found in the specified date range.")
    mt5.shutdown()
    exit(0)

print(f"Total deals in range: {len(deals)}")

# Index all deals by position_id
deals_by_pos = defaultdict(list)
for d in deals:
    deals_by_pos[d.position_id].append(d)

# Also check currently open positions
open_positions = mt5.positions_get()
open_by_magic = {}
if open_positions:
    for p in open_positions:
        if p.magic in MAGIC_NUMBERS:
            open_by_magic[p.ticket] = p

for magic in MAGIC_NUMBERS:
    print(f"\n{'='*80}")
    print(f"  MAGIC NUMBER: {magic}")
    print(f"{'='*80}")
    
    # Find entry deals with this magic number
    entries = [d for d in deals if d.magic == magic and d.entry == 0]  # DEAL_ENTRY_IN
    
    if not entries:
        # Check if there are any deals at all with this magic
        all_magic_deals = [d for d in deals if d.magic == magic]
        print(f"  No entry deals found. Total deals with this magic: {len(all_magic_deals)}")
        
        # Check open positions
        magic_open = [p for p in (open_positions or []) if p.magic == magic]
        if magic_open:
            print(f"\n  --- Currently Open Positions ({len(magic_open)}) ---")
            print(f"  {'Ticket':<12} {'Symbol':<12} {'Dir':<5} {'Vol':<6} {'Open Time':<20} {'Open Price':<12} {'Current P/L':<10} {'Comment'}")
            print(f"  {'-'*100}")
            for p in magic_open:
                direction = "BUY" if p.type == 0 else "SELL"
                open_time = datetime.fromtimestamp(p.time).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {p.ticket:<12} {p.symbol:<12} {direction:<5} {p.volume:<6} {open_time:<20} {p.price_open:<12.5f} {p.profit:<10.2f} {p.comment}")
            total_floating = sum(p.profit for p in magic_open)
            print(f"\n  Total floating P/L: ${total_floating:.2f}")
        else:
            print("  No open positions with this magic number either.")
        continue
    
    complete = []
    still_open_list = []
    
    for entry_deal in entries:
        pid = entry_deal.position_id
        siblings = deals_by_pos[pid]
        
        # Find the exit deal
        exit_deal = None
        for s in siblings:
            if s.entry == 1 and s.position_id == pid:  # DEAL_ENTRY_OUT
                exit_deal = s
                break
        
        direction = "BUY" if entry_deal.type == 0 else "SELL"
        open_time = datetime.fromtimestamp(entry_deal.time).strftime("%Y-%m-%d %H:%M:%S")
        
        if exit_deal:
            close_time = datetime.fromtimestamp(exit_deal.time).strftime("%Y-%m-%d %H:%M:%S")
            complete.append({
                "pos_id":      pid,
                "comment":     entry_deal.comment,
                "symbol":      entry_deal.symbol,
                "magic":       entry_deal.magic,
                "direction":   direction,
                "volume":      entry_deal.volume,
                "open_time":   open_time,
                "close_time":  close_time,
                "open_price":  entry_deal.price,
                "close_price": exit_deal.price,
                "profit":      exit_deal.profit,
                "swap":        exit_deal.swap,
                "commission":  entry_deal.commission + exit_deal.commission,
            })
        else:
            still_open_list.append({
                "pos_id":     pid,
                "comment":    entry_deal.comment,
                "symbol":     entry_deal.symbol,
                "direction":  direction,
                "volume":     entry_deal.volume,
                "open_time":  open_time,
                "open_price": entry_deal.price,
            })
    
    complete.sort(key=lambda x: x["open_time"])
    still_open_list.sort(key=lambda x: x["open_time"])
    
    print(f"  Entry deals found: {len(entries)}")
    print(f"  Closed positions:  {len(complete)}")
    print(f"  Still open (deals): {len(still_open_list)}")
    
    # Also check MT5 open positions for this magic
    magic_open = [p for p in (open_positions or []) if p.magic == magic]
    if magic_open:
        print(f"  Live open positions: {len(magic_open)}")
    
    if complete:
        total_profit = sum(p["profit"] for p in complete)
        total_comm   = sum(p["commission"] for p in complete)
        total_swap   = sum(p["swap"] for p in complete)
        net_pl       = total_profit + total_comm + total_swap
        winners      = sum(1 for p in complete if p["profit"] > 0)
        losers       = sum(1 for p in complete if p["profit"] < 0)
        flat         = sum(1 for p in complete if p["profit"] == 0)
        
        avg_win  = sum(p["profit"] for p in complete if p["profit"] > 0) / max(winners, 1)
        avg_loss = sum(p["profit"] for p in complete if p["profit"] < 0) / max(losers, 1)
        
        print(f"\n  --- Performance Summary ---")
        print(f"  Gross Profit: ${total_profit:.2f}")
        print(f"  Commission:   ${total_comm:.2f}")
        print(f"  Swap:         ${total_swap:.2f}")
        print(f"  Net P/L:      ${net_pl:.2f}")
        print(f"  Winners: {winners}  |  Losers: {losers}  |  Flat: {flat}")
        print(f"  Win Rate: {winners/len(complete)*100:.1f}%")
        print(f"  Avg Win:  ${avg_win:.2f}  |  Avg Loss: ${avg_loss:.2f}")
        if losers > 0:
            print(f"  Reward/Risk: {abs(avg_win/avg_loss):.2f}")
        
        print(f"\n  --- Closed Positions ---")
        print(f"  {'PosID':<12} {'Comment':<22} {'Symbol':<10} {'Dir':<5} {'Vol':<6} {'Open Time':<20} {'Close Time':<20} {'Open Price':<12} {'Close Price':<12} {'Profit':<10} {'Comm':<8} {'Swap':<8}")
        print(f"  {'-'*155}")
        for p in complete:
            print(f"  {p['pos_id']:<12} {p['comment']:<22} {p['symbol']:<10} {p['direction']:<5} {p['volume']:<6} {p['open_time']:<20} {p['close_time']:<20} {p['open_price']:<12.5f} {p['close_price']:<12.5f} {p['profit']:<10.2f} {p['commission']:<8.2f} {p['swap']:<8.2f}")
    
    if still_open_list:
        print(f"\n  --- Still Open (from deals) ---")
        for p in still_open_list:
            print(f"  {p['pos_id']:<12} {p['comment']:<22} {p['symbol']:<10} {p['direction']:<5} {p['volume']:<6} {p['open_time']:<20} {p['open_price']:<12.5f}")
    
    if magic_open:
        print(f"\n  --- Live Open Positions ---")
        print(f"  {'Ticket':<12} {'Symbol':<12} {'Dir':<5} {'Vol':<6} {'Open Time':<20} {'Open Price':<12} {'SL':<12} {'TP':<12} {'Current P/L':<10} {'Comment'}")
        print(f"  {'-'*120}")
        total_floating = 0
        for p in magic_open:
            direction = "BUY" if p.type == 0 else "SELL"
            open_time = datetime.fromtimestamp(p.time).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {p.ticket:<12} {p.symbol:<12} {direction:<5} {p.volume:<6} {open_time:<20} {p.price_open:<12.5f} {p.sl:<12.5f} {p.tp:<12.5f} {p.profit:<10.2f} {p.comment}")
            total_floating += p.profit
        print(f"\n  Total floating P/L: ${total_floating:.2f}")
    
    if not complete and not still_open_list and not magic_open:
        print("  No positions found for this magic number.")

mt5.shutdown()
print("\nDone.")
