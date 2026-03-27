"""
Calculate MAE (Maximum Adverse Excursion) for recovery trades
For each recovered position, find the worst drawdown from SL hit to recovery
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
    return price_diff * 100

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
    # Filter for recovered positions with <=120min and <=10 opposing
    df_rec = df[(df['Recovered'] == 'YES') & 
                (df['RecoveryDurationMin'] <= 120) & 
                (df['OpposingCount'] <= 10)]
    all_data.append(df_rec)
    print(f"{date}: {len(df_rec)} valid recovery trades")

df_all = pd.concat(all_data, ignore_index=True)
print(f"\nTotal valid recovery trades to analyze: {len(df_all)}")

# For each recovery trade, calculate MAE
symbol = "XAUUSD+"
mae_results = []

for idx, row in df_all.iterrows():
    date_str = row['Date']
    ticket = row['Ticket']
    direction = row['Direction']
    close_price = row['ClosePrice']  # This is where recovery trade would enter
    target_price = row['OpenPrice']  # This is the target
    recovery_time_str = row['RecoveryTime']
    
    # Parse times
    close_time = datetime.strptime(f"{date_str} {row['CloseTime']}", "%Y-%m-%d %H:%M:%S")
    close_time = close_time.replace(tzinfo=timezone.utc)
    recovery_time = datetime.strptime(f"{date_str} {recovery_time_str}", "%Y-%m-%d %H:%M:%S")
    recovery_time = recovery_time.replace(tzinfo=timezone.utc)
    
    # Fetch ticks between close and recovery
    ticks = mt5.copy_ticks_range(symbol, close_time, recovery_time, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        mae_results.append({
            'Ticket': ticket,
            'Date': date_str,
            'MAE_Points': None,
            'Entry_Price': close_price,
            'Worst_Price': None,
            'Recovery_Price': row['RecoveryPrice']
        })
        continue
    
    # Find MAE - worst price movement against recovery trade
    # For BUY recovery: worst price is the minimum bid (price goes down further)
    # For SELL recovery: worst price is the maximum ask (price goes up further)
    
    if direction == "BUY":
        # Recovery trade is BUY (original was BUY that lost, recovering back up)
        # Entry at close_price (lower), target is OpenPrice (higher)
        # MAE = lowest price reached after entry
        min_price = float('inf')
        for i in range(len(ticks)):
            price = ticks[i]['bid']
            if price < min_price:
                min_price = price
        
        # MAE in points = (entry - worst) * 100
        mae_points = price_to_points(close_price - min_price) if min_price != float('inf') else 0
        worst_price = min_price
    else:
        # Recovery trade is SELL (original was SELL that lost, recovering back down)
        # Entry at close_price (higher), target is OpenPrice (lower)
        # MAE = highest price reached after entry
        max_price = 0
        for i in range(len(ticks)):
            price = ticks[i]['ask']
            if price > max_price:
                max_price = price
        
        # MAE in points = (worst - entry) * 100
        mae_points = price_to_points(max_price - close_price) if max_price > 0 else 0
        worst_price = max_price
    
    mae_results.append({
        'Ticket': ticket,
        'Date': date_str,
        'Direction': direction,
        'MAE_Points': round(mae_points, 1),
        'Entry_Price': close_price,
        'Worst_Price': worst_price,
        'Recovery_Price': row['RecoveryPrice'],
        'Recovery_Duration': row['RecoveryDurationMin']
    })
    
    if (idx + 1) % 20 == 0:
        print(f"Processed {idx + 1}/{len(df_all)}...")

mt5.shutdown()

# Create DataFrame
df_mae = pd.DataFrame(mae_results)

# Save
df_mae.to_csv('data/Recovery_MAE_Analysis.csv', index=False)

print("\n" + "="*100)
print("MAE ANALYSIS COMPLETE")
print("="*100)

# Remove None values for stats
df_mae_valid = df_mae[df_mae['MAE_Points'].notna()]

print(f"\nTotal recovery trades analyzed: {len(df_mae_valid)}")

if len(df_mae_valid) > 0:
    print(f"\nMAE Statistics (in points):")
    print(f"  Mean: {df_mae_valid['MAE_Points'].mean():.1f}")
    print(f"  Median: {df_mae_valid['MAE_Points'].median():.1f}")
    print(f"  Min: {df_mae_valid['MAE_Points'].min():.1f}")
    print(f"  Max: {df_mae_valid['MAE_Points'].max():.1f}")
    print(f"  75th percentile: {df_mae_valid['MAE_Points'].quantile(0.75):.1f}")
    print(f"  90th percentile: {df_mae_valid['MAE_Points'].quantile(0.90):.1f}")
    print(f"  95th percentile: {df_mae_valid['MAE_Points'].quantile(0.95):.1f}")
    
    # Show top 10 worst MAE
    print("\nTop 10 Worst MAE (drawdowns):")
    worst_mae = df_mae_valid.nlargest(10, 'MAE_Points')[['Date', 'Ticket', 'Direction', 'MAE_Points', 'Entry_Price', 'Worst_Price', 'Recovery_Duration']]
    print(worst_mae.to_string(index=False))

print(f"\nSaved to data/Recovery_MAE_Analysis.csv")
