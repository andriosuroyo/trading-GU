"""
Create cleaned position history dataset for MLE.
Target: TrailStart hit prediction feature engineering.

Output: data/position_history_cleaned_260327.csv

NOTE: Date range is March 23-27, 2026 (settings changed significantly before March 23)
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os

# Configuration
OUTPUT_FILE = "data/position_history_cleaned_260327.csv"
SAMPLE_FILE = "data/position_history_sample_260327.csv"

# Valid GU magic numbers
GU_MAGICS = {11, 12, 13, 21, 22, 23, 31, 32, 33}

# Date range - March 23-27, 2026 (settings changed significantly before March 23)
START_DATE = datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
END_DATE = datetime(2026, 3, 27, 23, 59, 59, tzinfo=timezone.utc)

# TrailStart is typically 0.5x ATR
TRAILSTART_MULT = 0.5

SYMBOL_BB = "XAUUSDp"

# RELAXED carry-over threshold - allow positions to close up to 4 hours after session
CARRY_OVER_BUFFER_HOURS = 4


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


def is_gu_magic(magic):
    """Check if magic number is a GU magic (11-13, 21-23, 31-33)."""
    return magic in GU_MAGICS


def get_session_window(magic):
    """Get session trading window for a magic number."""
    session = magic % 10
    if session == 1:  # Asia
        return (2, 6)  # 02:00-06:00 UTC
    elif session == 2:  # London
        return (8, 12)  # 08:00-12:00 UTC
    elif session == 3:  # NY
        return (17, 21)  # 17:00-21:00 UTC
    return None


def is_carry_over_trade(close_time, magic):
    """
    Check if position closed outside its session window.
    RELAXED: Allows up to 4 hours after session end (TCM can hold positions longer)
    """
    window = get_session_window(magic)
    if not window:
        return False
    
    close_hour = close_time.hour
    start_hour, end_hour = window
    
    # Allow positions to close up to CARRY_OVER_BUFFER_HOURS after session end
    if close_hour < start_hour or close_hour > end_hour + CARRY_OVER_BUFFER_HOURS:
        return True
    return False


def fetch_positions_vantage():
    """Fetch all positions from Vantage MT5."""
    deals = mt5.history_deals_get(START_DATE, END_DATE)
    if not deals:
        print(f"No deals found")
        return []
    
    print(f"Total raw deals found: {len(deals)}")
    
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
            magic = entry_deal.magic
            
            # Filter for GU magics only
            if not is_gu_magic(magic):
                continue
            
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            
            positions.append({
                "ticket": pid,
                "magic": magic,
                "direction": direction,
                "open_time": datetime.fromtimestamp(entry_deal.time, tz=timezone.utc),
                "close_time": datetime.fromtimestamp(exit_deal.time, tz=timezone.utc),
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "volume": entry_deal.volume,
                "profit": exit_deal.profit + entry_deal.commission + entry_deal.commission + exit_deal.swap
            })
    
    print(f"GU positions found: {len(positions)}")
    return positions


def get_atr_m1_60_blackbull(target_time):
    """Get ATR(60) on M1 timeframe at target time from BlackBull."""
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
    
    df_before = df[df["time"] <= target_time]
    if df_before.empty:
        return None
    
    return df_before["atr_60"].iloc[-1]


def fetch_tick_data_blackbull(open_time, close_time):
    """Fetch tick data from BlackBull for position duration."""
    # Add small buffer
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = close_time + timedelta(seconds=5)
    
    ticks = mt5.copy_ticks_range(SYMBOL_BB, fetch_start, fetch_end, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        return None
    
    df = pd.DataFrame(ticks)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def calculate_mae_mfe_trailstart(tick_df, position, atr_points):
    """
    Calculate MAE, MFE, and TrailStart hit.
    Returns: (mfe_points, mae_points, furthest_price, trailstart_hit, recovered, recovery_time)
    """
    open_time = position["open_time"]
    entry_price = position["open_price"]
    direction = position["direction"]
    close_time = position["close_time"]
    
    # TrailStart distance in points
    trailstart_distance = atr_points * TRAILSTART_MULT
    
    # Filter ticks from open to close
    window_ticks = tick_df[(tick_df["time"] >= open_time) & (tick_df["time"] <= close_time)]
    
    if window_ticks.empty:
        return None, None, None, None, None, None
    
    if direction == "BUY":
        # MFE = max ask (favorable), MAE = min bid (adverse)
        mfe_price = window_ticks["ask"].max()
        mae_price = window_ticks["bid"].min()
        mfe_points = (mfe_price - entry_price) * 100
        mae_points = (entry_price - mae_price) * 100
        furthest_price = mae_price
        
        # TrailStart hit: price moved favorably by TrailStart distance
        trailstart_price = entry_price + (trailstart_distance / 100)
        trailstart_hit = (window_ticks["ask"] >= trailstart_price).any()
        
        # Recovery: price returned to entry
        recovered = (window_ticks["bid"] >= entry_price).any()
        
    else:  # SELL
        # MFE = min bid (favorable), MAE = max ask (adverse)
        mfe_price = window_ticks["bid"].min()
        mae_price = window_ticks["ask"].max()
        mfe_points = (entry_price - mfe_price) * 100
        mae_points = (mae_price - entry_price) * 100
        furthest_price = mae_price
        
        # TrailStart hit
        trailstart_price = entry_price - (trailstart_distance / 100)
        trailstart_hit = (window_ticks["bid"] <= trailstart_price).any()
        
        # Recovery
        recovered = (window_ticks["ask"] <= entry_price).any()
    
    # Recovery time (minutes)
    recovery_time = None
    if recovered:
        if direction == "BUY":
            recovery_ticks = window_ticks[window_ticks["bid"] >= entry_price]
        else:
            recovery_ticks = window_ticks[window_ticks["ask"] <= entry_price]
        if not recovery_ticks.empty:
            recovery_time = (recovery_ticks.iloc[0]["time"] - open_time).total_seconds() / 60
    
    return mfe_points, mae_points, furthest_price, trailstart_hit, recovered, recovery_time


def identify_glitch_trades(positions):
    """Identify glitch trades (simultaneous BUY/SELL at same timestamp)."""
    glitch_tickets = set()
    
    # Group by open time (rounded to minute)
    by_time = defaultdict(list)
    for pos in positions:
        time_key = pos["open_time"].replace(second=0, microsecond=0)
        by_time[time_key].append(pos)
    
    for time_key, pos_list in by_time.items():
        if len(pos_list) >= 2:
            directions = set(p["direction"] for p in pos_list)
            if len(directions) > 1:  # Both BUY and SELL at same time
                for p in pos_list:
                    glitch_tickets.add(p["ticket"])
                    print(f"  Glitch: Ticket {p['ticket']} at {time_key}")
    
    return glitch_tickets


def process_positions():
    """Main processing function."""
    print("=" * 80)
    print("Creating MLE Dataset - Cleaned Position History")
    print("=" * 80)
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Carry-over buffer: {CARRY_OVER_BUFFER_HOURS} hours after session")
    
    # Step 1: Connect to Vantage to fetch positions
    print("\nStep 1: Connecting to Vantage MT5...")
    if not connect_mt5_terminal("MT5_TERMINAL_VANTAGE"):
        print("Failed to connect to Vantage")
        return None
    
    # Fetch positions
    print(f"\nStep 2: Fetching positions from Vantage...")
    positions = fetch_positions_vantage()
    
    if not positions:
        print("No GU positions found")
        mt5.shutdown()
        return None
    
    print(f"Found {len(positions)} GU positions before filtering")
    mt5.shutdown()
    
    # Identify glitch trades
    print("\nStep 3: Identifying glitch trades...")
    glitch_tickets = identify_glitch_trades(positions)
    print(f"Found {len(glitch_tickets)} glitch trade tickets")
    
    # Step 2: Connect to BlackBull for tick data
    print("\nStep 4: Connecting to BlackBull MT5...")
    if not connect_mt5_terminal("MT5_TERMINAL_BLACKBULL"):
        print("Failed to connect to BlackBull")
        return None
    
    # Process each position
    print("\nStep 5: Processing positions (fetching ticks, calculating MAE/MFE)...")
    results = []
    
    for i, pos in enumerate(positions):
        # Skip glitch trades
        if pos["ticket"] in glitch_tickets:
            continue
        
        # Check for carry-over (with relaxed buffer)
        if is_carry_over_trade(pos["close_time"], pos["magic"]):
            continue
        
        # Get ATR at open from BlackBull
        atr_value = get_atr_m1_60_blackbull(pos["open_time"])
        if atr_value is None or pd.isna(atr_value):
            continue
        atr_points = atr_value * 100
        
        # Fetch tick data from BlackBull
        tick_df = fetch_tick_data_blackbull(pos["open_time"], pos["close_time"])
        if tick_df is None or tick_df.empty:
            continue
        
        # Calculate MAE/MFE and TrailStart
        calc_result = calculate_mae_mfe_trailstart(tick_df, pos, atr_points)
        mfe_pts, mae_pts, furthest_price, trailstart_hit, recovered, recovery_time = calc_result
        
        if mfe_pts is None:
            continue
        
        # Calculate points
        if pos["direction"] == "BUY":
            actual_points = (pos["close_price"] - pos["open_price"]) * 100
        else:
            actual_points = (pos["open_price"] - pos["close_price"]) * 100
        
        loss_points = abs(actual_points) if actual_points < 0 else 0
        
        # Normalize P/L to 0.01 lot (divide by 10 if 0.10 lot)
        lot_normalized_profit = pos["profit"] / (pos["volume"] * 100)
        
        # Determine basket (group by magic and date)
        date_str = pos["open_time"].strftime("%Y%m%d")
        basket = f"{date_str}_{pos['magic']}"
        
        results.append({
            "Date": pos["open_time"].strftime("%Y-%m-%d"),
            "Basket": basket,
            "Ticket": pos["ticket"],
            "Magic": pos["magic"],
            "Direction": pos["direction"],
            "OpenTime": pos["open_time"].strftime("%H:%M:%S"),
            "CloseTime": pos["close_time"].strftime("%H:%M:%S"),
            "OpenPrice": round(pos["open_price"], 2),
            "ClosePrice": round(pos["close_price"], 2),
            "LossPoints": round(loss_points, 1) if loss_points > 0 else 0,
            "ATRPoints": round(atr_points, 1),
            "Recovered": "Y" if recovered else "N",
            "RecoveryTime": round(recovery_time, 1) if recovery_time else 0,
            "FurthestPrice": round(furthest_price, 2) if furthest_price else round(pos["open_price"], 2),
            "LayerMAE": round(abs(mae_pts), 1),
            "TrailStartHit": "Y" if trailstart_hit else "N"
        })
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(positions)} positions... (kept {len(results)})")
    
    mt5.shutdown()
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    print("\n" + "=" * 80)
    print("Processing Complete")
    print("=" * 80)
    print(f"Total positions after filtering: {len(df)}")
    
    return df


def validate_data(df):
    """Validate the dataset meets acceptance criteria."""
    print("\n" + "=" * 80)
    print("Validation")
    print("=" * 80)
    
    # Check 1: At least 200 positions
    if len(df) < 200:
        print(f"[FAIL] Only {len(df)} positions (need at least 200)")
        return False
    print(f"[PASS] {len(df)} positions (>= 200)")
    
    # Check 2: No nulls in critical columns
    critical_cols = ["Magic", "OpenTime", "CloseTime", "TrailStartHit"]
    for col in critical_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            print(f"[FAIL] {col} has {null_count} null values")
            return False
    print("[PASS] No nulls in critical columns")
    
    # Check 3: Magic numbers are valid
    invalid_magics = df[~df["Magic"].isin(GU_MAGICS)]
    if len(invalid_magics) > 0:
        print(f"[FAIL] {len(invalid_magics)} invalid magic numbers")
        return False
    print("[PASS] All magic numbers valid")
    
    # Check 4: TrailStartHit distribution
    trailstart_y = (df["TrailStartHit"] == "Y").sum()
    trailstart_n = (df["TrailStartHit"] == "N").sum()
    print(f"[PASS] TrailStartHit distribution - Y: {trailstart_y}, N: {trailstart_n}")
    
    return True


if __name__ == "__main__":
    # Process positions
    df = process_positions()
    
    if df is None or len(df) == 0:
        print("ERROR: No data generated")
        exit(1)
    
    # Validate
    if not validate_data(df):
        print("\n[WARNING] Validation failed - saving anyway for inspection")
    
    # Save full dataset
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[SAVED] Full dataset: {OUTPUT_FILE}")
    
    # Save sample (5 rows) - mix of TrailStart hit and not hit
    sample_y = df[df["TrailStartHit"] == "Y"].head(3)
    sample_n = df[df["TrailStartHit"] == "N"].head(2)
    sample = pd.concat([sample_y, sample_n])
    sample.to_csv(SAMPLE_FILE, index=False)
    print(f"[SAVED] Sample: {SAMPLE_FILE}")
    
    # Display sample
    print("\n" + "=" * 80)
    print("Sample Output (5 rows)")
    print("=" * 80)
    print(sample.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("Deliverable Summary")
    print("=" * 80)
    print(f"Total rows: {len(df)}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Magic distribution:")
    for magic in sorted(df['Magic'].unique()):
        count = (df['Magic'] == magic).sum()
        print(f"  Magic {magic}: {count} positions")
    print(f"TrailStart hit rate: {(df['TrailStartHit'] == 'Y').mean()*100:.1f}%")
    print(f"Recovered rate: {(df['Recovered'] == 'Y').mean()*100:.1f}%")
