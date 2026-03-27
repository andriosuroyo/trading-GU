"""
Fetch complete trade history from Vantage Demo (PRIMARY data source)
Targets: All GU magic numbers (282603xx range) with full position lifecycle data
"""
import MetaTrader5 as mt5
import os
import sys
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

def load_env():
    """Load environment variables from .env file."""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars

def connect_mt5():
    """Connect to Vantage MT5 terminal."""
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    
    if not terminal_path or not os.path.exists(terminal_path):
        print(f"Error: Vantage terminal not found at {terminal_path}")
        return False
        
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize() failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
        
    info = mt5.account_info()
    if info:
        print(f"=" * 80)
        print(f"CONNECTED: {info.server}")
        print(f"Account: {info.login} | Name: {info.name}")
        print(f"Balance: ${info.balance:.2f} | Equity: ${info.equity:.2f}")
        print(f"=" * 80)
        return True
    return False

def parse_magic_number(magic):
    """Parse magic number to extract strategy and session information."""
    magic_str = str(int(magic)) if magic else ""
    
    # Check if it's a GU magic number (282603xx format)
    if not magic_str.startswith("282603"):
        return {"raw": magic, "strategy": "NON_GU", "session": "UNKNOWN", 
                "strategy_id": None, "session_id": None}
    
    try:
        strategy_id = magic_str[6]  # 7th digit
        session_id = magic_str[7]   # 8th digit
        
        strategies = {
            "0": "TESTS",
            "1": "HR10", 
            "2": "HR05",
            "3": "MH"
        }
        
        sessions = {
            "0": "FULL",
            "1": "ASIA",
            "2": "LONDON", 
            "3": "NY",
            "4": "SESS_4",
            "5": "SESS_5"
        }
        
        return {
            "raw": magic,
            "strategy": strategies.get(strategy_id, f"STRAT_{strategy_id}"),
            "session": sessions.get(session_id, f"SESS_{session_id}"),
            "strategy_id": strategy_id,
            "session_id": session_id
        }
    except (IndexError, ValueError):
        return {"raw": magic, "strategy": "UNKNOWN", "session": "UNKNOWN",
                "strategy_id": None, "session_id": None}

def fetch_all_positions(date_from, date_to):
    """
    Fetch all historical closed positions from MT5 between date_from and date_to.
    Matches DEAL_ENTRY_IN with DEAL_ENTRY_OUT by position_id.
    """
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        print(f"No deals found between {date_from} and {date_to}")
        return []
        
    print(f"\nTotal raw deals found: {len(deals)}")
    
    # Group by position_id
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    positions = []
    
    for pid, siblings in deals_by_pos.items():
        entry_deal = None
        exit_deal = None
        
        for s in siblings:
            if s.entry == 0:  # DEAL_ENTRY_IN
                entry_deal = s
            elif s.entry == 1:  # DEAL_ENTRY_OUT
                exit_deal = s
                
        if entry_deal and exit_deal:
            magic_info = parse_magic_number(entry_deal.magic)
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            
            # Calculate duration
            duration_seconds = exit_deal.time - entry_deal.time
            duration_minutes = duration_seconds / 60
            
            positions.append({
                "pos_id": pid,
                "magic": entry_deal.magic,
                "strategy": magic_info["strategy"],
                "session": magic_info["session"],
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
                "comment": entry_deal.comment
            })
    
    # Sort by open time
    positions.sort(key=lambda x: x["open_time"])
    return positions

def fetch_open_positions():
    """Fetch currently open positions."""
    open_pos = mt5.positions_get()
    if not open_pos:
        return []
    
    positions = []
    for p in open_pos:
        magic_info = parse_magic_number(p.magic)
        direction = "BUY" if p.type == 0 else "SELL"
        
        positions.append({
            "ticket": p.ticket,
            "magic": p.magic,
            "strategy": magic_info["strategy"],
            "session": magic_info["session"],
            "symbol": p.symbol,
            "direction": direction,
            "volume": p.volume,
            "open_time": datetime.fromtimestamp(p.time, tz=timezone.utc),
            "open_price": p.price_open,
            "current_price": p.price_current,
            "sl": p.sl,
            "tp": p.tp,
            "profit": p.profit,
            "comment": p.comment
        })
    
    positions.sort(key=lambda x: x["open_time"])
    return positions

def analyze_by_session(positions):
    """Analyze positions grouped by session."""
    sessions = defaultdict(list)
    for p in positions:
        sessions[p["session"]].append(p)
    
    results = {}
    for session, pos_list in sessions.items():
        if not pos_list:
            continue
            
        gross_profit = sum(p["profit"] for p in pos_list)
        total_comm = sum(p["commission"] for p in pos_list)
        total_swap = sum(p["swap"] for p in pos_list)
        net_pl = gross_profit + total_comm + total_swap
        
        winners = [p for p in pos_list if p["net_pl"] > 0]
        losers = [p for p in pos_list if p["net_pl"] < 0]
        
        avg_lot = sum(p["volume"] for p in pos_list) / len(pos_list)
        
        results[session] = {
            "count": len(pos_list),
            "gross_profit": gross_profit,
            "commission": total_comm,
            "swap": total_swap,
            "net_pl": net_pl,
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": len(winners) / len(pos_list) * 100 if pos_list else 0,
            "avg_profit": gross_profit / len(pos_list),
            "avg_duration_min": sum(p["duration_minutes"] for p in pos_list) / len(pos_list),
            "avg_lot_size": avg_lot
        }
    
    return results

def analyze_by_strategy(positions):
    """Analyze positions grouped by strategy."""
    strategies = defaultdict(list)
    for p in positions:
        strategies[p["strategy"]].append(p)
    
    results = {}
    for strategy, pos_list in strategies.items():
        if not pos_list or strategy == "NON_GU":
            continue
            
        gross_profit = sum(p["profit"] for p in pos_list)
        total_comm = sum(p["commission"] for p in pos_list)
        total_swap = sum(p["swap"] for p in pos_list)
        net_pl = gross_profit + total_comm + total_swap
        
        winners = [p for p in pos_list if p["net_pl"] > 0]
        losers = [p for p in pos_list if p["net_pl"] < 0]
        
        results[strategy] = {
            "count": len(pos_list),
            "net_pl": net_pl,
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": len(winners) / len(pos_list) * 100 if pos_list else 0,
            "avg_profit": gross_profit / len(pos_list)
        }
    
    return results

def save_to_json(positions, open_positions, output_file):
    """Save positions to JSON file."""
    # Convert datetime to ISO format for JSON serialization
    serializable_closed = []
    for p in positions:
        p_copy = p.copy()
        p_copy["open_time"] = p["open_time"].isoformat()
        p_copy["close_time"] = p["close_time"].isoformat()
        serializable_closed.append(p_copy)
    
    serializable_open = []
    for p in open_positions:
        p_copy = p.copy()
        p_copy["open_time"] = p["open_time"].isoformat()
        serializable_open.append(p_copy)
    
    data = {
        "fetch_time": datetime.now(timezone.utc).isoformat(),
        "total_closed": len(positions),
        "total_open": len(open_positions),
        "session_analysis": analyze_by_session(positions),
        "strategy_analysis": analyze_by_strategy(positions),
        "closed_positions": serializable_closed,
        "open_positions": serializable_open
    }
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    return data

def main():
    if not connect_mt5():
        sys.exit(1)
    
    try:
        # Fetch last 14 days of history by default
        date_to = datetime.now(timezone.utc) + timedelta(days=1)  # Include today
        date_from = date_to - timedelta(days=30)  # Last 30 days
        
        print(f"\nFetching position history from {date_from.date()} to {date_to.date()}...")
        
        # Fetch closed positions
        positions = fetch_all_positions(date_from, date_to)
        
        # Filter to GU magic numbers only
        gu_positions = [p for p in positions if str(p["magic"]).startswith("282603")]
        
        print(f"\n{'='*80}")
        print("CLOSED POSITIONS SUMMARY")
        print(f"{'='*80}")
        print(f"Total positions (all magics): {len(positions)}")
        print(f"GU strategy positions (282603xx): {len(gu_positions)}")
        
        if gu_positions:
            total_gross = sum(p["profit"] for p in gu_positions)
            total_comm = sum(p["commission"] for p in gu_positions)
            total_swap = sum(p["swap"] for p in gu_positions)
            net_pl = total_gross + total_comm + total_swap
            
            winners = [p for p in gu_positions if p["net_pl"] > 0]
            losers = [p for p in gu_positions if p["net_pl"] < 0]
            
            print(f"\nOverall P&L:")
            print(f"  Gross Profit: ${total_gross:,.2f}")
            print(f"  Commission:   ${total_comm:,.2f}")
            print(f"  Swap:         ${total_swap:,.2f}")
            print(f"  Net P/L:      ${net_pl:,.2f}")
            print(f"\nWin/Loss:")
            print(f"  Winners: {len(winners)} | Losers: {len(losers)}")
            print(f"  Win Rate: {len(winners)/len(gu_positions)*100:.1f}%")
            
            # Session breakdown
            print(f"\n{'='*80}")
            print("SESSION BREAKDOWN")
            print(f"{'='*80}")
            session_stats = analyze_by_session(gu_positions)
            for session, stats in sorted(session_stats.items()):
                print(f"\n{session}:")
                print(f"  Trades: {stats['count']} | Net P/L: ${stats['net_pl']:,.2f}")
                print(f"  Win Rate: {stats['win_rate']:.1f}% | Avg Duration: {stats['avg_duration_min']:.1f} min")
            
            # Strategy breakdown
            print(f"\n{'='*80}")
            print("STRATEGY BREAKDOWN")
            print(f"{'='*80}")
            strategy_stats = analyze_by_strategy(gu_positions)
            for strategy, stats in sorted(strategy_stats.items()):
                print(f"\n{strategy}:")
                print(f"  Trades: {stats['count']} | Net P/L: ${stats['net_pl']:,.2f}")
                print(f"  Win Rate: {stats['win_rate']:.1f}%")
        
        # Fetch open positions
        print(f"\n{'='*80}")
        print("CURRENTLY OPEN POSITIONS")
        print(f"{'='*80}")
        open_positions = fetch_open_positions()
        gu_open = [p for p in open_positions if str(p["magic"]).startswith("282603")]
        
        if gu_open:
            print(f"Open GU positions: {len(gu_open)}")
            for p in gu_open:
                print(f"  {p['ticket']}: {p['direction']} {p['volume']} lots {p['symbol']} @ {p['open_price']:.2f} | "
                      f"P/L: ${p['profit']:.2f} | {p['strategy']} {p['session']}")
        else:
            print("No open GU positions")
        
        # Save to JSON
        output_file = os.path.join(os.path.dirname(__file__), "vantage_trade_history.json")
        data = save_to_json(gu_positions, gu_open, output_file)
        print(f"\nData saved to: {output_file}")
        
        return data
        
    finally:
        mt5.shutdown()
        print("\nDisconnected from MT5")

if __name__ == "__main__":
    main()
