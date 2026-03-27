"""
Simulate Layered Recovery Strategy on Historical Data

Entry Rules:
- Wait for GU to open same-direction position after loss
- EntryDistanceMin = ATR m1(60) * Multiplier (in points)
- LayerSpacing = same distance
- Continue layering until: RemTime=0 OR Opp>=10 OR Price recovers

All layers close together as RecoveryBasket
"""
import MetaTrader5 as mt5
import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import numpy as np

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

def get_atr_points(df_ticks):
    """Calculate ATR m1(60) equivalent from tick data"""
    if df_ticks is None or len(df_ticks) < 60:
        return 200  # Default 200 points (ATR 2.00)
    
    # Calculate 1-minute candles from ticks
    # Simplified: use last 60 minutes of price movement
    prices = df_ticks['close'] if 'close' in df_ticks.columns else (df_ticks['bid'] + df_ticks['ask']) / 2
    
    if len(prices) < 2:
        return 200
    
    # Estimate ATR based on price range over last hour
    price_range = (prices.max() - prices.min()) * 100
    atr_estimate = price_range / 2  # Rough estimate
    
    return max(100, min(500, atr_estimate))  # Clamp between 100-500 points

def price_to_points(price_diff):
    return abs(price_diff) * 100

# Connect to MT5
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    exit(1)

print(f"Connected to: {mt5.account_info().server}")

# Configuration
ATR_MULTIPLIER = 2.0
RECOVERY_WINDOW_MIN = 120
OPPOSING_THRESHOLD = 10
symbol = "XAUUSD+"

# Load RecoveryAnalysis files
dates = ['2026-03-20', '2026-03-23', '2026-03-24']
all_recovery_data = []

for date_str in dates:
    df = pd.read_excel(f'data/{date_str}_RecoveryAnalysis.xlsx')
    all_recovery_data.append(df)
    print(f"Loaded {date_str}: {len(df)} losses")

df_losses = pd.concat(all_recovery_data, ignore_index=True)
print(f"\nTotal losses to simulate: {len(df_losses)}")

results = []

for idx, loss in df_losses.iterrows():
    date_str = loss['Date']
    ticket = loss['Ticket']
    direction = loss['Direction']
    open_price = loss['OpenPrice']  # Target
    close_price = loss['ClosePrice']  # Where SL hit (Layer 1 entry reference)
    close_time_str = loss['CloseTime']
    recovered = loss['Recovered']
    recovery_time_str = loss['RecoveryTime']
    
    # Parse times
    close_time = datetime.strptime(f"{date_str} {close_time_str}", "%Y-%m-%d %H:%M:%S")
    close_time = close_time.replace(tzinfo=timezone.utc)
    
    window_end = close_time + timedelta(minutes=RECOVERY_WINDOW_MIN)
    
    # Get ATR at close time (fetch ticks 60 min before)
    atr_start = close_time - timedelta(minutes=60)
    atr_ticks = mt5.copy_ticks_range(symbol, atr_start, close_time, mt5.COPY_TICKS_ALL)
    
    atr_points = 200  # Default
    if atr_ticks is not None and len(atr_ticks) > 0:
        # Simple ATR estimation: average range over available data
        highs = atr_ticks['ask']
        lows = atr_ticks['bid']
        if len(highs) > 0:
            avg_range = (highs.max() - lows.min()) * 100
            atr_points = max(100, min(400, avg_range * 0.5))
    
    entry_distance = atr_points * ATR_MULTIPLIER
    
    # Fetch all positions for this date to simulate GU entries
    date = datetime.strptime(date_str, '%Y-%m-%d')
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        continue
    
    # Build position list
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    all_positions = []
    for pid, siblings in deals_by_pos.items():
        entry_deal = None
        for s in siblings:
            if s.entry == 0:
                entry_deal = s
                break
        if entry_deal:
            open_t = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc)
            dir_str = "BUY" if entry_deal.type == 0 else "SELL"
            all_positions.append({
                'ticket': pid,
                'direction': dir_str,
                'open_time': open_t,
                'open_price': entry_deal.price,
                'magic': entry_deal.magic
            })
    
    all_positions.sort(key=lambda x: x['open_time'])
    
    # Simulate layered entries
    layers = []
    layer_entries = []
    last_entry_price = close_price
    opposing_count = 0
    current_time = close_time
    basket_closed = False
    close_reason = None
    
    # Get ticks for price tracking
    ticks = mt5.copy_ticks_range(symbol, close_time, window_end, mt5.COPY_TICKS_ALL)
    
    for pos in all_positions:
        if pos['ticket'] == ticket:
            continue
        
        pos_time = pos['open_time']
        
        # Check if window expired
        if pos_time > window_end:
            basket_closed = True
            close_reason = "TIMEOUT"
            break
        
        # Check opposing count
        if pos['direction'] != direction:
            opposing_count += 1
            if opposing_count >= OPPOSING_THRESHOLD:
                basket_closed = True
                close_reason = "OPPOSING_LIMIT"
                current_time = pos_time
                break
        
        # Check for same-direction GU position (potential layer entry)
        if pos['direction'] == direction:
            distance_from_last = price_to_points(last_entry_price - pos['open_price'])
            
            # For first layer: distance from close_price
            # For subsequent: distance from last layer entry
            if len(layers) == 0:
                distance_needed = entry_distance
                distance_actual = price_to_points(close_price - pos['open_price'])
            else:
                distance_needed = entry_distance
                distance_actual = price_to_points(last_entry_price - pos['open_price'])
            
            # Check if GU entry is sufficiently far (better price)
            if distance_actual >= distance_needed:
                # Open new layer
                layers.append({
                    'entry_time': pos_time,
                    'entry_price': pos['open_price'],
                    'distance_from_target': price_to_points(open_price - pos['open_price']),
                    'layer_num': len(layers) + 1
                })
                last_entry_price = pos['open_price']
                layer_entries.append(pos_time)
        
        # Check if price recovered (hit target) - simplified check
        # In reality would need tick-by-tick check
        current_time = pos_time
    
    # Check final outcome
    final_outcome = "UNKNOWN"
    if recovered == 'YES' and len(layers) > 0:
        final_outcome = "RECOVERED"
    elif recovered == 'NO' or len(layers) == 0:
        final_outcome = "LOST"
    
    # Calculate MAE for each layer
    layer_mae = []
    if ticks is not None and len(ticks) > 0 and len(layers) > 0:
        for i, layer in enumerate(layers):
            entry_p = layer['entry_price']
            entry_t = layer['entry_time']
            
            # Find worst price after entry
            worst_mae = 0
            for tick_idx in range(len(ticks)):
                tick = ticks[tick_idx]
                tick_time = datetime.fromtimestamp(tick['time'], tz=timezone.utc)
                if tick_time < entry_t:
                    continue
                
                if direction == "BUY":
                    price = tick['bid']
                    mae = price_to_points(entry_p - price)
                else:
                    price = tick['ask']
                    mae = price_to_points(price - entry_p)
                
                worst_mae = max(worst_mae, mae)
            
            layer_mae.append(worst_mae)
    
    results.append({
        'Date': date_str,
        'Ticket': ticket,
        'Magic': loss['Magic'],
        'Direction': direction,
        'ATR_Points': round(atr_points, 0),
        'EntryDistance': round(entry_distance, 0),
        'NumLayers': len(layers),
        'Layers': str([f"L{i+1}@{l['entry_price']}" for i, l in enumerate(layers)]),
        'Outcome': final_outcome,
        'CloseReason': close_reason,
        'TotalPotential': sum([l['distance_from_target'] for l in layers]) if layers else 0,
        'MaxMAE': max(layer_mae) if layer_mae else 0,
        'AvgMAE': sum(layer_mae)/len(layer_mae) if layer_mae else 0
    })
    
    if (idx + 1) % 20 == 0:
        print(f"Processed {idx + 1}/{len(df_losses)}...")

mt5.shutdown()

# Create DataFrame
df_results = pd.DataFrame(results)

# Save
df_results.to_csv('data/LayeredRecovery_Simulation.csv', index=False)

print("\n" + "="*100)
print("LAYERED RECOVERY SIMULATION COMPLETE")
print("="*100)

print(f"\nConfiguration: ATR×{ATR_MULTIPLIER}, EntryDistance=ATR×{ATR_MULTIPLIER}")

# Summary
print("\nLAYER STATISTICS:")
layer_dist = df_results['NumLayers'].value_counts().sort_index()
print(layer_dist.to_string())

print(f"\nMax Layers Observed: {df_results['NumLayers'].max()}")
print(f"Average Layers: {df_results['NumLayers'].mean():.2f}")

# By outcome
print("\n" + "="*100)
print("BY OUTCOME")
print("="*100)

recovered_df = df_results[df_results['Outcome'] == 'RECOVERED']
lost_df = df_results[df_results['Outcome'] == 'LOST']

print(f"\nRECOVERED ({len(recovered_df)} positions):")
if len(recovered_df) > 0:
    print(f"  Max Layers: {recovered_df['NumLayers'].max()}")
    print(f"  Avg Layers: {recovered_df['NumLayers'].mean():.2f}")
    print(f"  Layer distribution:")
    print(recovered_df['NumLayers'].value_counts().sort_index().to_string())

print(f"\nLOST ({len(lost_df)} positions):")
if len(lost_df) > 0:
    print(f"  Max Layers: {lost_df['NumLayers'].max()}")
    print(f"  Avg Layers: {lost_df['NumLayers'].mean():.2f}")
    print(f"  Layer distribution:")
    print(lost_df['NumLayers'].value_counts().sort_index().to_string())

# MAE Analysis
print("\n" + "="*100)
print("MAE BY LAYER COUNT")
print("="*100)

for layer_count in sorted(df_results['NumLayers'].unique()):
    subset = df_results[df_results['NumLayers'] == layer_count]
    print(f"\n{layer_count} Layer(s) - {len(subset)} positions:")
    print(f"  Max MAE: {subset['MaxMAE'].max():.0f} points")
    print(f"  Avg Max MAE: {subset['MaxMAE'].mean():.0f} points")
    print(f"  Outcomes: {subset['Outcome'].value_counts().to_dict()}")

print(f"\nSaved to data/LayeredRecovery_Simulation.csv")
