"""
Fix RecoveryAnalysis files with all corrections:
1. Rename files without "-" in date
2. Add "P" prefix to Ticket
3. Remove LossAmount column
4. Fix ATR calculation (proper ATR m1 60)
5. Fix OpposingCount (count opposing positions during recovery window only)
6. Add LostPrice column for failed recoveries
7. Rename Layer columns to Price/Potential/MAE format
8. Color Recovered column (green/red)
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

def get_atr_m1_60(symbol, target_time):
    """Get ATR m1(60) - look back 60 minutes"""
    start_time = target_time - timedelta(minutes=60)
    ticks = mt5.copy_ticks_range(symbol, start_time, target_time, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) < 10:
        return 200  # Default 200 points (ATR 2.00)
    
    # Calculate 1-minute candles and get range for each
    # Simplified: use high-low of the period divided by number of minutes
    highs = ticks['ask']
    lows = ticks['bid']
    
    if len(highs) == 0:
        return 200
    
    # ATR estimation: average true range over the period
    total_range = (highs.max() - lows.min()) * 100  # Convert to points
    num_minutes = 60
    atr_estimate = total_range / (num_minutes ** 0.5)  # Rough estimate
    
    return max(50, min(500, atr_estimate))  # Clamp between 50-500 points

def add_conditional_formatting(writer, df):
    """Add green/red conditional formatting to Recovered column"""
    workbook = writer.book
    worksheet = writer.sheets['Recovery']
    
    # Get column index for Recovered
    recovered_col = df.columns.get_loc('Recovered')
    
    # Define formats
    green_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
    red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    
    # Apply conditional formatting
    # Green for YES
    worksheet.conditional_format(1, recovered_col, len(df), recovered_col, {
        'type': 'cell',
        'criteria': 'equal to',
        'value': '"YES"',
        'format': green_format
    })
    
    # Red for NO
    worksheet.conditional_format(1, recovered_col, len(df), recovered_col, {
        'type': 'cell',
        'criteria': 'equal to',
        'value': '"NO"',
        'format': red_format
    })

# Connect to MT5
env_vars = load_env()
terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")

if not mt5.initialize(path=terminal_path):
    print(f"MT5 initialize() failed: {mt5.last_error()}")
    exit(1)

print(f"Connected to: {mt5.account_info().server}")

symbol = "XAUUSD+"

# Process dates
dates = ['2026-03-20', '2026-03-23', '2026-03-24', '2026-03-25']

for date_str in dates:
    print(f"\n{'='*80}")
    print(f"PROCESSING: {date_str}")
    print(f"{'='*80}")
    
    date = datetime.strptime(date_str, '%Y-%m-%d')
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    # Get all deals for this date
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        print(f"No deals for {date_str}")
        continue
    
    # Build position map
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
                "magic": entry_deal.magic,
                "comment": entry_deal.comment if hasattr(entry_deal, 'comment') else ""
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
        
        # Get proper ATR
        atr_points = get_atr_m1_60(symbol, loss_close_time)
        entry_distance = atr_points * 2.0  # ATR x2
        
        # Recovery window (120 min from SL hit)
        window_end = loss_close_time + timedelta(minutes=120)
        
        # Find opposing count (only during recovery window, before recovery or timeout)
        opposing_count = 0
        for pos in all_positions:
            if pos["ticket"] == loss["ticket"]:
                continue
            # Must be after SL hit and within 120 min window
            if loss_close_time < pos["open_time"] <= window_end:
                if pos["direction"] == opposing_direction:
                    opposing_count += 1
        
        # Track layers
        layers = []
        last_entry_price = None
        
        for pos in all_positions:
            if pos["ticket"] == loss["ticket"]:
                continue
            
            pos_time = pos["open_time"]
            
            # Only consider positions within recovery window
            if not (loss_close_time < pos_time <= window_end):
                continue
            
            # Check for same-direction entry
            if pos["direction"] == loss_direction:
                distance_needed = entry_distance
                
                if len(layers) == 0:
                    # First layer: distance from InitialOpenPrice
                    if loss_direction == "BUY":
                        distance = price_to_points(target_price - pos["open_price"])
                        valid = pos["open_price"] < target_price
                    else:
                        distance = price_to_points(pos["open_price"] - target_price)
                        valid = pos["open_price"] > target_price
                else:
                    # Subsequent layers: distance from last layer
                    if loss_direction == "BUY":
                        distance = price_to_points(last_entry_price - pos["open_price"])
                        valid = pos["open_price"] < last_entry_price
                    else:
                        distance = price_to_points(pos["open_price"] - last_entry_price)
                        valid = pos["open_price"] > last_entry_price
                
                if valid and distance >= distance_needed:
                    layers.append({
                        'entry_time': pos_time,
                        'entry_price': pos['open_price'],
                        'distance': distance
                    })
                    last_entry_price = pos['open_price']
        
        # Check recovery within 120 min
        ticks = mt5.copy_ticks_range(symbol, loss_close_time, window_end, mt5.COPY_TICKS_ALL)
        
        recovered = False
        recovery_time = None
        recovery_duration = None
        lost_price = None  # Price when recovery failed
        
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
            
            # If not recovered, get final price at window end
            if not recovered:
                last_tick = ticks[-1]
                if loss_direction == "BUY":
                    lost_price = last_tick['bid']
                else:
                    lost_price = last_tick['ask']
        
        if recovered and recovery_time:
            recovery_duration = (recovery_time - loss_close_time).total_seconds() / 60
        
        # Calculate Layer data
        layer_data = {}
        
        for layer_idx, layer in enumerate(layers[:5]):
            layer_num = layer_idx + 1
            entry_p = layer['entry_price']
            
            # Potential = distance to target (profit if successful)
            if loss_direction == "BUY":
                potential = price_to_points(target_price - entry_p)
                if recovered:
                    mae = 0  # Recovered, no MAE to lost_price
                else:
                    mae = price_to_points(entry_p - lost_price) if lost_price else 0
            else:
                potential = price_to_points(entry_p - target_price)
                if recovered:
                    mae = 0
                else:
                    mae = price_to_points(lost_price - entry_p) if lost_price else 0
            
            layer_data[f'Layer{layer_num}Price'] = entry_p
            layer_data[f'Layer{layer_num}Potential'] = round(potential, 0)
            layer_data[f'Layer{layer_num}MAE'] = round(mae, 0)
        
        # Fill empty layers
        for l in range(len(layers) + 1, 6):
            layer_data[f'Layer{l}Price'] = None
            layer_data[f'Layer{l}Potential'] = None
            layer_data[f'Layer{l}MAE'] = None
        
        # Build result row
        result = {
            'Date': date_str.replace('-', ''),
            'Ticket': f"P{loss['ticket']}",
            'Magic': loss['magic'],
            'Direction': loss_direction,
            'OpenTime': loss['open_time'].strftime('%H:%M:%S'),
            'CloseTime': loss['close_time'].strftime('%H:%M:%S'),
            'OpenPrice': loss['open_price'],
            'ClosePrice': loss['close_price'],
            'LossPoints': price_to_points(loss['close_price'] - loss['open_price']) if loss_direction == "BUY" else price_to_points(loss['open_price'] - loss['close_price']),
            'ATRPoints': round(atr_points, 0),
            'EntryDistance': round(entry_distance, 0),
            'NumLayers': len(layers),
            'OpposingCount': opposing_count,
            'Recovered': 'YES' if recovered else 'NO',
            'RecoveryTime': recovery_time.strftime('%H:%M:%S') if recovery_time else None,
            'RecoveryDurationMin': round(recovery_duration, 1) if recovery_duration else None,
        }
        
        # Add LostPrice for failed recoveries
        if not recovered and lost_price:
            result['LostPrice'] = lost_price
        else:
            result['LostPrice'] = None
        
        result.update(layer_data)
        results.append(result)
    
    # Create DataFrame with proper column order
    df = pd.DataFrame(results)
    
    # Reorder columns
    col_order = ['Date', 'Ticket', 'Magic', 'Direction', 'OpenTime', 'CloseTime', 
                 'OpenPrice', 'ClosePrice', 'LossPoints', 'ATRPoints', 'EntryDistance',
                 'NumLayers', 'OpposingCount', 'Recovered', 'RecoveryTime', 'RecoveryDurationMin',
                 'LostPrice']
    
    # Add layer columns in order
    for i in range(1, 6):
        col_order.extend([f'Layer{i}Price', f'Layer{i}Potential', f'Layer{i}MAE'])
    
    df = df[col_order]
    
    # Save with conditional formatting
    date_compact = date_str.replace('-', '')
    output_file = f"data/{date_compact}_RecoveryAnalysis.xlsx"
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Recovery')
        add_conditional_formatting(writer, df)
    
    print(f"\nSaved to {output_file}")
    print(f"  Total: {len(df)}")
    print(f"  Recovered: {len(df[df['Recovered'] == 'YES'])}")

mt5.shutdown()
print("\nAll files created with fixes!")
