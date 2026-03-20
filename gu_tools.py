import MetaTrader5 as mt5
import os
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

def load_env():
    """Load paths from .env file."""
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

def connect_mt5(terminal_path=None):
    """Connect to MT5 terminal."""
    if not terminal_path:
        env_vars = load_env()
        terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    
    if not terminal_path or not os.path.exists(terminal_path):
        print(f"Error: MT5 terminal path not found: {terminal_path}")
        return False
        
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize() failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
        
    info = mt5.account_info()
    if info:
        print(f"Connected to: {info.server} | Account: {info.login}")
        return True
    return False

def parse_magic(magic):
    """Parse magic number to strategy and session names."""
    magic_str = str(magic)
    if not magic_str.startswith("282603"):
        return "UNKNOWN", "UNKNOWN"
        
    try:
        strat_id = magic_str[6]
        session_id = magic_str[7]
        
        strategies = {
            "0": "TESTS",
            "1": "HR10",
            "2": "HR05",
            "3": "MH"
        }
        
        sessions = {
            "1": "ASIA",
            "2": "LONDON",
            "3": "NY",
            "4": "SESS_4",
            "5": "SESS_5"
        }
        
        strat = strategies.get(strat_id, f"STRAT_{strat_id}")
        sess = sessions.get(session_id, f"SESS_{session_id}")
        return strat, sess
    except IndexError:
        return "VARIOUS", "VARIOUS"

def fetch_positions(date_from, date_to, magic_filter=None):
    """
    Fetch all historical closed positions from MT5 between date_from and date_to.
    Matches DEAL_ENTRY_IN with DEAL_ENTRY_OUT by position_id.
    Returns: list of dicts representing closed positions.
    """
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        return []
        
    # Group by position_id
    deals_by_pos = defaultdict(list)
    for d in deals:
        # If magic_filter is provided, only include deals belonging to those magics.
        # But we must group all siblings of a position_id if at least one matches.
        # Actually, mt5 deal gets magic on both IN and OUT, so we can filter later.
        deals_by_pos[d.position_id].append(d)
        
    positions = []
    
    for pid, siblings in deals_by_pos.items():
        entry_deal = None
        exit_deal = None
        
        for s in siblings:
            if s.entry == 0: # DEAL_ENTRY_IN
                entry_deal = s
            elif s.entry == 1: # DEAL_ENTRY_OUT
                exit_deal = s
                
        if entry_deal and exit_deal:
            # Check magic filter
            if magic_filter and entry_deal.magic not in magic_filter:
                continue
                
            strat, sess = parse_magic(entry_deal.magic)
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            
            positions.append({
                "pos_id": pid,
                "magic": entry_deal.magic,
                "strategy": strat,
                "session": sess,
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
                "lot_size": entry_deal.volume,
                "comment": entry_deal.comment
            })
            
    # Sort by open time
    positions.sort(key=lambda x: x["open_time"])
    return positions

def analyze_performance(positions):
    """
    Calculate performance metrics for a given list of positions.
    Returns a dict of metrics.
    """
    if not positions:
        return None
        
    n = len(positions)
    gross_profit = sum(p["profit"] for p in positions)
    comm = sum(p["commission"] for p in positions)
    swap = sum(p["swap"] for p in positions)
    net_pl = gross_profit + comm + swap
    
    winners = [p for p in positions if p["net_pl"] > 0]
    losers = [p for p in positions if p["net_pl"] < 0]
    flats = [p for p in positions if p["net_pl"] == 0]
    
    w_count = len(winners)
    l_count = len(losers)
    
    win_rate = (w_count / n) * 100 if n > 0 else 0
    
    avg_win = sum(p["net_pl"] for p in winners) / w_count if w_count > 0 else 0
    avg_loss = sum(p["net_pl"] for p in losers) / l_count if l_count > 0 else 0
    
    reward_risk = abs(avg_win / avg_loss) if l_count > 0 and avg_loss != 0 else float('inf')
    expectancy = (win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss)
    
    # Normalize to 0.01 lot equivalent
    avg_lot = sum(p.get("lot_size", 0.01) for p in positions) / n if n > 0 else 0.01
    lot_normalization_factor = avg_lot * 100  # Convert to 0.01 lot units
    
    return {
        "trades": n,
        "buys": sum(1 for p in positions if p["direction"] == "BUY"),
        "sells": sum(1 for p in positions if p["direction"] == "SELL"),
        "gross_profit": gross_profit,
        "commission": comm,
        "swap": swap,
        "net_pl": net_pl,
        "net_pl_normalized": net_pl / lot_normalization_factor if lot_normalization_factor > 0 else net_pl,
        "winners": w_count,
        "losers": l_count,
        "flats": len(flats),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_win_normalized": avg_win / lot_normalization_factor if lot_normalization_factor > 0 else avg_win,
        "avg_loss_normalized": avg_loss / lot_normalization_factor if lot_normalization_factor > 0 else avg_loss,
        "reward_risk": reward_risk,
        "expectancy": expectancy,
        "expectancy_normalized": expectancy / lot_normalization_factor if lot_normalization_factor > 0 else expectancy,
        "avg_lot_size": avg_lot
    }
