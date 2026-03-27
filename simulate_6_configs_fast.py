"""
Fast simulation - Pre-fetch all tick data
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

def check_recovery(ticks, direction, target_price):
    """Check if price recovered to target within ticks"""
    if ticks is None or len(ticks) == 0:
        return False
    
    for i in range(len(ticks)):
        if direction == "BUY":
            if ticks[i]['bid'] >= target_price:
                return True
        else:
            if ticks[i]['ask'] <= target_price:
                return True
    return False

def get_furthest_price(ticks, direction):
    """Get worst price reached"""
    if ticks is None or len(ticks) == 0:
        return None
    
    if direction == "BUY":
        return min(ticks['bid'])
    else:
        return max(ticks['ask'])

# Connect
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print("MT5 init failed")
    exit(1)

symbol = "XAUUSD+"
configs = [(2, 1.0), (2, 2.0), (2, 3.0), (3, 1.0), (3, 2.0), (3, 3.0)]
dates = ['2026-03-23', '2026-03-24', '2026-03-25']

print('='*100)
print('RECOVERY SIMULATION - 6 CONFIGURATIONS (Fast)')
print('='*100)

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
                "profit": exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap,
                "atr": None,  # Will be calculated
                "ticks": None  # Will be fetched
            })
    
    all_positions.sort(key=lambda x: x["open_time"])
    losing_positions = [p for p in all_positions if p["profit"] < 0]
    
    # Group into baskets
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
    
    # Pre-fetch ATR and ticks for each basket
    print('Fetching ATR and tick data...')
    for i, basket in enumerate(baskets):
        primary = basket[0]
        primary['atr'] = get_atr_m1_60(symbol, primary['close_time'])
        window_end = primary['close_time'] + timedelta(minutes=120)
        primary['ticks'] = mt5.copy_ticks_range(symbol, primary['close_time'], window_end, mt5.COPY_TICKS_ALL)
        primary['furthest'] = get_furthest_price(primary['ticks'], primary['direction'])
        primary['recovered'] = check_recovery(primary['ticks'], primary['direction'], primary['open_price'])
        if i % 10 == 0:
            print(f'  {i+1}/{len(baskets)}...')
    
    print('Simulating configurations...')
    
    # Test each configuration
    results = []
    
    for max_layers, atr_mult in configs:
        for use_layer1 in [True, False]:
            total_profit = 0
            total_loss = 0
            recovered_count = 0
            no_entry_count = 0
            
            for basket in baskets:
                primary = basket[0]
                target_price = primary['open_price']
                loss_direction = primary['direction']
                entry_distance = primary['atr'] * atr_mult
                
                layers = []
                last_entry_price = None
                
                if use_layer1:
                    layers.append({
                        'entry_price': primary['close_price'],
                        'potential': price_to_points(target_price - primary['close_price']) if loss_direction == "BUY" else price_to_points(primary['close_price'] - target_price)
                    })
                    last_entry_price = primary['close_price']
                
                # Additional layers
                for pos in all_positions:
                    if pos["ticket"] in [p["ticket"] for p in basket]:
                        continue
                    if not (primary['close_time'] < pos["open_time"] <= primary['close_time'] + timedelta(minutes=120)):
                        continue
                    if pos["direction"] == loss_direction:
                        if len(layers) == 0:
                            if loss_direction == "BUY":
                                distance = price_to_points(target_price - pos["open_price"])
                                valid = pos["open_price"] < target_price
                            else:
                                distance = price_to_points(pos["open_price"] - target_price)
                                valid = pos["open_price"] > target_price
                        else:
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
                    no_entry_count += 1
                    continue
                
                # Calculate P&L
                if primary['recovered']:
                    total_profit += sum(l['potential'] for l in layers)
                    recovered_count += 1
                else:
                    furthest = primary['furthest']
                    if furthest:
                        for layer in layers:
                            if loss_direction == "BUY":
                                mae = price_to_points(layer['entry_price'] - furthest)
                            else:
                                mae = price_to_points(furthest - layer['entry_price'])
                            total_loss += mae
            
            net = total_profit - total_loss
            valid_baskets = len(baskets) - no_entry_count
            
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
    print(f'\n{"Config":<15} {"Layer1":<10} {"Net":>12} {"Rec":>5} {"Tot":>4} {"Rate":>7} {"NoEntry":>8}')
    print('-' * 75)
    
    for r in results:
        layer1_str = "Yes" if r['layer1'] else "No"
        print(f"{r['config']:<15} {layer1_str:<10} {r['net']:+12,.0f} {r['recovered']:>5} {r['total']:>4} {r['rate']:>6.1f}% {r['no_entry']:>8}")

mt5.shutdown()
print('\n' + '='*100)
