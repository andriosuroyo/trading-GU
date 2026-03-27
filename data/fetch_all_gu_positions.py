"""
Fetch ALL GU positions from Vantage Demo using comment-based detection.
Criteria: Comment contains "GU_" (case insensitive)
"""
import MetaTrader5 as mt5
import os
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

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

def connect_mt5(terminal_key="MT5_TERMINAL_VANTAGE"):
    """Connect to specified MT5 terminal"""
    env_vars = load_env()
    terminal_path = env_vars.get(terminal_key)
    
    if not terminal_path or not os.path.exists(terminal_path):
        print(f"Error: Terminal not found at {terminal_path}")
        return False
        
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize() failed: {mt5.last_error()}")
        return False
        
    info = mt5.account_info()
    print(f"Connected: {info.server} | Account: {info.login} | {info.name}")
    return True

def is_gu_position(comment, magic):
    """Check if position is GU strategy based on comment"""
    if comment and "GU_" in comment.upper():
        return True
    # Also check legacy magic numbers as fallback
    if magic and str(magic).startswith("282603"):
        return True
    return False

def parse_comment_session(comment):
    """Extract session info from comment"""
    if not comment:
        return "UNKNOWN"
    comment_upper = comment.upper()
    if "ASIA" in comment_upper:
        return "ASIA"
    elif "LONDON" in comment_upper:
        return "LONDON"
    elif "NEWYORK" in comment_upper or "NY" in comment_upper:
        return "NY"
    elif "FULL" in comment_upper:
        return "FULL"
    return "UNKNOWN"

def fetch_all_positions(date_from, date_to):
    """Fetch all historical positions with GU_ in comment"""
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        print(f"No deals found between {date_from} and {date_to}")
        return []
        
    print(f"Total raw deals found: {len(deals)}")
    
    # Group by position_id
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    positions = []
    gu_count = 0
    
    for pid, siblings in deals_by_pos.items():
        entry_deal = None
        exit_deal = None
        
        for s in siblings:
            if s.entry == 0:  # DEAL_ENTRY_IN
                entry_deal = s
            elif s.entry == 1:  # DEAL_ENTRY_OUT
                exit_deal = s
                
        if entry_deal and exit_deal:
            # Check if GU position
            is_gu = is_gu_position(entry_deal.comment, entry_deal.magic)
            
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            duration_seconds = exit_deal.time - entry_deal.time
            duration_minutes = duration_seconds / 60
            
            pos_data = {
                "pos_id": pid,
                "magic": entry_deal.magic,
                "symbol": entry_deal.symbol,
                "direction": direction,
                "volume": entry_deal.volume,
                "open_time": datetime.fromtimestamp(entry_deal.time, tz=timezone.utc),
                "close_time": datetime.fromtimestamp(exit_deal.time, tz=timezone.utc),
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": exit_deal.profit,
                "commission": entry_deal.commission + exit_deal.commission,
                "swap": exit_deal.swap,
                "net_pl": exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap,
                "duration_minutes": duration_minutes,
                "comment": entry_deal.comment,
                "session": parse_comment_session(entry_deal.comment),
                "is_gu": is_gu
            }
            
            positions.append(pos_data)
            if is_gu:
                gu_count += 1
    
    positions.sort(key=lambda x: x["open_time"])
    print(f"GU positions identified: {gu_count}")
    return positions

def fetch_open_positions():
    """Fetch currently open positions"""
    open_pos = mt5.positions_get()
    if not open_pos:
        return []
    
    positions = []
    for p in open_pos:
        if is_gu_position(p.comment, p.magic):
            direction = "BUY" if p.type == 0 else "SELL"
            positions.append({
                "ticket": p.ticket,
                "magic": p.magic,
                "symbol": p.symbol,
                "direction": direction,
                "volume": p.volume,
                "open_time": datetime.fromtimestamp(p.time, tz=timezone.utc),
                "open_price": p.price_open,
                "current_price": p.price_current,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "comment": p.comment,
                "session": parse_comment_session(p.comment)
            })
    
    positions.sort(key=lambda x: x["open_time"])
    return positions

def analyze_by_date(positions):
    """Analyze positions by date"""
    by_date = defaultdict(list)
    for p in positions:
        # Handle both datetime and string formats
        open_time = p["open_time"]
        if isinstance(open_time, str):
            open_time = datetime.fromisoformat(open_time)
        date_key = open_time.date()
        by_date[date_key].append(p)
    
    results = {}
    for date, pos_list in sorted(by_date.items()):
        gross = sum(p["profit"] for p in pos_list)
        net = sum(p["net_pl"] for p in pos_list)
        winners = sum(1 for p in pos_list if p["net_pl"] > 0)
        
        results[str(date)] = {
            "count": len(pos_list),
            "gross": gross,
            "net": net,
            "winners": winners,
            "win_rate": winners / len(pos_list) * 100 if pos_list else 0
        }
    
    return results

def save_to_json(positions, open_positions, output_file):
    """Save positions to JSON"""
    gu_positions = [p for p in positions if p["is_gu"]]
    
    # Convert datetime to ISO format
    for p in gu_positions:
        p["open_time"] = p["open_time"].isoformat()
        p["close_time"] = p["close_time"].isoformat()
    
    for p in open_positions:
        p["open_time"] = p["open_time"].isoformat()
    
    data = {
        "fetch_time": datetime.now(timezone.utc).isoformat(),
        "server": mt5.account_info().server if mt5.account_info() else "Unknown",
        "total_positions": len(positions),
        "gu_positions": len(gu_positions),
        "open_gu_positions": len(open_positions),
        "by_date": {str(k): v for k, v in analyze_by_date(gu_positions).items()},
        "closed_positions": gu_positions,
        "open_positions": open_positions
    }
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    return data

def main():
    if not connect_mt5("MT5_TERMINAL_VANTAGE"):
        print("Failed to connect to Vantage")
        return
    
    try:
        # Fetch last 30 days
        date_to = datetime.now(timezone.utc) + timedelta(days=1)
        date_from = date_to - timedelta(days=30)
        
        print(f"\nFetching positions from {date_from.date()} to {date_to.date()}...")
        print(f"Criteria: Comment contains 'GU_' or magic starts with '282603'")
        
        positions = fetch_all_positions(date_from, date_to)
        gu_positions = [p for p in positions if p["is_gu"]]
        
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total positions (all): {len(positions)}")
        print(f"GU positions: {len(gu_positions)}")
        
        if gu_positions:
            total_gross = sum(p["profit"] for p in gu_positions)
            total_net = sum(p["net_pl"] for p in gu_positions)
            winners = sum(1 for p in gu_positions if p["net_pl"] > 0)
            
            print(f"\nP&L:")
            print(f"  Gross: ${total_gross:,.2f}")
            print(f"  Net: ${total_net:,.2f}")
            print(f"  Win Rate: {winners/len(gu_positions)*100:.1f}%")
            
            # By date
            print(f"\nBy Date:")
            by_date = analyze_by_date(gu_positions)
            for date, stats in sorted(by_date.items()):
                print(f"  {date}: {stats['count']} trades | Net: ${stats['net']:,.2f} | WR: {stats['win_rate']:.0f}%")
        
        # Open positions
        print(f"\n{'='*70}")
        print("OPEN GU POSITIONS")
        print(f"{'='*70}")
        open_pos = fetch_open_positions()
        if open_pos:
            for p in open_pos:
                print(f"  {p['ticket']}: {p['direction']} {p['volume']} lots @ {p['open_price']:.2f} | {p['comment']}")
        else:
            print("  None")
        
        # Save
        output_file = os.path.join(os.path.dirname(__file__), "gu_positions_vantage.json")
        data = save_to_json(positions, open_pos, output_file)
        print(f"\nSaved to: {output_file}")
        
        return data
        
    finally:
        mt5.shutdown()
        print("\nDisconnected")

if __name__ == "__main__":
    main()
