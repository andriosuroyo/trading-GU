#!/usr/bin/env python3
"""
Candle Close Analysis
For positions held >2 min, trace close price at each candle
"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import MetaTrader5 as mt5
import gu_tools
from datetime import datetime, timezone, timedelta
import pandas as pd

def fetch_m1_bars(symbol, from_time, to_time):
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

# Connect
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    exit(1)

# Get positions
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
positions = gu_tools.fetch_positions(date_from, datetime.now(timezone.utc))

def parse_sess(m):
    sess = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    return sess.get(str(int(m))[7] if len(str(int(m))) > 7 else '0', 'UNKNOWN')

asia = [p for p in positions if str(p['magic']).startswith('282603') and parse_sess(p['magic']) == 'ASIA']

# Group baskets
asia_sorted = sorted(asia, key=lambda x: (x['magic'], x['open_time']))
baskets = []
current = None
for p in asia_sorted:
    if current is None or p['magic'] != current['magic']:
        current = {'magic': p['magic'], 'positions': [p]}
        baskets.append(current)
    else:
        if (p['open_time'] - current['positions'][0]['open_time']).total_seconds() <= 60:
            current['positions'].append(p)
        else:
            current = {'magic': p['magic'], 'positions': [p]}
            baskets.append(current)

first_pos = [b['positions'][0] for b in baskets]
glitches = [datetime(2026, 3, 12, 5, 2, 15, tzinfo=timezone.utc), datetime(2026, 3, 12, 5, 5, 19, tzinfo=timezone.utc)]
clean = [p for p in first_pos if p['open_time'] not in glitches]

print("="*120)
print("CANDLE CLOSE ANALYSIS - ASIA SESSION")
print("="*120)
print(f"Positions: {len(clean)}")
print("\nTracing close price at each candle for positions")
print()

# Fetch data for all positions
print("Fetching data...")
pos_data = []
for pos in clean:
    bar_from = pos['open_time'].replace(second=0, microsecond=0)
    bar_to = bar_from + timedelta(minutes=35)
    bars = fetch_m1_bars('XAUUSD+', bar_from, bar_to)
    
    if not bars.empty and len(bars) >= 2:
        norm = pos['lot_size'] * 100
        dur_min = (pos['close_time'] - pos['open_time']).total_seconds() / 60
        pos_data.append({
            'pos': pos,
            'bars': bars,
            'actual_norm': pos['net_pl'] / norm,
            'duration_min': dur_min
        })

print(f"Loaded {len(pos_data)} positions")

# Filter for positions held >2 minutes
long_positions = [p for p in pos_data if p['duration_min'] > 2]
print(f"Positions held >2 minutes: {len(long_positions)}")

print("\n" + "="*120)
print("CANDLE-BY-CANDLE P&L TRACE (Positions held >2 min)")
print("="*120)

# For each long position, trace the close price at each candle
candle_pnl_data = []

for i, pdata in enumerate(long_positions[:15]):  # Show first 15 as examples
    pos = pdata['pos']
    bars = pdata['bars'].sort_values('time').reset_index(drop=True)
    
    print(f"\n--- Position {i+1}: {pos['open_time'].strftime('%m-%d %H:%M:%S')} {pos['direction']} @ {pos['open_price']:.2f} ---")
    print(f"Actual Duration: {pdata['duration_min']:.2f} min | Actual P&L: ${pdata['actual_norm']:.2f}")
    print(f"{'Candle':>8} | {'Close Time':<20} | {'Close Price':>12} | {'P&L ($)':>10} | {'Cumulative':>12}")
    print("-" * 80)
    
    for j, bar in bars.iterrows():
        candle_num = j + 1
        close_price = bar['close']
        
        if pos['direction'] == 'BUY':
            pnl = (close_price - pos['open_price']) * 0.01
        else:
            pnl = (pos['open_price'] - close_price) * 0.01
        
        # Track if this is before position closed
        bar_time = bar['time']
        position_closed = bar_time >= pos['close_time']
        marker = " [CLOSED]" if position_closed else ""
        
        print(f"{candle_num:>8} | {str(bar['time']):<20} | {close_price:>12.2f} | ${pnl:>8.2f} | {marker}")
        
        candle_pnl_data.append({
            'pos_idx': i,
            'candle': candle_num,
            'pnl': pnl,
            'position_closed': position_closed
        })
        
        # Stop after position closed or max 20 candles
        if position_closed or candle_num >= 20:
            break

# Summary statistics by candle
print("\n" + "="*120)
print("SUMMARY: AVERAGE P&L BY CANDLE (All positions held >2 min)")
print("="*120)

# Calculate average P&L at each candle across all long positions
candle_summary = {}

for pdata in long_positions:
    pos = pdata['pos']
    bars = pdata['bars'].sort_values('time').reset_index(drop=True)
    
    for j, bar in bars.iterrows():
        candle_num = j + 1
        close_price = bar['close']
        
        if pos['direction'] == 'BUY':
            pnl = (close_price - pos['open_price']) * 0.01
        else:
            pnl = (pos['open_price'] - close_price) * 0.01
        
        if candle_num not in candle_summary:
            candle_summary[candle_num] = []
        
        candle_summary[candle_num].append(pnl)
        
        # Stop after position closed
        if bar['time'] >= pos['close_time'] or candle_num >= 30:
            break

print(f"\n{'Candle':>8} | {'Avg P&L ($)':>12} | {'Min P&L ($)':>12} | {'Max P&L ($)':>12} | {'Count':>8}")
print("-" * 75)

for candle_num in sorted(candle_summary.keys())[:20]:
    pnls = candle_summary[candle_num]
    avg_pnl = sum(pnls) / len(pnls)
    min_pnl = min(pnls)
    max_pnl = max(pnls)
    
    marker = ""
    if avg_pnl < 0:
        marker = " [DRAWDOWN]"
    elif avg_pnl > 0.5:
        marker = " [PROFIT]"
    
    print(f"{candle_num:>8} | ${avg_pnl:>10.2f} | ${min_pnl:>10.2f} | ${max_pnl:>10.2f} | {len(pnls):>8}{marker}")

# Time-based exit simulation using close prices
print("\n" + "="*120)
print("TIME-BASED EXIT SIMULATION (Using Candle Close)")
print("="*120)
print("\nTP = 20 points ($0.20)")
print(f"{'Cutoff':>8} | {'TP Hits':>9} | {'Time Exits':>12} | {'Avg Time-Exit P&L':>18} | {'Total P&L':>12}")
print("-" * 80)

tp_points = 20  # $0.20

time_results = []
for cutoff in [2, 3, 5, 10, 15, 20, 30]:
    total_pnl = 0
    tp_hits = 0
    time_exits = 0
    time_exit_pnls = []
    
    for pdata in pos_data:
        pos = pdata['pos']
        bars = pdata['bars'].sort_values('time').reset_index(drop=True)
        
        # Check if TP hit within cutoff
        tp_hit = False
        hit_candle = None
        
        for j, bar in bars.iterrows():
            candle_num = j + 1
            
            # Check if this candle hits TP
            if pos['direction'] == 'BUY':
                if bar['high'] >= pos['open_price'] + tp_points/100:
                    tp_hit = True
                    hit_candle = candle_num
                    break
            else:
                if bar['low'] <= pos['open_price'] - tp_points/100:
                    tp_hit = True
                    hit_candle = candle_num
                    break
            
            # Stop at cutoff
            if candle_num >= cutoff:
                break
        
        if tp_hit and hit_candle <= cutoff:
            total_pnl += tp_points * 0.01
            tp_hits += 1
        else:
            # Exit at close of cutoff candle
            if cutoff <= len(bars):
                exit_bar = bars.iloc[cutoff - 1]
                close_price = exit_bar['close']
                
                if pos['direction'] == 'BUY':
                    pnl = (close_price - pos['open_price']) * 0.01
                else:
                    pnl = (pos['open_price'] - close_price) * 0.01
                
                total_pnl += pnl
                time_exits += 1
                time_exit_pnls.append(pnl)
    
    avg_time_exit_pnl = sum(time_exit_pnls) / len(time_exit_pnls) if time_exit_pnls else 0
    time_results.append({
        'cutoff': cutoff,
        'tp_hits': tp_hits,
        'time_exits': time_exits,
        'total_pnl': total_pnl,
        'avg_time_exit_pnl': avg_time_exit_pnl
    })
    
    print(f"{cutoff:>6}min | {tp_hits:>4}/{len(pos_data)} | {time_exits:>6}/{len(pos_data)} | "
          f"${avg_time_exit_pnl:>15.2f} | ${total_pnl:>10.2f}")

actual_total = sum(p['actual_norm'] for p in pos_data)
print(f"\nActual P&L: ${actual_total:.2f}")

# Find closest
closest = min(time_results, key=lambda x: abs(x['total_pnl'] - actual_total))
print(f"Closest simulation: {closest['cutoff']}min with ${closest['total_pnl']:.2f}")

mt5.shutdown()
print("\n[COMPLETE]")
