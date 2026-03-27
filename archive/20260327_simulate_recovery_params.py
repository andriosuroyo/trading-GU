"""
Simulate different Recovery parameters:
1. EntryDistance multiplier: 1x, 2x, 3x
2. RecoveryDuration: 60, 90, 120, 150, 180, 210, 240 min
3. MaxLayers: 1, 2, 3
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
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

def get_atr_m1_60(symbol, target_time):
    start_time = target_time - timedelta(minutes=60)
    ticks = mt5.copy_ticks_range(symbol, start_time, target_time, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) < 100:
        return 250
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index('time', inplace=True)
    
    ohlc = df.resample('1min').agg({'ask': ['first', 'max', 'min', 'last']})
    ohlc.columns = ['open', 'high', 'low', 'close']
    ohlc = ohlc.dropna()
    
    if len(ohlc) < 10:
        return 250
    
    tr_list = []
    for i in range(1, len(ohlc)):
        high = ohlc.iloc[i]['high']
        low = ohlc.iloc[i]['low']
        close_prev = ohlc.iloc[i-1]['close']
        tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
        tr_list.append(tr)
    
    if not tr_list:
        return 250
    
    atr = np.mean(tr_list) * 100
    return max(100, min(600, atr))

def simulate_recovery(basket, all_positions, symbol, atr_mult, max_duration, max_layers):
    """Simulate recovery with given parameters"""
    primary = basket[0]
    loss_close_time = primary["close_time"]
    target_price = primary["open_price"]
    loss_direction = primary["direction"]
    
    atr_points = get_atr_m1_60(symbol, loss_close_time)
    entry_distance = atr_points * atr_mult
    window_end = loss_close_time + timedelta(minutes=max_duration)
    
    ticks = mt5.copy_ticks_range(symbol, loss_close_time, window_end, mt5.COPY_TICKS_ALL)
    
    # Layer 1: immediate
    layers = [{
        'entry_price': primary["close_price"],
        'potential': price_to_points(target_price - primary["close_price"]) if loss_direction == "BUY" else price_to_points(primary["close_price"] - target_price)
    }]
    last_entry_price = primary["close_price"]
    
    # Additional layers (up to max_layers)
    for pos in all_positions:
        if pos["ticket"] in [p["ticket"] for p in basket]:
            continue
        pos_time = pos["open_time"]
        if not (loss_close_time < pos_time <= window_end):
            continue
        if pos["direction"] == loss_direction:
            if loss_direction == "BUY":
                distance = price_to_points(last_entry_price - pos["open_price"])
                valid = pos["open_price"] < last_entry_price
            else:
                distance = price_to_points(pos["open_price"] - last_entry_price)
                valid = pos["open_price"] > last_entry_price
            
            if valid and distance >= entry_distance and len(layers) < max_layers:
                layers.append({
                    'entry_price': pos['open_price'],
                    'potential': price_to_points(target_price - pos['open_price']) if loss_direction == "BUY" else price_to_points(pos['open_price'] - target_price)
                })
                last_entry_price = pos['open_price']
    
    # Check recovery
    recovered = False
    if ticks is not None and len(ticks) > 0:
        for i in range(len(ticks)):
            if loss_direction == "BUY":
                if ticks[i]['bid'] >= target_price:
                    recovered = True
                    break
            else:
                if ticks[i]['ask'] <= target_price:
                    recovered = True
                    break
    
    # Calculate MAE
    if recovered:
        total_profit = sum(l['potential'] for l in layers)
        total_loss = 0
    else:
        total_profit = 0
        # Calculate MAE for each layer to furthest price
        furthest_price = None
        if ticks is not None and len(ticks) > 0:
            if loss_direction == "BUY":
                furthest_price = min(ticks['bid'])
            else:
                furthest_price = max(ticks['ask'])
        
        total_loss = 0
        for layer in layers:
            if furthest_price:
                if loss_direction == "BUY":
                    mae = price_to_points(layer['entry_price'] - furthest_price)
                else:
                    mae = price_to_points(furthest_price - layer['entry_price'])
                total_loss += mae
    
    return recovered, total_profit, total_loss, len(layers)

# Connect
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
if not mt5.initialize(path=terminal_path):
    print("MT5 init failed")
    exit(1)

symbol = "XAUUSD+"

# Test configurations
atr_mults = [1.0, 2.0, 3.0]
durations = [60, 90, 120, 150, 180, 210, 240]
max_layers_list = [1, 2, 3]

# Process only March 23-25
dates = ['2026-03-23', '2026-03-24', '2026-03-25']

results = []

for date_str in dates:
    print(f"\nProcessing {date_str}...")
    
    date = datetime.strptime(date_str, '%Y-%m-%d')
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        continue
    
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    all_positions = []
    for pid, siblings in deals_by_pos.items():
        entry_deal, exit_deal = None, None
        for s in siblings:
            if s.entry == 0:
                entry_deal = s
            elif s.entry == 1:
                exit_deal = s
        if entry_deal and exit_deal:
            all_positions.append({
                "ticket": pid,
                "direction": "BUY" if entry_deal.type == 0 else "SELL",
                "open_time": datetime.fromtimestamp(entry_deal.time, tz=timezone.utc),
                "close_time": datetime.fromtimestamp(exit_deal.time, tz=timezone.utc),
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap
            })
    
    all_positions.sort(key=lambda x: x["open_time"])
    losing_positions = [p for p in all_positions if p["profit"] < 0]
    
    # Group into baskets (2 second window)
    baskets = []
    current_basket = [losing_positions[0]] if losing_positions else []
    for i in range(1, len(losing_positions)):
        if (losing_positions[i]['open_time'] - current_basket[-1]['open_time']).total_seconds() <= 2:
            current_basket.append(losing_positions[i])
        else:
            baskets.append(current_basket)
            current_basket = [losing_positions[i]]
    if current_basket:
        baskets.append(current_basket)
    
    # Test all configurations
    for atr_mult in atr_mults:
        for duration in durations:
            for max_layers in max_layers_list:
                total_profit = 0
                total_loss = 0
                recovered_count = 0
                
                for basket in baskets:
                    recovered, profit, loss, num_layers = simulate_recovery(
                        basket, all_positions, symbol, atr_mult, duration, max_layers
                    )
                    if recovered:
                        total_profit += profit
                        recovered_count += 1
                    else:
                        total_loss += loss
                
                net = total_profit - total_loss
                
                results.append({
                    'Date': date_str,
                    'ATR_Mult': atr_mult,
                    'Duration': duration,
                    'Max_Layers': max_layers,
                    'Recovered': recovered_count,
                    'Total': len(baskets),
                    'Recovery_Rate': recovered_count / len(baskets) * 100 if baskets else 0,
                    'Gross_Profit': total_profit,
                    'Gross_Loss': total_loss,
                    'Net_Profit': net
                })

mt5.shutdown()

# Create DataFrame and show results
df_results = pd.DataFrame(results)

print("\n" + "="*100)
print("SIMULATION RESULTS - BEST CONFIGURATIONS BY DATE")
print("="*100)

for date in dates:
    date_results = df_results[df_results['Date'] == date_str]
    print(f"\n{date}:")
    
    # Top 5 by Net Profit
    top5 = date_results.nlargest(5, 'Net_Profit')
    print("\n  Top 5 by Net Profit:")
    for idx, row in top5.iterrows():
        print(f"    ATR{row['ATR_Mult']:.0f}x, {row['Duration']}min, {row['Max_Layers']}layers: "
              f"Net={row['Net_Profit']:+.0f} ({row['Recovered']}/{row['Total']} = {row['Recovery_Rate']:.1f}%)")
    
    # Best overall
    best = date_results.loc[date_results['Net_Profit'].idxmax()]
    print(f"\n  BEST: ATR{best['ATR_Mult']:.0f}x, {best['Duration']}min, {best['Max_Layers']}layers")
    print(f"        Net: {best['Net_Profit']:+,.0f} points, Recovery: {best['Recovery_Rate']:.1f}%")

print("\n" + "="*100)
print("OVERALL BEST (Combined):")
print("="*100)

# Group by config and sum
combined = df_results.groupby(['ATR_Mult', 'Duration', 'Max_Layers']).agg({
    'Net_Profit': 'sum',
    'Gross_Profit': 'sum',
    'Gross_Loss': 'sum',
    'Recovered': 'sum',
    'Total': 'sum'
}).reset_index()

combined['Recovery_Rate'] = combined['Recovered'] / combined['Total'] * 100

top10 = combined.nlargest(10, 'Net_Profit')
for idx, row in top10.iterrows():
    print(f"ATR{row['ATR_Mult']:.0f}x, {int(row['Duration'])}min, {int(row['Max_Layers'])}layers: "
          f"Net={row['Net_Profit']:+.0f} (Recovered: {row['Recovered']}/{row['Total']})")

print("\n" + "="*100)
