"""
Regenerate all RecoveryAnalysis v3 files with corrected FurthestPrice logic
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

def get_atr_m1_60(symbol, target_time):
    """Get ATR m1(60)"""
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
        
        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)
        tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    if not tr_list:
        return 250
    
    atr = np.mean(tr_list) * 100
    return max(100, min(600, atr))

def group_into_baskets(positions, time_window_seconds=2):
    if not positions:
        return []
    sorted_pos = sorted(positions, key=lambda x: x['open_time'])
    baskets = []
    current_basket = [sorted_pos[0]]
    
    for i in range(1, len(sorted_pos)):
        prev_time = current_basket[-1]['open_time']
        curr_time = sorted_pos[i]['open_time']
        time_diff = (curr_time - prev_time).total_seconds()
        
        if time_diff <= time_window_seconds:
            current_basket.append(sorted_pos[i])
        else:
            baskets.append(current_basket)
            current_basket = [sorted_pos[i]]
    
    if current_basket:
        baskets.append(current_basket)
    return baskets

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

# Connect
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
if not mt5.initialize(path=terminal_path):
    print(f"MT5 init failed: {mt5.last_error()}")
    exit(1)

symbol = "XAUUSD+"
dates = ['2026-03-20', '2026-03-23', '2026-03-24', '2026-03-25']

for date_str in dates:
    print(f"\n{'='*80}")
    print(f"PROCESSING: {date_str}")
    print(f"{'='*80}")
    
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
            open_time = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc)
            close_time = datetime.fromtimestamp(exit_deal.time, tz=timezone.utc)
            direction = "BUY" if entry_deal.type == 0 else "SELL"
            profit = exit_deal.profit + entry_deal.commission + exit_deal.commission + exit_deal.swap
            
            all_positions.append({
                "ticket": pid,
                "direction": direction,
                "open_time": open_time,
                "close_time": close_time,
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": profit,
                "magic": entry_deal.magic
            })
    
    all_positions.sort(key=lambda x: x["open_time"])
    losing_positions = [p for p in all_positions if p["profit"] < 0]
    baskets = group_into_baskets(losing_positions, time_window_seconds=2)
    
    print(f"Baskets: {len(baskets)}")
    
    results = []
    
    for basket_idx, basket in enumerate(baskets):
        primary = basket[0]
        loss_close_time = primary["close_time"]
        target_price = primary["open_price"]
        loss_direction = primary["direction"]
        opposing_direction = "BUY" if loss_direction == "SELL" else "SELL"
        num_pos = len(basket)
        
        atr_points = get_atr_m1_60(symbol, loss_close_time)
        entry_distance = atr_points * 2.0
        window_end = loss_close_time + timedelta(minutes=120)
        
        ticks = mt5.copy_ticks_range(symbol, loss_close_time, window_end, mt5.COPY_TICKS_ALL)
        
        # Find FurthestPrice (worst price reached)
        furthest_price = None
        if ticks is not None and len(ticks) > 0:
            if loss_direction == "BUY":
                furthest_price = float('inf')
                for i in range(len(ticks)):
                    price = ticks[i]['bid']
                    if price < furthest_price:
                        furthest_price = price
            else:
                furthest_price = 0
                for i in range(len(ticks)):
                    price = ticks[i]['ask']
                    if price > furthest_price:
                        furthest_price = price
            
            if furthest_price == float('inf') or furthest_price == 0:
                furthest_price = primary["close_price"]
        
        # Count opposing
        opposing_count = 0
        for pos in all_positions:
            if pos["ticket"] in [p["ticket"] for p in basket]:
                continue
            if loss_close_time < pos["open_time"] <= window_end:
                if pos["direction"] == opposing_direction:
                    opposing_count += 1
        
        # Layer 1: immediate entry
        layers = [{
            'entry_time': loss_close_time,
            'entry_price': primary["close_price"],
            'distance': price_to_points(target_price - primary["close_price"]) if loss_direction == "BUY" else price_to_points(primary["close_price"] - target_price)
        }]
        last_entry_price = primary["close_price"]
        
        # Additional layers
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
                
                if valid and distance >= entry_distance:
                    layers.append({'entry_time': pos_time, 'entry_price': pos['open_price'], 'distance': distance})
                    last_entry_price = pos['open_price']
        
        # Check recovery
        recovered = False
        recovery_time = None
        recovery_duration = None
        
        if ticks is not None and len(ticks) > 0:
            for i in range(len(ticks)):
                tick = ticks[i]
                tick_time = datetime.fromtimestamp(tick['time'], tz=timezone.utc)
                if loss_direction == "BUY":
                    if tick['bid'] >= target_price:
                        recovered = True
                        recovery_time = tick_time
                        break
                else:
                    if tick['ask'] <= target_price:
                        recovered = True
                        recovery_time = tick_time
                        break
        
        if recovered and recovery_time:
            recovery_duration = (recovery_time - loss_close_time).total_seconds() / 60
        
        # Layer data with corrected MAE using FurthestPrice
        layer_data = {}
        for layer_idx, layer in enumerate(layers[:5]):
            layer_num = layer_idx + 1
            entry_p = layer['entry_price']
            
            if loss_direction == "BUY":
                potential = price_to_points(target_price - entry_p)
                mae = price_to_points(entry_p - furthest_price) if furthest_price else 0
            else:
                potential = price_to_points(entry_p - target_price)
                mae = price_to_points(furthest_price - entry_p) if furthest_price else 0
            
            layer_data[f'Layer{layer_num}Price'] = entry_p
            layer_data[f'Layer{layer_num}Potential'] = round(potential, 0)
            layer_data[f'Layer{layer_num}MAE'] = round(mae, 0)
        
        for l in range(len(layers) + 1, 6):
            layer_data[f'Layer{l}Price'] = None
            layer_data[f'Layer{l}Potential'] = None
            layer_data[f'Layer{l}MAE'] = None
        
        result = {
            'Date': date_str.replace('-', ''),
            'Basket': f"B{basket_idx+1:03d}",
            'NumPos': num_pos,
            'Ticket': f"P{primary['ticket']}",
            'Magic': primary['magic'],
            'Direction': loss_direction,
            'OpenTime': primary['open_time'].strftime('%H:%M:%S'),
            'CloseTime': primary['close_time'].strftime('%H:%M:%S'),
            'OpenPrice': primary['open_price'],
            'ClosePrice': primary['close_price'],
            'LossPoints': price_to_points(primary['close_price'] - primary['open_price']) if loss_direction == "BUY" else price_to_points(primary['open_price'] - primary['close_price']),
            'ATRPoints': round(atr_points, 0),
            'EntryDistance': round(entry_distance, 0),
            'NumLayers': len(layers),
            'OpposingCount': opposing_count,
            'Recovered': 'YES' if recovered else 'NO',
            'RecoveryTime': recovery_time.strftime('%H:%M:%S') if recovery_time else None,
            'RecoveryDurationMin': round(recovery_duration, 1) if recovery_duration else None,
            'FurthestPrice': round(furthest_price, 2) if furthest_price else None,
        }
        result.update(layer_data)
        results.append(result)
    
    df = pd.DataFrame(results)
    col_order = ['Date', 'Basket', 'NumPos', 'Ticket', 'Magic', 'Direction', 
                 'OpenTime', 'CloseTime', 'OpenPrice', 'ClosePrice', 'LossPoints', 
                 'ATRPoints', 'EntryDistance', 'NumLayers', 'OpposingCount', 
                 'Recovered', 'RecoveryTime', 'RecoveryDurationMin', 'FurthestPrice']
    for i in range(1, 6):
        col_order.extend([f'Layer{i}Price', f'Layer{i}Potential', f'Layer{i}MAE'])
    df = df[col_order]
    
    output_file = f"data/{date_str.replace('-', '')}_RecoveryAnalysis_FINAL.xlsx"
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Recovery')
        add_conditional_formatting(writer, df)
    
    print(f"Saved: {output_file}")

mt5.shutdown()
print("\nAll files regenerated with corrected FurthestPrice!")
