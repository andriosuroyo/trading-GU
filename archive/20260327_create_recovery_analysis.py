"""
Create RecoveryAnalysis_{date}.xlsx files
For each losing position, track:
- RecoveryTime: When price returned to OpenPrice (if ever)
- RecoveryDuration: Minutes from close to recovery
- OpposingCount: Number of opposing positions opened before recovery

XAUUSD: $1 = 100 points
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

def analyze_date(date_str, env_vars):
    """Analyze recovery for all losing positions on a given date"""
    print(f"\n{'='*100}")
    print(f"PROCESSING: {date_str}")
    print(f"{'='*100}")
    
    date = datetime.strptime(date_str, '%Y-%m-%d')
    date_from = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=timezone.utc)
    
    # Connect to MT5
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 initialize failed: {mt5.last_error()}")
        return None
    
    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        print(f"No deals for {date_str}")
        mt5.shutdown()
        return None
    
    print(f"Total deals: {len(deals)}")
    
    # Group by position
    deals_by_pos = defaultdict(list)
    for d in deals:
        deals_by_pos[d.position_id].append(d)
    
    # Build all positions list
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
            duration = (close_time - open_time).total_seconds() / 60
            
            all_positions.append({
                "ticket": pid,
                "direction": direction,
                "open_time": open_time,
                "close_time": close_time,
                "open_price": entry_deal.price,
                "close_price": exit_deal.price,
                "profit": profit,
                "profit_points": price_to_points(entry_deal.price - exit_deal.price) if direction == "SELL" else price_to_points(exit_deal.price - entry_deal.price),
                "duration_min": duration,
                "magic": entry_deal.magic,
                "symbol": entry_deal.symbol
            })
    
    all_positions.sort(key=lambda x: x["open_time"])
    
    # Get losing positions only (profit < 0)
    losing_positions = [p for p in all_positions if p["profit"] < 0]
    print(f"Losing positions: {len(losing_positions)}")
    
    if not losing_positions:
        mt5.shutdown()
        return None
    
    # Analyze recovery for each losing position
    MAX_RECOVERY_MINUTES = 240
    results = []
    
    symbol = "XAUUSD+"
    
    for idx, loss in enumerate(losing_positions):
        loss_close_time = loss["close_time"]
        target_price = loss["open_price"]
        loss_direction = loss["direction"]
        opposing_direction = "BUY" if loss_direction == "SELL" else "SELL"
        
        recovery_search_end = loss_close_time + timedelta(minutes=MAX_RECOVERY_MINUTES)
        
        # Fetch ticks to check for recovery
        ticks = mt5.copy_ticks_range(symbol, loss_close_time, recovery_search_end, mt5.COPY_TICKS_ALL)
        
        recovered = False
        recovery_time = None
        recovery_price = None
        recovery_duration_min = None
        
        if ticks is not None and len(ticks) > 0:
            for i in range(len(ticks)):
                tick = ticks[i]
                tick_time = datetime.fromtimestamp(tick['time'], tz=timezone.utc)
                
                # For BUY: check bid >= target
                # For SELL: check ask <= target
                if loss_direction == "BUY":
                    price = tick['bid']
                    if price >= target_price:
                        recovered = True
                        recovery_time = tick_time
                        recovery_price = price
                        break
                else:
                    price = tick['ask']
                    if price <= target_price:
                        recovered = True
                        recovery_time = tick_time
                        recovery_price = price
                        break
        
        # Calculate recovery duration
        if recovered and recovery_time:
            recovery_duration_min = (recovery_time - loss_close_time).total_seconds() / 60
            analysis_end = recovery_time
        else:
            analysis_end = recovery_search_end
        
        # Count opposing positions opened between loss close and recovery (or timeout)
        opposing_positions = []
        for pos in all_positions:
            if pos['ticket'] == loss['ticket']:
                continue
            if pos['direction'] == opposing_direction:
                if loss_close_time < pos['open_time'] <= analysis_end:
                    opposing_positions.append({
                        'time': pos['open_time'],
                        'ticket': pos['ticket'],
                        'magic': pos['magic']
                    })
        
        opposing_count = len(opposing_positions)
        
        # Calculate potential recovery profit
        if recovered:
            # Profit = distance from close price to recovery price
            if loss_direction == "BUY":
                recovery_profit_points = price_to_points(recovery_price - loss['close_price'])
            else:
                recovery_profit_points = price_to_points(loss['close_price'] - recovery_price)
        else:
            recovery_profit_points = 0
        
        results.append({
            'Date': date_str,
            'Ticket': loss['ticket'],
            'Magic': loss['magic'],
            'Direction': loss_direction,
            'OpenTime': loss['open_time'].strftime('%H:%M:%S'),
            'CloseTime': loss['close_time'].strftime('%H:%M:%S'),
            'OpenPrice': loss['open_price'],
            'ClosePrice': loss['close_price'],
            'LossAmount': loss['profit'],
            'LossPoints': loss['profit_points'],
            'DurationMin': loss['duration_min'],
            'Recovered': 'YES' if recovered else 'NO',
            'RecoveryTime': recovery_time.strftime('%H:%M:%S') if recovery_time else None,
            'RecoveryDurationMin': round(recovery_duration_min, 1) if recovery_duration_min else None,
            'RecoveryPrice': recovery_price,
            'OpposingCount': opposing_count,
            'RecoveryProfitPoints': round(recovery_profit_points, 1) if recovered else 0
        })
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(losing_positions)}...")
    
    mt5.shutdown()
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save to Excel
    output_file = f"data/{date_str}_RecoveryAnalysis.xlsx"
    df.to_excel(output_file, index=False, sheet_name='Recovery')
    print(f"\nSaved to {output_file}")
    
    # Print summary
    recovered_count = len(df[df['Recovered'] == 'YES'])
    not_recovered_count = len(df[df['Recovered'] == 'NO'])
    
    print(f"\nSummary:")
    print(f"  Total losses: {len(df)}")
    print(f"  Recovered: {recovered_count} ({recovered_count/len(df)*100:.1f}%)")
    print(f"  Not recovered: {not_recovered_count} ({not_recovered_count/len(df)*100:.1f}%)")
    
    if recovered_count > 0:
        recovered_df = df[df['Recovered'] == 'YES']
        print(f"  Avg recovery time: {recovered_df['RecoveryDurationMin'].mean():.1f} min")
        print(f"  Median recovery time: {recovered_df['RecoveryDurationMin'].median():.1f} min")
        print(f"  Avg opposing count: {recovered_df['OpposingCount'].mean():.1f}")
        print(f"  Total potential recovery profit: {recovered_df['RecoveryProfitPoints'].sum():.0f} points")
    
    return df

# Main execution
env_vars = load_env()

dates = ['2026-03-20', '2026-03-23', '2026-03-24']

all_results = {}
for date_str in dates:
    result = analyze_date(date_str, env_vars)
    if result is not None:
        all_results[date_str] = result

print("\n" + "="*100)
print("ALL DATES COMPLETE")
print("="*100)

# Combined summary
print("\nCombined Summary:")
for date_str, df in all_results.items():
    recovered = len(df[df['Recovered'] == 'YES'])
    total = len(df)
    print(f"  {date_str}: {recovered}/{total} recovered ({recovered/total*100:.1f}%)")
