"""Fetch BB Demo positions by Magic Number — output to report file."""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict
import json

TERMINAL_PATH = r"C:\Program Files\MetaTrader 5_1\terminal64.exe"
MAGIC_NUMBERS = [28260301, 28260302]
OUTPUT_FILE = r"C:\Trading_GU\magic_report_output.json"

if not mt5.initialize(path=TERMINAL_PATH):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

info = mt5.account_info()
print(f"Connected: {info.server} | Account: {info.login}")

date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
date_to   = datetime(2030, 1, 1, tzinfo=timezone.utc)

deals = mt5.history_deals_get(date_from, date_to)
if deals is None or len(deals) == 0:
    print("No deals found.")
    mt5.shutdown()
    exit(0)

print(f"Total deals in range: {len(deals)}")

deals_by_pos = defaultdict(list)
for d in deals:
    deals_by_pos[d.position_id].append(d)

open_positions = mt5.positions_get()

report = {}

for magic in MAGIC_NUMBERS:
    entries = [d for d in deals if d.magic == magic and d.entry == 0]
    
    complete = []
    still_open_deals = []
    
    for entry_deal in entries:
        pid = entry_deal.position_id
        siblings = deals_by_pos[pid]
        
        exit_deal = None
        for s in siblings:
            if s.entry == 1 and s.position_id == pid:
                exit_deal = s
                break
        
        direction = "BUY" if entry_deal.type == 0 else "SELL"
        open_time = datetime.fromtimestamp(entry_deal.time).strftime("%Y-%m-%d %H:%M:%S")
        
        if exit_deal:
            close_time = datetime.fromtimestamp(exit_deal.time).strftime("%Y-%m-%d %H:%M:%S")
            complete.append({
                "pos_id": pid,
                "comment": entry_deal.comment,
                "symbol": entry_deal.symbol,
                "direction": direction,
                "volume": entry_deal.volume,
                "open_time": open_time,
                "close_time": close_time,
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": exit_deal.profit,
                "swap": exit_deal.swap,
                "commission": entry_deal.commission + exit_deal.commission,
            })
        else:
            still_open_deals.append({
                "pos_id": pid,
                "comment": entry_deal.comment,
                "symbol": entry_deal.symbol,
                "direction": direction,
                "volume": entry_deal.volume,
                "open_time": open_time,
                "open_price": entry_deal.price,
            })
    
    complete.sort(key=lambda x: x["open_time"])
    
    # Live open positions
    magic_open = []
    if open_positions:
        for p in open_positions:
            if p.magic == magic:
                magic_open.append({
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "direction": "BUY" if p.type == 0 else "SELL",
                    "volume": p.volume,
                    "open_time": datetime.fromtimestamp(p.time).strftime("%Y-%m-%d %H:%M:%S"),
                    "open_price": p.price_open,
                    "sl": p.sl,
                    "tp": p.tp,
                    "profit": p.profit,
                    "comment": p.comment,
                })
    
    # Summary
    summary = {}
    if complete:
        total_profit = sum(p["profit"] for p in complete)
        total_comm   = sum(p["commission"] for p in complete)
        total_swap   = sum(p["swap"] for p in complete)
        net_pl       = total_profit + total_comm + total_swap
        winners      = sum(1 for p in complete if p["profit"] > 0)
        losers       = sum(1 for p in complete if p["profit"] < 0)
        flat_count   = sum(1 for p in complete if p["profit"] == 0)
        
        avg_win  = sum(p["profit"] for p in complete if p["profit"] > 0) / max(winners, 1)
        avg_loss = sum(p["profit"] for p in complete if p["profit"] < 0) / max(losers, 1)
        
        summary = {
            "total_positions": len(complete),
            "gross_profit": round(total_profit, 2),
            "commission": round(total_comm, 2),
            "swap": round(total_swap, 2),
            "net_pl": round(net_pl, 2),
            "winners": winners,
            "losers": losers,
            "flat": flat_count,
            "win_rate_pct": round(winners/len(complete)*100, 1),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "reward_risk": round(abs(avg_win/avg_loss), 2) if losers > 0 else None,
        }
    
    report[str(magic)] = {
        "entry_deals": len(entries),
        "summary": summary,
        "closed_positions": complete,
        "open_deals": still_open_deals,
        "live_open_positions": magic_open,
    }

with open(OUTPUT_FILE, "w") as f:
    json.dump(report, f, indent=2, default=str)

print(f"Report saved to {OUTPUT_FILE}")
mt5.shutdown()
print("Done.")
