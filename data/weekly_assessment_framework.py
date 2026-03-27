"""
Weekly Assessment Framework for GU FULL Mode Strategy
Tracks ATR-based TP, time-exit patterns, and MA performance relationships
"""
import MetaTrader5 as mt5
import pandas as pd
import json
import os
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

def connect_mt5():
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    print(f"Connected: {info.server} | Account: {info.login}")
    return True

def detect_session(utc_time):
    """Detect trading session based on UTC hour"""
    hour = utc_time.hour
    # Using UTC times from knowledge base
    if 2 <= hour < 6:
        return "ASIA"
    elif 8 <= hour < 12:
        return "LONDON"
    elif 17 <= hour < 21:
        return "NY"
    else:
        return "OFF_SESSION"

def analyze_exit_pattern(duration_minutes):
    """Categorize exit based on duration"""
    if duration_minutes < 1.5:
        return "VERY_EARLY"
    elif 1.5 <= duration_minutes < 2.5:
        return "PARTIAL_CLOSE_TARGET"
    elif 2.5 <= duration_minutes < 4.5:
        return "MID_RANGE"
    elif 4.5 <= duration_minutes < 6:
        return "FULL_CLOSE_TARGET"
    else:
        return "EXTENDED"

def fetch_weekly_data(week_start_date):
    """Fetch all GU positions for a specific week"""
    week_end = week_start_date + timedelta(days=7, hours=1)  # Add buffer
    
    print(f"Fetching deals from {week_start_date} to {week_end}")
    deals = mt5.history_deals_get(week_start_date, week_end)
    print(f"Raw deals returned: {len(deals) if deals else 0}")
    if not deals:
        return []
    
    # Group ALL deals by position_id first
    by_pos = defaultdict(list)
    for d in deals:
        by_pos[d.position_id].append(d)
    
    positions = []
    for pid, siblings in by_pos.items():
        entry = None
        exit_deal = None
        for s in siblings:
            if s.entry == 0:
                entry = s
            elif s.entry == 1:
                exit_deal = s
        
        # Check if GU position by comment (check entry deal)
        if entry and exit_deal and entry.comment and "GU_" in entry.comment.upper():
            open_time = datetime.fromtimestamp(entry.time, tz=timezone.utc)
            close_time = datetime.fromtimestamp(exit_deal.time, tz=timezone.utc)
            duration = (close_time - open_time).total_seconds() / 60
            
            positions.append({
                'pos_id': pid,
                'magic': entry.magic,
                'strategy': parse_magic(entry.magic),
                'session': detect_session(open_time),
                'direction': 'BUY' if entry.type == 0 else 'SELL',
                'volume': entry.volume,
                'open_time': open_time,
                'close_time': close_time,
                'duration_min': duration,
                'exit_pattern': analyze_exit_pattern(duration),
                'open_price': entry.price,
                'close_price': exit_deal.price,
                'gross_pl': exit_deal.profit,
                'commission': entry.commission + exit_deal.commission,
                'net_pl': exit_deal.profit + entry.commission + exit_deal.commission,
                'comment': entry.comment
            })
    
    positions.sort(key=lambda x: x['open_time'])
    return positions

def parse_magic(magic):
    """Parse magic to strategy name - handles both 2-digit and 8-digit formats"""
    magic_str = str(int(magic)) if magic else ""
    
    # 8-digit format: 282603xx
    if magic_str.startswith("282603"):
        strategy_id = magic_str[6] if len(magic_str) > 6 else "?"
        strategies = {"0": "TESTS", "1": "HR10", "2": "HR05", "3": "MH"}
        return strategies.get(strategy_id, f"STRAT_{strategy_id}")
    
    # 2-digit format: 10, 11, 12, 13, 20, 21, 22, 23, 30, 31, 32, 33
    if magic_str in ["10", "11", "12", "13"]:
        return "MH"  # MA 20/80
    elif magic_str in ["20", "21", "22", "23"]:
        return "HR10"  # MA 10/40
    elif magic_str in ["30", "31", "32", "33"]:
        return "HR05"  # MA 5/20
    
    return f"OTHER_{magic_str}"

def generate_weekly_report(positions, week_start):
    """Generate comprehensive weekly assessment report"""
    if not positions:
        return {"error": "No positions found"}
    
    report = {
        'week_start': week_start.isoformat(),
        'week_end': (week_start + timedelta(days=7)).isoformat(),
        'total_positions': len(positions),
        'summary': {},
        'by_strategy': {},
        'by_session': {},
        'exit_pattern_analysis': {},
        'daily_breakdown': {}
    }
    
    # Overall summary
    total_gross = sum(p['gross_pl'] for p in positions)
    total_net = sum(p['net_pl'] for p in positions)
    total_comm = sum(p['commission'] for p in positions)
    winners = sum(1 for p in positions if p['net_pl'] > 0)
    
    report['summary'] = {
        'gross_pl': round(total_gross, 2),
        'commission': round(total_comm, 2),
        'net_pl': round(total_net, 2),
        'winners': winners,
        'losers': len(positions) - winners,
        'win_rate': round(winners / len(positions) * 100, 1),
        'avg_duration': round(sum(p['duration_min'] for p in positions) / len(positions), 1)
    }
    
    # By strategy (MA relationship analysis)
    by_strategy = defaultdict(list)
    for p in positions:
        by_strategy[p['strategy']].append(p)
    
    for strategy, pos_list in by_strategy.items():
        net = sum(p['net_pl'] for p in pos_list)
        wins = sum(1 for p in pos_list if p['net_pl'] > 0)
        report['by_strategy'][strategy] = {
            'count': len(pos_list),
            'net_pl': round(net, 2),
            'win_rate': round(wins / len(pos_list) * 100, 1),
            'avg_duration': round(sum(p['duration_min'] for p in pos_list) / len(pos_list), 1),
            'frequency_pct': round(len(pos_list) / len(positions) * 100, 1)
        }
    
    # By session (for upcoming session-specific TCM analysis)
    by_session = defaultdict(list)
    for p in positions:
        by_session[p['session']].append(p)
    
    for session, pos_list in by_session.items():
        net = sum(p['net_pl'] for p in pos_list)
        wins = sum(1 for p in pos_list if p['net_pl'] > 0)
        report['by_session'][session] = {
            'count': len(pos_list),
            'net_pl': round(net, 2),
            'win_rate': round(wins / len(pos_list) * 100, 1),
            'avg_duration': round(sum(p['duration_min'] for p in pos_list) / len(pos_list), 1)
        }
    
    # Exit pattern analysis (time-based SL assessment)
    by_exit = defaultdict(list)
    for p in positions:
        by_exit[p['exit_pattern']].append(p)
    
    for pattern, pos_list in by_exit.items():
        net = sum(p['net_pl'] for p in pos_list)
        wins = sum(1 for p in pos_list if p['net_pl'] > 0)
        report['exit_pattern_analysis'][pattern] = {
            'count': len(pos_list),
            'pct_of_total': round(len(pos_list) / len(positions) * 100, 1),
            'net_pl': round(net, 2),
            'win_rate': round(wins / len(pos_list) * 100, 1),
            'avg_pl': round(net / len(pos_list), 2)
        }
    
    # Daily breakdown
    by_day = defaultdict(list)
    for p in positions:
        day = p['open_time'].strftime('%Y-%m-%d')
        by_day[day].append(p)
    
    for day, pos_list in sorted(by_day.items()):
        net = sum(p['net_pl'] for p in pos_list)
        wins = sum(1 for p in pos_list if p['net_pl'] > 0)
        report['daily_breakdown'][day] = {
            'count': len(pos_list),
            'net_pl': round(net, 2),
            'win_rate': round(wins / len(pos_list) * 100, 1)
        }
    
    return report

def main():
    """Run assessment for current/previous week"""
    print("=" * 70)
    print("GU STRATEGY - WEEKLY ASSESSMENT FRAMEWORK")
    print("=" * 70)
    
    if not connect_mt5():
        return
    
    try:
        # Analyze March 20 week (Mar 16-22)
        week_start = datetime(2026, 3, 16, tzinfo=timezone.utc)
        
        print(f"\nAnalyzing week: {week_start.date()} to {(week_start + timedelta(days=7)).date()}")
        
        positions = fetch_weekly_data(week_start)
        print(f"Positions found: {len(positions)}")
        
        if positions:
            report = generate_weekly_report(positions, week_start)
            
            # Print summary
            print("\n" + "=" * 70)
            print("WEEKLY SUMMARY")
            print("=" * 70)
            s = report['summary']
            print(f"Total Positions: {report['total_positions']}")
            print(f"Net P/L: ${s['net_pl']:.2f} (Gross: ${s['gross_pl']:.2f}, Comm: ${s['commission']:.2f})")
            print(f"Win Rate: {s['winners']}/{report['total_positions']} ({s['win_rate']:.1f}%)")
            print(f"Avg Duration: {s['avg_duration']:.1f} min")
            
            # Strategy breakdown
            print("\n" + "=" * 70)
            print("BY STRATEGY (MA Relationship)")
            print("=" * 70)
            print(f"{'Strategy':<10} {'Count':>8} {'Freq%':>8} {'Net P/L':>12} {'Win%':>8} {'AvgDur':>8}")
            print("-" * 70)
            for strat, data in sorted(report['by_strategy'].items()):
                print(f"{strat:<10} {data['count']:>8} {data['frequency_pct']:>7.1f}% ${data['net_pl']:>10.2f} {data['win_rate']:>7.1f}% {data['avg_duration']:>7.1f}m")
            
            # Exit pattern analysis
            print("\n" + "=" * 70)
            print("EXIT PATTERN ANALYSIS (Time-Based SL Assessment)")
            print("=" * 70)
            print(f"{'Pattern':<20} {'Count':>8} {'Pct':>8} {'Net P/L':>12} {'Win%':>8} {'Avg P/L':>10}")
            print("-" * 70)
            for pattern, data in sorted(report['exit_pattern_analysis'].items()):
                print(f"{pattern:<20} {data['count']:>8} {data['pct_of_total']:>7.1f}% ${data['net_pl']:>10.2f} {data['win_rate']:>7.1f}% ${data['avg_pl']:>9.2f}")
            
            # Save report
            output_file = f"data/weekly_report_{week_start.strftime('%Y%m%d')}.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nFull report saved to: {output_file}")
            
            return report
    
    finally:
        mt5.shutdown()
        print("\nDisconnected")

if __name__ == "__main__":
    main()
