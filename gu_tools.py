import MetaTrader5 as mt5
import os
import sys
import argparse
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

def connect_mt5(terminal_path=None):
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
    magic_str = str(magic)
    if not magic_str.startswith("282603"):
        return "UNKNOWN", "UNKNOWN"
    try:
        strat_id = magic_str[6]
        session_id = magic_str[7]
        strategies = {"0": "TESTS", "1": "HR10", "2": "HR05", "3": "MH"}
        sessions = {"1": "ASIA", "2": "LONDON", "3": "NY", "4": "SESS_4", "5": "SESS_5"}
        return strategies.get(strat_id, f"STRAT_{strat_id}"), sessions.get(session_id, f"SESS_{session_id}")
    except IndexError:
        return "VARIOUS", "VARIOUS"

def fetch_positions(date_from, date_to, magic_filter=None):
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        return []
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
            if magic_filter and entry_deal.magic not in magic_filter:
                continue
            strat, sess = parse_magic(entry_deal.magic)
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            positions.append({
                "pos_id": pid, "magic": entry_deal.magic, "strategy": strat, "session": sess,
                "symbol": entry_deal.symbol, "direction": direction, "volume": entry_deal.volume,
                "open_time": datetime.fromtimestamp(entry_deal.time, tz=timezone.utc),
                "close_time": datetime.fromtimestamp(exit_deal.time, tz=timezone.utc),
                "open_price": entry_deal.price, "close_price": exit_deal.price,
                "profit": exit_deal.profit, "commission": entry_deal.commission + exit_deal.commission,
                "swap": exit_deal.swap, "net_pl": exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap,
                "lot_size": entry_deal.volume, "comment": entry_deal.comment
            })
    positions.sort(key=lambda x: x["open_time"])
    return positions

def analyze_performance(positions):
    if not positions:
        return None
    n = len(positions)
    gross_profit = sum(p["profit"] for p in positions)
    comm = sum(p["commission"] for p in positions)
    swap = sum(p["swap"] for p in positions)
    net_pl = gross_profit + comm + swap
    winners = [p for p in positions if p["net_pl"] > 0]
    losers = [p for p in positions if p["net_pl"] < 0]
    w_count, l_count = len(winners), len(losers)
    win_rate = (w_count / n) * 100 if n > 0 else 0
    avg_win = sum(p["net_pl"] for p in winners) / w_count if w_count > 0 else 0
    avg_loss = sum(p["net_pl"] for p in losers) / l_count if l_count > 0 else 0
    reward_risk = abs(avg_win / avg_loss) if l_count > 0 and avg_loss != 0 else float('inf')
    expectancy = (win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss)
    avg_lot = sum(p.get("lot_size", 0.01) for p in positions) / n if n > 0 else 0.01
    lot_norm = avg_lot * 100
    return {
        "trades": n, "buys": sum(1 for p in positions if p["direction"] == "BUY"),
        "sells": sum(1 for p in positions if p["direction"] == "SELL"),
        "gross_profit": gross_profit, "commission": comm, "swap": swap, "net_pl": net_pl,
        "net_pl_normalized": net_pl / lot_norm if lot_norm > 0 else net_pl,
        "winners": w_count, "losers": l_count,
        "win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss,
        "reward_risk": reward_risk, "expectancy": expectancy,
        "avg_lot_size": avg_lot
    }

def run_analysis_comprehensive(target_date_str):
    """Run comprehensive time window x ATR multiplier analysis."""
    import subprocess
    print("=" * 80)
    print("COMPREHENSIVE ANALYSIS: Time Window x ATR Multiplier Matrix")
    print("=" * 80)
    print(f"\nRunning analysis for date: {target_date_str}")
    print("Executing: data/comprehensive_analysis.py\n")
    result = subprocess.run(['python', 'data/comprehensive_analysis.py', '--date', target_date_str])
    if result.returncode != 0:
        print("\nError running comprehensive analysis")

def run_analysis_risk_adjusted(target_date_str):
    """Run risk-adjusted analysis with MAE dimension."""
    import subprocess
    print("=" * 80)
    print("RISK-ADJUSTED ANALYSIS: Total Outcome / Max MAE Ratio")
    print("=" * 80)
    print(f"\nRunning analysis for date: {target_date_str}")
    print("Executing: data/risk_adjusted_analysis.py\n")
    result = subprocess.run(['python', 'data/risk_adjusted_analysis.py', '--date', target_date_str])
    if result.returncode != 0:
        print("\nError running risk-adjusted analysis")

def main():
    parser = argparse.ArgumentParser(description='GU Trading Tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    perf_parser = subparsers.add_parser('performance', help='Analyze performance for a date')
    perf_parser.add_argument('date', help='Date to analyze (YYYY-MM-DD)')
    
    list_parser = subparsers.add_parser('list', help='List positions for a date')
    list_parser.add_argument('date', help='Date to list (YYYY-MM-DD)')
    
    # Analysis commands
    comp_parser = subparsers.add_parser('comprehensive-analysis', 
        help='Run comprehensive time x multiplier analysis (54 configs)')
    comp_parser.add_argument('--date', default=None, help='Date to analyze (YYYY-MM-DD), defaults to today')
    
    risk_parser = subparsers.add_parser('risk-adjusted-analysis',
        help='Run risk-adjusted analysis with MAE dimension')
    risk_parser.add_argument('--date', default=None, help='Date to analyze (YYYY-MM-DD), defaults to today')
    
    args = parser.parse_args()
    
    if args.command == 'performance':
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        date_from = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        date_to = date_from + timedelta(days=1)
        if connect_mt5():
            positions = fetch_positions(date_from, date_to)
            if positions:
                m = analyze_performance(positions)
                print(f"\nPerformance for {args.date}:")
                print(f"  Trades: {m['trades']} ({m['buys']} buys, {m['sells']} sells)")
                print(f"  Net P/L: ${m['net_pl']:.2f}")
                print(f"  Win Rate: {m['win_rate']:.1f}% ({m['winners']}/{m['losers']})")
                print(f"  Expectancy: ${m['expectancy']:.2f}")
            else:
                print("No positions found")
            mt5.shutdown()
    
    elif args.command == 'list':
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        date_from = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        date_to = date_from + timedelta(days=1)
        if connect_mt5():
            positions = fetch_positions(date_from, date_to)
            print(f"\nPositions for {args.date}:")
            for p in positions:
                print(f"  {p['pos_id']}: {p['direction']} {p['strategy']}/{p['session']} ${p['net_pl']:.2f}")
            mt5.shutdown()
    
    elif args.command == 'comprehensive-analysis':
        date_str = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
        run_analysis_comprehensive(date_str)
    
    elif args.command == 'risk-adjusted-analysis':
        date_str = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
        run_analysis_risk_adjusted(date_str)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
