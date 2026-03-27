import sys
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Add parent directory to path to import gu_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import gu_tools

def generate_report():
    if not gu_tools.connect_mt5():
        print("Failed to connect to MT5.")
        return

    # Default to yesterday
    now = datetime.now(timezone.utc)
    # Calculate yesterday's boundaries (00:00:00 to 23:59:59)
    # We use server time conceptually, but fetch deals in UTC
    yesterday_date = (now - timedelta(days=1)).date()
    
    # If user provided a date arg (YYYY-MM-DD), use it
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
            date_from = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")
            return
    else:
        target_date = yesterday_date
        date_from = datetime.combine(yesterday_date, datetime.min.time(), tzinfo=timezone.utc)
        
    date_to = date_from + timedelta(days=1)
    
    print(f"# GU Daily Performance Report: {target_date}")
    print(f"**Data Period:** {date_from.strftime('%Y-%m-%d %H:%M:%S UTC')} to {date_to.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

    deals = gu_tools.mt5.history_deals_get(date_from, date_to)
    if not deals:
        print("No trading activity found for this period.")
        gu_tools.mt5.shutdown()
        return
        
    positions = gu_tools.fetch_positions(date_from, date_to)
    
    # Filter only GU magic numbers (282603xx)
    gu_positions = [p for p in positions if str(p['magic']).startswith("282603")]
    
    if not gu_positions:
        print("No GU-specific closed positions found for this period.")
        gu_tools.mt5.shutdown()
        return
        
    # Group by Strategy -> Session
    grouped = defaultdict(lambda: defaultdict(list))
    for p in gu_positions:
        grouped[p['strategy']][p['session']].append(p)
        
    # Overall performance
    overall = gu_tools.analyze_performance(gu_positions)
    
    print("## Executive Summary\n")
    print(f"- **Total Positions:** {overall['trades']}")
    print(f"- **Net P/L:** ${overall['net_pl']:.2f}")
    if overall['trades'] > 0:
        print(f"- **Win Rate:** {overall['win_rate']:.1f}% ({overall['winners']}W / {overall['losers']}L)")
        print(f"- **Average Trade:** ${overall['net_pl'] / overall['trades']:.2f}")
    
    print("\n## Strategy Breakdown\n")
    
    for strat in ["TESTS", "MH", "HR10", "HR05"]:
        if strat not in grouped:
            continue
            
        print(f"### Strategy: {strat}\n")
        print("| Session | Trades | Net P/L | Win Rate | W/L | Avg Win | Avg Loss | R/R |")
        print("|---|---|---|---|---|---|---|---|")
        
        strat_total_pos = []
        for sess in ["ASIA", "LONDON", "NY"]:
            sess_pos = grouped[strat].get(sess, [])
            if not sess_pos:
                continue
                
            strat_total_pos.extend(sess_pos)
            perf = gu_tools.analyze_performance(sess_pos)
            
            rr_str = f"{perf['reward_risk']:.2f}" if perf['reward_risk'] != float('inf') else "N/A"
            print(f"| {sess} | {perf['trades']} | ${perf['net_pl']:.2f} | {perf['win_rate']:.1f}% | {perf['winners']}/{perf['losers']} | ${perf['avg_win']:.2f} | ${perf['avg_loss']:.2f} | {rr_str} |")
            
        # Strategy overall
        if strat_total_pos:
            st_perf = gu_tools.analyze_performance(strat_total_pos)
            rr_str = f"{st_perf['reward_risk']:.2f}" if st_perf['reward_risk'] != float('inf') else "N/A"
            print(f"| **TOTAL** | **{st_perf['trades']}** | **${st_perf['net_pl']:.2f}** | **{st_perf['win_rate']:.1f}%** | **{st_perf['winners']}/{st_perf['losers']}** | | | |")
        
        print("\n")
        
    # Anomaly Detection / Notes
    print("## Risk & Anomaly Flags\n")
    flags = []
    
    for strat, sessions in grouped.items():
        for sess, pos in sessions.items():
            perf = gu_tools.analyze_performance(pos)
            
            # High SL hit rate (assuming avg loss tracks SL)
            if perf['win_rate'] < 50 and perf['trades'] >= 5:
                flags.append(f"⚠️ **{strat} {sess}**: Poor win rate ({perf['win_rate']:.1f}% across {perf['trades']} trades). Bleeding P/L (${perf['net_pl']:.2f}).")
                
            # Severe negative R/R (scalping inverse R/R is normal, but watch out for extremes)
            if perf['reward_risk'] < 0.1 and perf['losers'] >= 3:
                flags.append(f"⚠️ **{strat} {sess}**: High risk asymmetry (R/R {perf['reward_risk']:.2f}). Avg win is ${perf['avg_win']:.2f} vs avg loss ${perf['avg_loss']:.2f}.")
                
            # Volume anomaly (TESTS should have many, others maybe not)
            if strat != "TESTS" and perf['trades'] > 50:
                flags.append(f"ℹ️ **{strat} {sess}**: Unusually high trade volume ({perf['trades']} trades). Ensure no signaling loop.")
                
    if not flags:
        print("No immediate statistical anomalies detected in yesterday's data.")
    else:
        for f in flags:
            print("- " + f)
            
    gu_tools.mt5.shutdown()

if __name__ == "__main__":
    generate_report()
