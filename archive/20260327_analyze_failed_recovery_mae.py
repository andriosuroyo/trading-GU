"""
Analyze MAE for failed recovery positions
For the 54 positions that failed (either recovered outside criteria or never recovered),
calculate the worst MAE within 120 minutes from InitialOpenTime.
"""
import MetaTrader5 as mt5
import os
import pandas as pd
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

def price_to_points(price_diff):
    """Convert XAUUSD price difference to points. $1 = 100 points"""
    return abs(price_diff) * 100

# Connect to MT5
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

print(f"Connected to: {mt5.account_info().server} | Account: {mt5.account_info().login}")

# Load RecoveryAnalysis files
dates = ['2026-03-20', '2026-03-23', '2026-03-24']
all_data = []

for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis.xlsx')
    all_data.append(df)

df_all = pd.concat(all_data, ignore_index=True)

# Get the 54 failed positions:
# 1. Recovered but >120min OR >10 opposing
# 2. Never recovered
recovered_120_10 = df_all[
    (df_all['Recovered'] == 'YES') & 
    (df_all['RecoveryDurationMin'] <= 120) & 
    (df_all['OpposingCount'] <= 10)
]

# All other positions are "failed" by our criteria
failed_tickets = set(df_all['Ticket']) - set(recovered_120_10['Ticket'])
df_failed = df_all[df_all['Ticket'].isin(failed_tickets)]

print(f"\nTotal failed positions to analyze: {len(df_failed)}")
print(f"  - Recovered but outside criteria: {len(df_all[(df_all['Recovered'] == 'YES') & (~df_all['Ticket'].isin(recovered_120_10['Ticket']))])}")
print(f"  - Never recovered: {len(df_all[df_all['Recovered'] == 'NO'])}")

# For each failed position, calculate MAE within 120 minutes from InitialOpenTime
symbol = "XAUUSD+"
mae_results = []

for idx, row in df_failed.iterrows():
    date_str = row['Date']
    ticket = row['Ticket']
    direction = row['Direction']
    open_price = row['OpenPrice']  # This is where the original position opened
    close_price = row['ClosePrice']  # This is where SL hit
    
    # Parse InitialOpenTime
    open_time = datetime.strptime(f"{date_str} {row['OpenTime']}", "%Y-%m-%d %H:%M:%S")
    open_time = open_time.replace(tzinfo=timezone.utc)
    
    # 120 minutes from InitialOpenTime
    window_end = open_time + timedelta(minutes=120)
    
    # Fetch ticks from InitialOpenTime to +120min
    ticks = mt5.copy_ticks_range(symbol, open_time, window_end, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        mae_results.append({
            'Ticket': ticket,
            'Date': date_str,
            'Magic': row['Magic'],
            'Direction': direction,
            'Failed_Reason': 'Recovered>120min' if row['Recovered'] == 'YES' else 'NeverRecovered',
            'MAE_120min_Points': None,
            'Open_Price': open_price,
            'Close_Price': close_price,
            'Worst_Price': None,
            'RecoveryTime': row['RecoveryTime'],
            'RecoveryDuration': row['RecoveryDurationMin'],
            'OpposingCount': row['OpposingCount']
        })
        continue
    
    # Find MAE from InitialOpenPrice perspective
    # For BUY position: worst price = lowest bid (most against position)
    # For SELL position: worst price = highest ask (most against position)
    
    if direction == "BUY":
        # Position bought at open_price, want price to go up
        # MAE = how much lower did price go from open_price
        min_price = float('inf')
        for i in range(len(ticks)):
            price = ticks[i]['bid']
            if price < min_price:
                min_price = price
        
        mae_points = price_to_points(open_price - min_price) if min_price != float('inf') else 0
        worst_price = min_price
    else:
        # Position sold at open_price, want price to go down
        # MAE = how much higher did price go from open_price
        max_price = 0
        for i in range(len(ticks)):
            price = ticks[i]['ask']
            if price > max_price:
                max_price = price
        
        mae_points = price_to_points(max_price - open_price) if max_price > 0 else 0
        worst_price = max_price
    
    mae_results.append({
        'Ticket': ticket,
        'Date': date_str,
        'Magic': row['Magic'],
        'Direction': direction,
        'Failed_Reason': 'Recovered>120min' if row['Recovered'] == 'YES' else 'NeverRecovered',
        'MAE_120min_Points': round(mae_points, 1),
        'Open_Price': open_price,
        'Close_Price': close_price,
        'Worst_Price': worst_price,
        'RecoveryTime': row['RecoveryTime'],
        'RecoveryDuration': row['RecoveryDurationMin'],
        'OpposingCount': row['OpposingCount']
    })
    
    if (idx + 1) % 10 == 0:
        print(f"Processed {idx + 1}/{len(df_failed)}...")

mt5.shutdown()

# Create DataFrame
df_mae = pd.DataFrame(mae_results)

# Save
df_mae.to_csv('data/Failed_Recovery_MAE_Analysis.csv', index=False)

print("\n" + "="*100)
print("FAILED RECOVERY MAE ANALYSIS")
print("="*100)

# Remove None values for stats
df_mae_valid = df_mae[df_mae['MAE_120min_Points'].notna()]

print(f"\nTotal failed positions analyzed: {len(df_mae_valid)}")

if len(df_mae_valid) > 0:
    print(f"\nMAE within 120min from InitialOpenTime (in points):")
    print(f"  Mean: {df_mae_valid['MAE_120min_Points'].mean():.1f}")
    print(f"  Median: {df_mae_valid['MAE_120min_Points'].median():.1f}")
    print(f"  Min: {df_mae_valid['MAE_120min_Points'].min():.1f}")
    print(f"  Max: {df_mae_valid['MAE_120min_Points'].max():.1f}")
    print(f"  75th percentile: {df_mae_valid['MAE_120min_Points'].quantile(0.75):.1f}")
    print(f"  90th percentile: {df_mae_valid['MAE_120min_Points'].quantile(0.90):.1f}")
    print(f"  95th percentile: {df_mae_valid['MAE_120min_Points'].quantile(0.95):.1f}")
    
    # By failure reason
    print("\nBy Failure Reason:")
    for reason in df_mae_valid['Failed_Reason'].unique():
        subset = df_mae_valid[df_mae_valid['Failed_Reason'] == reason]
        print(f"  {reason}: {len(subset)} positions")
        print(f"    Mean MAE: {subset['MAE_120min_Points'].mean():.1f} points")
        print(f"    Max MAE: {subset['MAE_120min_Points'].max():.1f} points")
    
    # Show top 10 worst MAE
    print("\nTop 10 Worst MAE (failed recoveries):")
    worst_mae = df_mae_valid.nlargest(10, 'MAE_120min_Points')[['Date', 'Ticket', 'Magic', 'Direction', 'Failed_Reason', 'MAE_120min_Points', 'Worst_Price', 'OpposingCount']]
    print(worst_mae.to_string(index=False))

print(f"\nSaved to data/Failed_Recovery_MAE_Analysis.csv")
