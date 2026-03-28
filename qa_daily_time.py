"""
Daily TimeAnalysis Generator (CommentTag-Based)
Generates {date}_TimeAnalysis.xlsx for time-based SL evaluation

NEW SYSTEM: Uses CommentTag (e.g., "GU_m1052005") not magic number ranges
Organizes by Strategy name, not "Magic11, Magic12"
Session derived from OpenTime

Usage: python qa_daily_time.py --date 2026-03-27
Output: data/20260327_TimeAnalysis.xlsx
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os
import argparse

# Configuration
OUTPUT_DIR = "data"
TIME_WINDOWS = range(1, 31)  # 1-30 minutes
SYMBOL_BB = "XAUUSDp"
ATR_TP_MULTIPLIER = 0.5  # Standard TP = 0.5x ATR


def load_env():
    """Load environment variables."""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars


def connect_mt5_terminal(terminal_key):
    """Connect to MT5 terminal."""
    env_vars = load_env()
    terminal_path = env_vars.get(terminal_key)
    
    if not terminal_path or not os.path.exists(terminal_path):
        print(f"Error: Terminal path not found for {terminal_key}")
        return False
    
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize() failed: {mt5.last_error()}")
        return False
    
    info = mt5.account_info()
    print(f"Connected to: {info.server} | Account: {info.login}")
    return True


def is_gu_position(comment):
    """Check if position is GU strategy based on CommentTag."""
    if comment and "GU_" in str(comment).upper():
        return True
    return False


def get_strategy_name(comment):
    """Extract strategy name from CommentTag."""
    if not comment:
        return "Unknown"
    comment_str = str(comment)
    if "GU_" in comment_str.upper():
        parts = comment_str.split("_")
        if len(parts) >= 2:
            return f"GU_{parts[1]}"
    return "Unknown"


def get_session_from_time(dt):
    """Derive trading session from OpenTime (UTC)."""
    hour = dt.hour
    if 2 <= hour < 6:
        return "Asia"
    elif 8 <= hour < 12:
        return "London"
    elif 17 <= hour < 21:
        return "NY"
    else:
        return "Other"


def fetch_gu_positions(target_date):
    """Fetch GU positions from Vantage using CommentTag filter."""
    date_from = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    date_to = date_from + timedelta(days=1)
    
    print(f"\nFetching positions for {target_date}...")
    
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        return []
    
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    positions = []
    for pid, siblings in deals_by_pos.items():
        entry = None
        exit_d = None
        for s in siblings:
            if s.entry == 0:
                entry = s
            elif s.entry == 1:
                exit_d = s
        
        if entry and exit_d:
            if not is_gu_position(entry.comment):
                continue
            
            direction = "BUY" if entry.type == 0 else "SELL"
            open_time = datetime.utcfromtimestamp(entry.time).replace(tzinfo=timezone.utc)
            
            positions.append({
                "ticket": pid,
                "magic": entry.magic,
                "strategy": get_strategy_name(entry.comment),
                "session": get_session_from_time(open_time),
                "direction": direction,
                "open_time": open_time,
                "close_time": datetime.utcfromtimestamp(exit_d.time).replace(tzinfo=timezone.utc),
                "open_price": entry.price,
                "close_price": exit_d.price,
                "profit": exit_d.profit + entry.commission + entry.commission + exit_d.swap
            })
    
    print(f"GU positions: {len(positions)}")
    return positions


def get_atr_m1_60(target_time):
    """Get ATR(60) from BlackBull."""
    from_time = target_time - timedelta(hours=2)
    rates = mt5.copy_rates_range(SYMBOL_BB, mt5.TIMEFRAME_M1, from_time, target_time)
    
    if rates is None or len(rates) < 60:
        return None
    
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    
    df["high_low"] = df["high"] - df["low"]
    df["high_close"] = abs(df["high"] - df["close"].shift())
    df["low_close"] = abs(df["low"] - df["close"].shift())
    df["tr"] = df[["high_low", "high_close", "low_close"]].max(axis=1)
    df["atr_60"] = df["tr"].rolling(window=60).mean()
    
    df_before = df[df["time"] <= target_time]
    if df_before.empty:
        return None
    
    return df_before["atr_60"].iloc[-1]


def fetch_tick_data(open_time, window_minutes=30):
    """Fetch tick data from BlackBull."""
    window_end = open_time + timedelta(minutes=window_minutes)
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_end + timedelta(seconds=5)
    
    ticks = mt5.copy_ticks_range(SYMBOL_BB, fetch_start, fetch_end, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    
    df = pd.DataFrame(ticks)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def calculate_mae_mfe(tick_df, position, window_minutes):
    """Calculate MAE/MFE for a specific time window."""
    open_time = position["open_time"]
    entry_price = position["open_price"]
    direction = position["direction"]
    
    window_end = open_time + timedelta(minutes=window_minutes)
    window_ticks = tick_df[(tick_df["time"] >= open_time) & (tick_df["time"] <= window_end)]
    
    if window_ticks.empty:
        return None, None, None
    
    if direction == "BUY":
        mfe_price = window_ticks["ask"].max()
        mae_price = window_ticks["bid"].min()
        mfe_points = (mfe_price - entry_price) * 100
        mae_points = (entry_price - mae_price) * 100
        close_price = window_ticks["bid"].iloc[-1]
        close_points = (close_price - entry_price) * 100
    else:  # SELL
        mfe_price = window_ticks["bid"].min()
        mae_price = window_ticks["ask"].max()
        mfe_points = (entry_price - mfe_price) * 100
        mae_points = (mae_price - entry_price) * 100
        close_price = window_ticks["ask"].iloc[-1]
        close_points = (entry_price - close_price) * 100
    
    return mfe_points, mae_points, close_points


def simulate_time_sl(position, tick_df, atr_points):
    """Simulate outcome if position closed at time-based SL."""
    tp_points = atr_points * ATR_TP_MULTIPLIER
    results = {}
    
    for minutes in TIME_WINDOWS:
        mfe, mae, close_pnl = calculate_mae_mfe(tick_df, position, minutes)
        
        if mfe is None:
            continue
        
        # PROFIT if MFE >= TP
        if mfe >= tp_points:
            outcome = "PROFIT"
            outcome_points = tp_points
        else:
            outcome = "LOSS"
            outcome_points = close_pnl
        
        results[minutes] = {
            "outcome": outcome,
            "outcome_points": outcome_points,
            "mfe_points": mfe,
            "mae_points": mae
        }
    
    return results


def analyze_strategy(positions, strategy_name):
    """Analyze all positions for a specific strategy."""
    strategy_positions = [p for p in positions if p["strategy"] == strategy_name]
    
    if not strategy_positions:
        return None
    
    # Collect results for each time window
    time_results = {m: {"wins": 0, "losses": 0, "total_pnl": 0, "mae_sum": 0} for m in TIME_WINDOWS}
    
    for pos in strategy_positions:
        # Get ATR
        atr = get_atr_m1_60(pos["open_time"])
        if atr is None or pd.isna(atr):
            continue
        atr_points = atr * 100
        
        # Get tick data
        tick_df = fetch_tick_data(pos["open_time"])
        if tick_df is None:
            continue
        
        # Simulate time SL
        sim_results = simulate_time_sl(pos, tick_df, atr_points)
        
        for minutes, result in sim_results.items():
            if result["outcome"] == "PROFIT":
                time_results[minutes]["wins"] += 1
            else:
                time_results[minutes]["losses"] += 1
            time_results[minutes]["total_pnl"] += result["outcome_points"]
            time_results[minutes]["mae_sum"] += result["mae_points"]
    
    # Build DataFrame
    rows = []
    for minutes in TIME_WINDOWS:
        stats = time_results[minutes]
        total = stats["wins"] + stats["losses"]
        if total > 0:
            win_rate = stats["wins"] / total * 100
            avg_mae = stats["mae_sum"] / total
            rows.append({
                "TimeSL_Min": minutes,
                "WinRate": round(win_rate, 1),
                "Wins": stats["wins"],
                "Losses": stats["losses"],
                "TotalPnL": round(stats["total_pnl"], 1),
                "AvgMAE": round(avg_mae, 1)
            })
    
    return pd.DataFrame(rows)


def generate_time_analysis(target_date):
    """Main function to generate TimeAnalysis."""
    print("=" * 80)
    print(f"Daily TimeAnalysis Generator")
    print(f"Date: {target_date}")
    print("=" * 80)
    
    # Connect to Vantage
    if not connect_mt5_terminal("MT5_TERMINAL_VANTAGE"):
        return None
    
    positions = fetch_gu_positions(target_date)
    if not positions:
        mt5.shutdown()
        return None
    mt5.shutdown()
    
    # Connect to BlackBull for tick/ATR data
    if not connect_mt5_terminal("MT5_TERMINAL_BLACKBULL"):
        return None
    
    # Get unique strategies
    strategies = sorted(set(p["strategy"] for p in positions if p["strategy"] != "Unknown"))
    print(f"\nStrategies found: {strategies}")
    
    # Analyze each strategy
    strategy_results = {}
    summary_rows = []
    
    for strategy in strategies:
        print(f"\nAnalyzing {strategy}...")
        df_strategy = analyze_strategy(positions, strategy)
        
        if df_strategy is not None and len(df_strategy) > 0:
            strategy_results[strategy] = df_strategy
            
            # Find optimal
            optimal_row = df_strategy.loc[df_strategy["TotalPnL"].idxmax()]
            summary_rows.append({
                "Strategy": strategy,
                "Positions": len([p for p in positions if p["strategy"] == strategy]),
                "OptimalTimeSL": int(optimal_row["TimeSL_Min"]),
                "OptimalWinRate": optimal_row["WinRate"],
                "OptimalPnL": optimal_row["TotalPnL"]
            })
    
    mt5.shutdown()
    
    # Summary DataFrame
    df_summary = pd.DataFrame(summary_rows)
    
    # Save to Excel
    output_file = os.path.join(OUTPUT_DIR, f"{target_date.strftime('%Y%m%d')}_TimeAnalysis.xlsx")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        for strategy, df in strategy_results.items():
            # Sheet name limited to 31 chars
            sheet_name = strategy[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print("\n" + "=" * 80)
    print("TimeAnalysis Complete")
    print("=" * 80)
    print(f"Output: {output_file}")
    print(f"\nSummary:")
    print(df_summary.to_string(index=False))
    
    # Escalation check
    for row in summary_rows:
        if row["OptimalTimeSL"] > 15:
            print(f"\n[ESCALATION] {row['Strategy']} optimal SL {row['OptimalTimeSL']} min > 15 min threshold")
    
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Daily TimeAnalysis')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format (default: yesterday)')
    args = parser.parse_args()
    
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    
    generate_time_analysis(target_date)
