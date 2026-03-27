"""
Fix RecoveryAnalysis with correct layer tracking
ATR-based entry spacing: Only count layers that meet EntryDistance criteria
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
    return abs(price_diff) * 100

# Connect to MT5
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    exit(1)

print(f"Connected to: {mt5.account_info().server}")

ATR_MULTIPLIER = 2.0
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
        print(f"No deals")
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
    print(f"Losing positions: {len(losing_positions)}")
    
    results = []
    
    for idx, loss in enumerate(losing_positions):
        loss_close_time = loss["close_time"]
        target_price = loss["open_price"]
        loss_direction = loss["direction"]
        opposing_direction = "BUY" if loss_direction == "SELL" else "SELL"
        
        # Get ATR
        atr_start = loss_close_time - timedelta(minutes=60)
        atr_ticks = mt5.copy_ticks_range(symbol, atr_start, loss_close_time, mt5.COPY_TICKS_ALL)
        atr_points = 200
        if atr_ticks is not None and len(atr_ticks) > 0:
            highs = atr_ticks['ask']
            lows = atr_ticks['bid']
            if len(highs) > 0:
                avg_range = (highs.max() - lows.min()) * 100
                atr_points = max(100, min(400, avg_range * 0.5))
        
        entry_distance = atr_points * ATR_MULTIPLIER
        
        # Track layers with proper ATR-based spacing
        layers = []
        last_entry_price = None
        opposing_count = 0
        
        for pos in all_positions:
            if pos["ticket"] == loss["ticket"]:
                continue
            
            pos_time = pos["open_time"]
            
            # Count opposing
            if pos["direction"] == opposing_direction and pos_time > loss_close_time:
                opposing_count += 1
            
            # Check for same-direction entry
            if pos["direction"] == loss_direction and pos_time > loss_close_time:
                # Determine distance needed
                distance_needed = entry_distance
                
                if len(layers) == 0:
                    # First layer: distance from InitialOpenPrice
                    # For BUY recovery: GU entry must be BELOW InitialOpenPrice
                    # For SELL recovery: GU entry must be ABOVE InitialOpenPrice
                    if loss_direction == "BUY":
                        distance = price_to_points(target_price - pos["open_price"])
                        valid = pos["open_price"] < target_price  # Better price for BUY
                    else:
                        distance = price_to_points(pos["open_price"] - target_price)
                        valid = pos["open_price"] > target_price  # Better price for SELL
                else:
                    # Subsequent layers: distance from last layer entry
                    if loss_direction == "BUY":
                        distance = price_to_points(last_entry_price - pos["open_price"])
                        valid = pos["open_price"] < last_entry_price  # Even lower
                    else:
                        distance = price_to_points(pos["open_price"] - last_entry_price)
                        valid = pos["open_price"] > last_entry_price  # Even higher
                
                if valid and distance >= distance_needed:
                    layers.append({
                        'entry_time': pos_time,
                        'entry_price': pos['open_price'],
                        'distance': distance
                    })
                    last_entry_price = pos['open_price']
        
        # Check recovery within 240min
        recovery_deadline = loss_close_time + timedelta(minutes=240)
        ticks = mt5.copy_ticks_range(symbol, loss_close_time, recovery_deadline, mt5.COPY_TICKS_ALL)
        
        recovered = False
        recovery_time = None
        recovery_duration = None
        
        if ticks is not None and len(ticks) > 0:
            for i in range(len(ticks)):
                tick = ticks[i]
                tick_time = datetime.fromtimestamp(tick['time'], tz=timezone.utc)
                
                if loss_direction == "BUY":
                    price = tick['bid']
                    if price >= target_price:
                        recovered = True
                        recovery_time = tick_time
                        break
                else:
                    price = tick['ask']
                    if price <= target_price:
                        recovered = True
                        recovery_time = tick_time
                        break
        
        if recovered and recovery_time:
            recovery_duration = (recovery_time - loss_close_time).total_seconds() / 60
        
        # Calculate MAE for each layer
        layer_data = {}
        
        for layer_idx, layer in enumerate(layers[:5]):
            layer_num = layer_idx + 1
            entry_p = layer['entry_price']
            entry_t = layer['entry_time']
            
            worst_mae = 0
            if ticks is not None:
                for tick_idx in range(len(ticks)):
                    tick = ticks[tick_idx]
                    tick_time = datetime.fromtimestamp(tick['time'], tz=timezone.utc)
                    if tick_time < entry_t:
                        continue
                    
                    if loss_direction == "BUY":
                        price = tick['bid']
                        mae = price_to_points(entry_p - price)
                    else:
                        price = tick['ask']
                        mae = price_to_points(price - entry_p)
                    
                    worst_mae = max(worst_mae, mae)
            
            tp_price = target_price
            dist = price_to_points(tp_price - entry_p) if loss_direction == "BUY" else price_to_points(entry_p - tp_price)
            
            layer_data[f'Layer{layer_num}Open'] = entry_p
            layer_data[f'Layer{layer_num}TP'] = tp_price
            layer_data[f'Layer{layer_num}MAE'] = round(worst_mae, 0)
            layer_data[f'Layer{layer_num}Dist'] = round(dist, 0)
        
        for l in range(len(layers) + 1, 6):
            layer_data[f'Layer{l}Open'] = None
            layer_data[f'Layer{l}TP'] = None
            layer_data[f'Layer{l}MAE'] = None
            layer_data[f'Layer{l}Dist'] = None
        
        result = {
            'Date': date_str,
            'Ticket': loss['ticket'],
            'Magic': loss['magic'],
            'Direction': loss_direction,
            'OpenTime': loss['open_time'].strftime('%H:%M:%S'),
            'CloseTime': loss['close_time'].strftime('%H:%M:%S'),
            'OpenPrice': loss['open_price'],
            'ClosePrice': loss['close_price'],
            'LossAmount': loss['profit'],
            'LossPoints': price_to_points(loss['close_price'] - loss['open_price']) if loss_direction == "BUY" else price_to_points(loss['open_price'] - loss['close_price']),
            'ATR_Points': round(atr_points, 0),
            'EntryDistance': round(entry_distance, 0),
            'NumLayers': len(layers),
            'OpposingCount': opposing_count,
            'Recovered': 'YES' if recovered else 'NO',
            'RecoveryTime': recovery_time.strftime('%H:%M:%S') if recovery_time else None,
            'RecoveryDurationMin': round(recovery_duration, 1) if recovery_duration else None,
        }
        result.update(layer_data)
        results.append(result)
    
    df = pd.DataFrame(results)
    output_file = f"data/{date_str}_RecoveryAnalysis.xlsx"
    df.to_excel(output_file, index=False, sheet_name='Recovery')
    print(f"\nSaved to {output_file}")
    
    print(f"\nSummary:")
    print(f"  Total: {len(df)}")
    print(f"  Recovered: {len(df[df['Recovered'] == 'YES'])}")
    layer_dist = df['NumLayers'].value_counts().sort_index()
    print(f"  Layers: {dict((int(k), int(v)) for k, v in layer_dist.items())}")

mt5.shutdown()
print("\nDone!")
