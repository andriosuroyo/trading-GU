"""
Create comprehensive analysis for March 23, 2026 GU positions.

Fetches positions from Vantage, calculates MFE/MAE using BlackBull tick data,
and outputs to Excel with RESULT summary and 30 time window sheets.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
from collections import defaultdict

# Configuration
TARGET_DATE = datetime(2026, 3, 23).date()
SYMBOL_BB = "XAUUSDp"
TIME_WINDOWS = range(1, 31)  # 1-30 minutes


def load_env():
    """Load environment variables from .env file."""
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
    """Connect to MT5 terminal specified by environment variable key."""
    env_vars = load_env()
    terminal_path = env_vars.get(terminal_key)
    
    if not terminal_path or not os.path.exists(terminal_path):
        print(f"Error: Terminal path not found for {terminal_key}: {terminal_path}")
        return False
    
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize() failed for {terminal_key}: {mt5.last_error()}")
        return False
    
    info = mt5.account_info()
    print(f"Connected to: {info.server} | Account: {info.login}")
    return True


def is_gu_position(comment, magic):
    """Check if position is GU strategy based on comment or magic."""
    if comment and "GU_" in comment.upper():
        return True
    if magic and str(magic).startswith("282603"):
        return True
    return False


def fetch_gu_positions(date_from, date_to):
    """Fetch all GU positions from Vantage for given date range."""
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
            if not is_gu_position(entry_deal.comment, entry_deal.magic):
                continue
            
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            
            positions.append({
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
                "comment": entry_deal.comment
            })
            gu_count += 1
    
    positions.sort(key=lambda x: x["open_time"])
    print(f"GU positions found: {gu_count}")
    return positions


def get_atr_m1_60(target_time):
    """Get ATR(60) on M1 timeframe at target time from BlackBull."""
    # Ensure target_time is timezone-aware (UTC)
    if target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=timezone.utc)
    
    # Get 2 hours of M1 data to have enough for 60-period ATR
    from_time = target_time - timedelta(hours=2)
    rates = mt5.copy_rates_range(SYMBOL_BB, mt5.TIMEFRAME_M1, from_time, target_time)
    
    if rates is None or len(rates) < 60:
        return None
    
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    
    # Calculate True Range
    df["high_low"] = df["high"] - df["low"]
    df["high_close"] = abs(df["high"] - df["close"].shift())
    df["low_close"] = abs(df["low"] - df["close"].shift())
    df["tr"] = df[["high_low", "high_close", "low_close"]].max(axis=1)
    
    # Calculate ATR(60)
    df["atr_60"] = df["tr"].rolling(window=60).mean()
    
    # Get ATR at or before target_time
    df_before = df[df["time"] <= target_time]
    if df_before.empty:
        return None
    
    return df_before["atr_60"].iloc[-1]


def fetch_tick_data(open_time, window_minutes=30):
    """Fetch tick data from BlackBull for specified window."""
    # Ensure open_time is timezone-aware (UTC)
    if open_time.tzinfo is None:
        open_time = open_time.replace(tzinfo=timezone.utc)
    
    window_end = open_time + timedelta(minutes=window_minutes)
    
    # Add small buffer for fetching
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_end + timedelta(seconds=5)
    
    ticks = mt5.copy_ticks_range(SYMBOL_BB, fetch_start, fetch_end, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        return None
    
    df = pd.DataFrame(ticks)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    
    return df


def calculate_mfe_mae(tick_df, position, window_minutes):
    """Calculate MFE and MAE for a specific time window."""
    open_time = position["open_time"]
    if open_time.tzinfo is None:
        open_time = open_time.replace(tzinfo=timezone.utc)
    
    window_end = open_time + timedelta(minutes=window_minutes)
    
    # Filter ticks within the window
    window_ticks = tick_df[(tick_df["time"] >= open_time) & (tick_df["time"] <= window_end)]
    
    if window_ticks.empty:
        return None, None, None, None, None
    
    entry_price = position["open_price"]
    direction = position["direction"]
    
    if direction == "BUY":
        # For BUY: MFE = max ask (favorable), MAE = min bid (adverse)
        mfe_price = window_ticks["ask"].max()
        mae_price = window_ticks["bid"].min()
        # Close price at window end (use bid for BUY close)
        window_close_price = window_ticks["bid"].iloc[-1]
    else:  # SELL
        # For SELL: MFE = min bid (favorable), MAE = max ask (adverse)
        mfe_price = window_ticks["bid"].min()
        mae_price = window_ticks["ask"].max()
        # Close price at window end (use ask for SELL close)
        window_close_price = window_ticks["ask"].iloc[-1]
    
    # Calculate points
    if direction == "BUY":
        mfe_points = round(abs((mfe_price - entry_price) * 100))
        mae_points = round(abs((entry_price - mae_price) * 100))
        close_points = round((window_close_price - entry_price) * 100)
    else:  # SELL
        mfe_points = round(abs((entry_price - mfe_price) * 100))
        mae_points = round(abs((mae_price - entry_price) * 100))
        close_points = round((entry_price - window_close_price) * 100)
    
    return mfe_price, mfe_points, mae_price, mae_points, close_points


def analyze_position(position, all_tick_df):
    """Analyze a single position across all time windows."""
    pos_id = position["pos_id"]
    direction = position["direction"]
    entry_price = position["open_price"]
    exit_price = position["close_price"]
    magic = position["magic"]
    open_time = position["open_time"]
    close_time = position["close_time"]
    comment = position["comment"]
    
    # Get ATR at open time
    atr_value = get_atr_m1_60(open_time)
    if atr_value is None or pd.isna(atr_value):
        atr_value = 0
    atr_tp_points = round(atr_value * 0.5 * 100)
    
    # Calculate actual points
    if direction == "BUY":
        actual_points = round((exit_price - entry_price) * 100)
    else:
        actual_points = round((entry_price - exit_price) * 100)
    
    # Results for each time window
    window_results = {}
    
    for window_min in TIME_WINDOWS:
        mfe_price, mfe_points, mae_price, mae_points, close_points = calculate_mfe_mae(
            all_tick_df, position, window_min
        )
        
        if mfe_points is None:
            continue
        
        # Determine outcome: PROFIT if MFE >= ATR_TP, else LOSS
        if mfe_points >= atr_tp_points:
            outcome = "PROFIT"
            outcome_points = atr_tp_points
        else:
            outcome = "LOSS"
            outcome_points = close_points
        
        window_results[window_min] = {
            "mfe_price": round(mfe_price, 2),
            "mfe_points": mfe_points,
            "mae_price": round(mae_price, 2),
            "mae_points": mae_points,
            "outcome": outcome,
            "outcome_points": outcome_points
        }
    
    return {
        "pos_id": pos_id,
        "magic": magic,
        "direction": direction,
        "open_time": open_time,
        "open_price": entry_price,
        "close_time": close_time,
        "close_price": exit_price,
        "actual_points": actual_points,
        "atr_value": round(atr_value, 2),
        "atr_tp": atr_tp_points,
        "comment": comment,
        "windows": window_results
    }


def create_excel_output(results, output_file):
    """Create Excel file with RESULT sheet and individual time window sheets."""
    
    # Prepare RESULT sheet data
    result_rows = []
    
    for window_min in TIME_WINDOWS:
        profit_count = 0
        loss_count = 0
        total_outcome = 0
        
        for r in results:
            if window_min in r["windows"]:
                w_data = r["windows"][window_min]
                if w_data["outcome"] == "PROFIT":
                    profit_count += 1
                else:
                    loss_count += 1
                total_outcome += w_data["outcome_points"]
        
        total_count = profit_count + loss_count
        win_rate = (profit_count / total_count * 100) if total_count > 0 else 0
        
        result_rows.append({
            "TimeWindow": f"{window_min}min",
            "ProfitCount": profit_count,
            "LossCount": loss_count,
            "WinRate": round(win_rate, 2),
            "TotalOutcomePoints": total_outcome
        })
    
    df_result = pd.DataFrame(result_rows)
    
    # Create Excel writer
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Write RESULT sheet
        df_result.to_excel(writer, sheet_name="RESULT", index=False)
        
        # Write individual time window sheets
        for window_min in TIME_WINDOWS:
            sheet_name = f"{window_min}min"
            sheet_rows = []
            
            for r in results:
                if window_min not in r["windows"]:
                    continue
                
                w_data = r["windows"][window_min]
                
                sheet_rows.append({
                    "Ticket": f"P{r['pos_id']}",
                    "Magic Number": r["magic"],
                    "Type": r["direction"],
                    "TimeOpen": r["open_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "PriceOpen": r["open_price"],
                    "TimeClose": r["close_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "PriceClose": r["close_price"],
                    "ActualPoints": r["actual_points"],
                    "ATROpen": r["atr_value"],
                    "ATRTP": r["atr_tp"],
                    f"MFE{window_min}Price": w_data["mfe_price"],
                    f"MFE{window_min}Points": w_data["mfe_points"],
                    f"MAE{window_min}Price": w_data["mae_price"],
                    f"MAE{window_min}Points": w_data["mae_points"],
                    "Outcome": w_data["outcome"],
                    "OutcomePoints": w_data["outcome_points"]
                })
            
            if sheet_rows:
                df_sheet = pd.DataFrame(sheet_rows)
                df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Excel file saved: {output_file}")
    return df_result


def main():
    """Main function to run the analysis."""
    print("=" * 80)
    print("GU Analysis for March 23, 2026")
    print("=" * 80)
    
    # Step 1: Connect to Vantage and fetch positions
    print("\nStep 1: Connecting to Vantage MT5...")
    if not connect_mt5_terminal("MT5_TERMINAL_VANTAGE"):
        print("Failed to connect to Vantage")
        return
    
    # Calculate date range for March 23, 2026
    date_from = datetime.combine(TARGET_DATE, datetime.min.time(), tzinfo=timezone.utc)
    date_to = date_from + timedelta(days=1)
    
    print(f"\nStep 2: Fetching GU positions for {TARGET_DATE}...")
    positions = fetch_gu_positions(date_from, date_to)
    
    if not positions:
        print("No GU positions found for the target date")
        mt5.shutdown()
        return
    
    print(f"Found {len(positions)} positions to analyze")
    
    # Shutdown Vantage connection
    mt5.shutdown()
    
    # Step 3: Connect to BlackBull
    print("\nStep 3: Connecting to BlackBull MT5...")
    if not connect_mt5_terminal("MT5_TERMINAL_BLACKBULL"):
        print("Failed to connect to BlackBull")
        return
    
    # Step 4: Analyze each position
    print("\nStep 4: Analyzing positions...")
    results = []
    
    for i, pos in enumerate(positions, 1):
        print(f"  Processing position {i}/{len(positions)} (ID: {pos['pos_id']})...")
        
        # Fetch 30 minutes of tick data for this position
        tick_df = fetch_tick_data(pos["open_time"], window_minutes=30)
        
        if tick_df is None or tick_df.empty:
            print(f"    Warning: No tick data available for position {pos['pos_id']}")
            continue
        
        # Analyze this position
        result = analyze_position(pos, tick_df)
        results.append(result)
    
    # Shutdown BlackBull connection
    mt5.shutdown()
    
    if not results:
        print("\nNo results generated - all positions failed to get tick data")
        return
    
    # Step 5: Create Excel output
    print("\nStep 5: Creating Excel output...")
    output_file = os.path.join(os.path.dirname(__file__), "data", "Analysis_20260323.xlsx")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    df_result = create_excel_output(results, output_file)
    
    # Print summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\nTotal positions analyzed: {len(results)}")
    print(f"\nRESULT sheet preview:")
    print(df_result.to_string(index=False))
    
    # Summary statistics
    total_profit = df_result["ProfitCount"].sum()
    total_loss = df_result["LossCount"].sum()
    if total_profit + total_loss > 0:
        overall_wr = total_profit / (total_profit + total_loss) * 100
        print(f"\nOverall: {total_profit} profits, {total_loss} losses ({overall_wr:.1f}% WR)")
    
    print(f"\nOutput file: {output_file}")
    print("\nDone!")


if __name__ == "__main__":
    main()
