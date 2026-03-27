"""
Fix RecoveryAnalysis v3 - Correct FurthestPrice calculation
For BUY: FurthestPrice = LOWEST price (worst drawdown)
For SELL: FurthestPrice = HIGHEST price (worst drawdown)
"""
import MetaTrader5 as mt5
import os
import pandas as pd
import numpy as np
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
    return abs(price_diff) * 100

def add_conditional_formatting(writer, df):
    workbook = writer.book
    worksheet = writer.sheets['Recovery']
    recovered_col = df.columns.get_loc('Recovered')
    green_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
    red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    
    worksheet.conditional_format(1, recovered_col, len(df), recovered_col, {
        'type': 'cell', 'criteria': 'equal to', 'value': '"YES"', 'format': green_format
    })
    worksheet.conditional_format(1, recovered_col, len(df), recovered_col, {
        'type': 'cell', 'criteria': 'equal to', 'value': '"NO"', 'format': red_format
    })

# Connect to MT5
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    exit(1)

print(f"Connected to: {mt5.account_info().server}")

symbol = "XAUUSD+"

# Process only March 23 for now (the file with the issue)
dates = ['2026-03-23']

for date_str in dates:
    print(f"\n{'='*80}")
    print(f"FIXING: {date_str}")
    print(f"{'='*80}")
    
    # Load existing v3 file
    date_compact = date_str.replace('-', '')
    df = pd.read_excel(f'data/{date_compact}_RecoveryAnalysis_v3.xlsx')
    
    print(f"Loaded {len(df)} baskets")
    
    date = datetime.strptime(date_str, '%Y-%m-%d')
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    # Process each row to fix FurthestPrice and MAE
    for idx, row in df.iterrows():
        ticket_str = row['Ticket']  # P1023086679 format
        ticket_id = int(ticket_str[1:])  # Remove 'P' prefix
        
        direction = row['Direction']
        close_price = row['ClosePrice']  # Layer 1 entry price
        target_price = row['OpenPrice']  # Target
        
        # Get close time from the row
        close_time_str = row['CloseTime']
        hour, minute, sec = map(int, close_time_str.split(':'))
        close_time = datetime(date.year, date.month, date.day, hour, minute, sec, tzinfo=timezone.utc)
        
        window_end = close_time + timedelta(minutes=120)
        
        # Get ticks for this window
        ticks = mt5.copy_ticks_range(symbol, close_time, window_end, mt5.COPY_TICKS_ALL)
        
        if ticks is None or len(ticks) == 0:
            print(f"  Row {idx}: No tick data")
            continue
        
        # Find FurthestPrice (worst price for the position)
        # For BUY: lowest price (most against)
        # For SELL: highest price (most against)
        
        if direction == "BUY":
            # For BUY recovery, worst price is the LOWEST
            furthest_price = float('inf')
            for i in range(len(ticks)):
                price = ticks[i]['bid']
                if price < furthest_price:
                    furthest_price = price
        else:
            # For SELL recovery, worst price is the HIGHEST
            furthest_price = 0
            for i in range(len(ticks)):
                price = ticks[i]['ask']
                if price > furthest_price:
                    furthest_price = price
        
        if furthest_price == float('inf') or furthest_price == 0:
            furthest_price = close_price
        
        # Update FurthestPrice
        df.at[idx, 'FurthestPrice'] = round(furthest_price, 2)
        
        # Recalculate MAE for all layers
        num_layers = int(row['NumLayers'])
        
        for layer_idx in range(1, num_layers + 1):
            layer_price = row[f'Layer{layer_idx}Price']
            
            if pd.isna(layer_price):
                continue
            
            # MAE = distance from layer entry to furthest price
            if direction == "BUY":
                # For BUY: MAE = LayerPrice - FurthestPrice (Furthest is lower)
                mae = price_to_points(layer_price - furthest_price)
            else:
                # For SELL: MAE = FurthestPrice - LayerPrice (Furthest is higher)
                mae = price_to_points(furthest_price - layer_price)
            
            df.at[idx, f'Layer{layer_idx}MAE'] = round(mae, 0)
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(df)}...")
    
    # Save fixed file
    output_file = f"data/{date_compact}_RecoveryAnalysis_v3_fixed.xlsx"
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Recovery')
        add_conditional_formatting(writer, df)
    
    print(f"\nSaved fixed file to {output_file}")
    
    # Show sample verification
    print("\nSample verification (first 3 SELL positions):")
    sell_positions = df[df['Direction'] == 'SELL'].head(3)
    for idx, row in sell_positions.iterrows():
        print(f"  Row {idx}: ClosePrice={row['ClosePrice']:.2f}, FurthestPrice={row['FurthestPrice']:.2f}")
        if row['FurthestPrice'] > row['ClosePrice']:
            print(f"    ✓ FurthestPrice is HIGHER than ClosePrice (correct for SELL)")
        else:
            print(f"    ✗ ERROR: FurthestPrice should be higher")

mt5.shutdown()
print("\nFix complete!")
