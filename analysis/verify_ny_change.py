"""Verify NY setfile change: InpStartHour=17, InpEndHour=22 (UTC+0)
Combined with 45/45 all-news filter and 2500 pts SL.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
from collections import defaultdict

MT5_TZ = timezone(timedelta(hours=2))
HARD_SL_PTS = 2500
HARD_SL_USD = HARD_SL_PTS / 100

# News events in MT5 server time (UTC+2) — converting to UTC for comparison
# All events in UTC:
ALL_NEWS_UTC = sorted([
    datetime(2026, 3, 3, 15, 0),   # ISM Mfg PMI 10AM ET = 15:00 UTC
    datetime(2026, 3, 4, 15, 0),   # Factory Orders / JOLTS
    datetime(2026, 3, 5, 13, 15),  # ADP Employment
    datetime(2026, 3, 5, 13, 30),  # Trade Balance
    datetime(2026, 3, 5, 15, 0),   # ISM Services PMI
    datetime(2026, 3, 6, 13, 30),  # Jobless Claims / Productivity
    datetime(2026, 3, 7, 13, 30),  # NFP
])

mt5.initialize(path=r"C:\Program Files\MetaTrader 5_1\terminal64.exe")
deals = mt5.history_deals_get(datetime(2020,1,1,tzinfo=timezone.utc), datetime(2030,1,1,tzinfo=timezone.utc))
d_by_pos = defaultdict(list)
for d in deals:
    d_by_pos[d.position_id].append(d)

PREFIXES = ("GU_HR10_", "GU_HR05_", "GU_MHB_", "GU_MHS_")
ny = []
for e in deals:
    if not (e.comment and e.comment.startswith(PREFIXES) and e.entry == 0 and e.comment.endswith("_NY")):
        continue
    ex = next((s for s in d_by_pos[e.position_id] if s.entry == 1), None)
    if ex:
        open_utc = datetime.fromtimestamp(e.time, tz=timezone.utc)
        open_server = open_utc.astimezone(MT5_TZ)
        ny.append({
            "pos_id": e.position_id,
            "comment": e.comment,
            "direction": "BUY" if e.type == 0 else "SELL",
            "open_ts": e.time,
            "open_utc_hour": open_utc.hour,
            "open_server_hour": open_server.hour,
            "open_price": e.price,
            "symbol": e.symbol,
            "profit": ex.profit,
            "commission": e.commission + ex.commission,
            "swap": ex.swap,
        })

ny.sort(key=lambda x: x["open_ts"])

# Compute MAE for SL
print(f"Computing MAE for {len(ny)} NY positions...")
for i, pos in enumerate(ny):
    utc_open = datetime.fromtimestamp(pos["open_ts"], tz=timezone.utc) - timedelta(minutes=1)
    ex_deal = next((s for s in d_by_pos[pos["pos_id"]] if s.entry == 1), None)
    utc_close = datetime.fromtimestamp(ex_deal.time, tz=timezone.utc) + timedelta(minutes=2)
    candles = mt5.copy_rates_range(pos["symbol"], mt5.TIMEFRAME_M1, utc_open, utc_close)
    
    if candles is None or len(candles) == 0:
        pos["mae_pts"] = 0
    elif pos["direction"] == "BUY":
        pos["mae_pts"] = max(0, (pos["open_price"] - min(c['low'] for c in candles)) * 100)
    else:
        pos["mae_pts"] = max(0, (max(c['high'] for c in candles) - pos["open_price"]) * 100)
    
    actual_net = pos["profit"] + pos["commission"] + pos["swap"]
    pos["actual_net"] = actual_net
    if pos["mae_pts"] >= HARD_SL_PTS:
        pos["sl_net"] = -HARD_SL_USD + pos["commission"] + pos["swap"]
        pos["stopped"] = True
    else:
        pos["sl_net"] = actual_net
        pos["stopped"] = False
    
    if (i + 1) % 100 == 0:
        print(f"  {i+1}/{len(ny)}...")

print(f"  {len(ny)}/{len(ny)} done.")
mt5.shutdown()

# News filter check
def is_news_blocked(open_ts_unix, before_min, after_min):
    open_utc = datetime.fromtimestamp(open_ts_unix, tz=timezone.utc).replace(tzinfo=None)
    for n in ALL_NEWS_UTC:
        if (n - timedelta(minutes=before_min)) <= open_utc <= (n + timedelta(minutes=after_min)):
            return True
    return False

print(f"\n{'='*100}")
print("VERIFICATION: NY SETFILE CHANGE")
print(f"{'='*100}")

# Current window: InpStartHour=14, InpEndHour=22 (UTC)
# = UTC hours 14-21 inclusive
current = [p for p in ny if 14 <= p["open_utc_hour"] < 22]

# Proposed window: InpStartHour=17, InpEndHour=22 (UTC)
# = UTC hours 17-21 inclusive
proposed = [p for p in ny if 17 <= p["open_utc_hour"] < 22]

# With 45/45 news filter on top of proposed window
proposed_filtered = [p for p in proposed if not is_news_blocked(p["open_ts"], 45, 45)]
news_blocked = [p for p in proposed if is_news_blocked(p["open_ts"], 45, 45)]

def summarize(label, positions):
    total_actual = sum(p["actual_net"] for p in positions)
    total_sl = sum(p["sl_net"] for p in positions)
    stops = sum(1 for p in positions if p["stopped"])
    wins_actual = sum(1 for p in positions if p["actual_net"] > 0)
    wins_sl = sum(1 for p in positions if p["sl_net"] > 0)
    wr_act = wins_actual/len(positions)*100 if positions else 0
    wr_sl = wins_sl/len(positions)*100 if positions else 0
    print(f"\n  {label}")
    print(f"    Positions: {len(positions)}")
    print(f"    No SL:     ${total_actual:>8.2f}  (WR: {wr_act:.1f}%)")
    print(f"    SL 2500:   ${total_sl:>8.2f}  (WR: {wr_sl:.1f}%, stops: {stops})")

print(f"\n--- Current: InpStartHour=14, InpEndHour=22 (UTC) ---")
print(f"    = Server time 16:00 - 00:00")
summarize("All NY (current window)", current)

print(f"\n--- Proposed: InpStartHour=17, InpEndHour=22 (UTC) ---")
print(f"    = Server time 19:00 - 00:00")
summarize("Proposed window (no news filter change)", proposed)
summarize("Proposed window + 45/45 all-news filter", proposed_filtered)

if news_blocked:
    print(f"\n  Positions blocked by 45/45 news filter:")
    nb_actual = sum(p["actual_net"] for p in news_blocked)
    nb_sl = sum(p["sl_net"] for p in news_blocked)
    print(f"    Count: {len(news_blocked)}, No SL P/L: ${nb_actual:.2f}, SL P/L: ${nb_sl:.2f}")

# Hourly detail for proposed window
print(f"\n--- UTC Hour Breakdown (proposed window 17:00-22:00 UTC) ---")
print(f"  {'UTC':<6} {'Server':<8} {'Count':<7} {'NoSL':<10} {'SL2500':<10} {'Stops'}")
print(f"  {'-'*50}")
for utc_h in range(17, 22):
    sub = [p for p in proposed if p["open_utc_hour"] == utc_h]
    if not sub: continue
    a = sum(p["actual_net"] for p in sub)
    s = sum(p["sl_net"] for p in sub)
    st = sum(1 for p in sub if p["stopped"])
    print(f"  {utc_h:02d}:00  {utc_h+2:02d}:00    {len(sub):<7} ${a:>7.2f}   ${s:>7.2f}   {st}")

# Full strategy summary
print(f"\n{'='*100}")
print("FULL STRATEGY PROJECTION")
print(f"{'='*100}")
# ASIA and LONDON are unchanged
ny_sl = sum(p["sl_net"] for p in proposed_filtered)
ny_stops = sum(1 for p in proposed_filtered if p["stopped"])
print(f"\n  ASIA:                +$111.96  (0 stops)")
print(f"  LONDON:              +$ 93.71  (0 stops)")
print(f"  NY (17-22 UTC+45/45): ${ny_sl:>+7.2f}  ({ny_stops} stops)")
total = 111.96 + 93.71 + ny_sl
print(f"  ---------------------------------")
print(f"  TOTAL:               ${total:>+7.2f}")

print(f"\n{'='*100}")
print("Done.")
