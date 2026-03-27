"""
Simulate 6 configurations:
- MaxLayers: 2 or 3
- ATR Multiplier: 1x, 2x, 3x
- With and without Layer1 (immediate entry)

Calculate net profit for each.
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

def simulate_basket(basket, all_positions, symbol, max_layers, atr_mult, use_layer1, duration_min=120):
    """
    Simulate recovery for a basket
    use_layer1: True = immediate entry at SL, False = wait for GU confirmation
    """
    primary = basket[0]
    loss_close_time = primary["close_time"]
    target_price = primary["open_price"]
    loss_direction = primary["direction"]
    
    atr_points = get_atr_m1_60(symbol, loss_close_time)
    entry_distance = atr_points * atr_mult
    window_end = loss_close_time + timedelta(minutes=duration_min)
    
    ticks = mt5.copy_ticks_range(symbol, loss_close_time, window_end, mt5.COPY_TICKS_ALL)
    
    layers = []
    last_entry_price = None
    
    if use_layer1:
        # Layer 1: immediate entry at SL hit
        layers.append({
            'entry_price': primary["close_price"],
            'potential': price_to_points(target_price - primary["close_price"]) if loss_direction == "BUY" else price_to_points(primary["close_price"] - target_price)
        })
        last_entry_price = primary["close_price"]
    
    # Additional layers: wait for GU confirmation
    for pos in all_positions:
        if pos["ticket"] in [p["ticket"] for p in basket]:
            continue
        pos_time = pos["open_time"]
        if not (loss_close_time < pos_time <= window_end):
            continue
        if pos["direction"] == loss_direction:
            # First layer (if no Layer1) or subsequent layers
            if len(layers) == 0:
                # First entry - distance from InitialOpenPrice
                if loss_direction == "BUY":
                    distance = price_to_points(target_price - pos["open_price"])
                    valid = pos["open_price"] < target_price
                else:
                    distance = price_to_points(pos["open_price"] - target_price)
                    valid = pos["open_price"] > target_price
            else:
                # Subsequent layers - distance from last entry
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
    
    if len(layers) == 0:
        return None, 0, 0  # No entry triggered
    
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
    
    # Calculate profit/loss
    if recovered:
        total_profit = sum(l['potential'] for l in layers)
        total_loss = 0
    else:
        total_profit = 0
        # Find furthest price for MAE
        furthest_price = None
        if ticks is not None and len(ticks) > 0:
            if loss_direction == "BUY":
                furthest_price = min(ticks['bid'])
            else:
                furthest_price = max(ticks['ask'])
        
        total_loss = 0
        if furthest_price:
            for layer in layers:
                if loss_direction == "BUY":
                    mae = price_to_points(layer['entry_price'] - furthest_price)
                else:
                    mae = price_to_points(furthest_price - layer['entry_price'])
                total_loss += mae
    
    return recovered, total_profit, total_loss

# Connect to MT5
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print("MT5 init failed")
    exit(1)

symbol = "XAUUSD+"

# Test configurations
configs = [
    (2, 1.0), (2, 2.0), (2, 3.0),
    (3, 1.0), (3, 2.0), (3, 3.0)
]

# Process dates
dates = ['2026-03-23', '2026-03-24', '2026-03-25']

print('='*100)
print('RECOVERY SIMULATION - 6 CONFIGURATIONS')
print('='*100)
print()

for date_str in dates:
    print(f'\n{"="*100}')
    print(f'{date_str}')
    print(f'{"="*100}')
    
    date = datetime.strptime(date_str, '%Y-%m-%d')
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        continue
    
    # Build positions
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
    if losing_positions:
        current_basket = [losing_positions[0]]
        for i in range(1, len(losing_positions)):
            if (losing_positions[i]['open_time'] - current_basket[-1]['open_time']).total_seconds() <= 2:
                current_basket.append(losing_positions[i])
            else:
                baskets.append(current_basket)
                current_basket = [losing_positions[i]]
        if current_basket:
            baskets.append(current_basket)
    
    print(f'Total baskets: {len(baskets)}')
    
    # Test each configuration
    results = []
    
    for max_layers, atr_mult in configs:
        for use_layer1 in [True, False]:
            total_profit = 0
            total_loss = 0
            recovered_count = 0
            no_entry_count = 0
            
            for basket in baskets:
                recovered, profit, loss = simulate_basket(
                    basket, all_positions, symbol, max_layers, atr_mult, use_layer1
                )
                
                if recovered is None:
                    no_entry_count += 1
                elif recovered:
                    total_profit += profit
                    recovered_count += 1
                else:
                    total_loss += loss
            
            net = total_profit - total_loss
            valid_baskets = len(baskets) - no_entry_count
            
            layer1_status = "WITH Layer1" if use_layer1 else "NO Layer1"
            
            results.append({
                'config': f"Max{max_layers}+Mult{atr_mult:.0f}x",
                'layer1': use_layer1,
                'net': net,
                'profit': total_profit,
                'loss': total_loss,
                'recovered': recovered_count,
                'total': valid_baskets,
                'no_entry': no_entry_count,
                'rate': recovered_count / valid_baskets * 100 if valid_baskets > 0 else 0
            })
    
    # Print results
    print(f'\n{"Config":<15} {"Layer1":<12} {"Net":>12} {"Rec":>5} {"Tot":>4} {"Rate":>6} {"NoEntry":>8}')
    print('-' * 80)
    
    for r in results:
        layer1_str = "Yes" if r['layer1'] else "No"
        print(f"{r['config']:<15} {layer1_str:<12} {r['net']:+12,.0f} {r['recovered']:>5} {r['total']:>4} {r['rate']:>5.1f}% {r['no_entry']:>8}")

mt5.shutdown()
print('\n' + '='*100)
print('Simulation complete!')
