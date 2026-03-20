#!/usr/bin/env python3
"""
Full TP Table - 20 to 300 points, per 10 points
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

def fetch_ticks(symbol, from_time, to_time):
    ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['price'] = (df['bid'] + df['ask']) / 2
    return df

def find_tp_hit_candle(open_price, direction, tp_points, entry_time, bars_df, ticks_df):
    """Find which candle TP is hit in. Returns (hit: bool, candle_num: int or None)"""
    tp_price_move = tp_points / 100  # points to price
    
    if direction == 'BUY':
        tp_price = open_price + tp_price_move
    else:
        tp_price = open_price - tp_price_move
    
    bars = bars_df.sort_values('time').reset_index(drop=True)
    
    for i, bar in bars.iterrows():
        candle_num = i + 1
        
        if candle_num == 1:
            bar_end = bar['time'] + timedelta(minutes=1)
            candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < bar_end)]
            
            if candle_ticks.empty:
                continue
            
            if direction == 'BUY':
                if (candle_ticks['price'] >= tp_price).any():
                    return True, candle_num
            else:
                if (candle_ticks['price'] <= tp_price).any():
                    return True, candle_num
        else:
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    return True, candle_num
            else:
                if tp_price >= bar['low']:
                    return True, candle_num
    
    return False, None

# Connect
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    exit(1)

# Get positions
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
positions = gu_tools.fetch_positions(date_from, datetime.now(timezone.utc))

def parse_sess(m):
    sess = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    return sess.get(str(int(m))[7] if len(str(int(m))) > 7 else '0', 'UNKNOWN')

def parse_strat(m):
    strat = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    return strat.get(str(int(m))[6] if len(str(int(m))) > 6 else '0', 'UNKNOWN')

asia = [p for p in positions if str(p['magic']).startswith('282603') and parse_sess(p['magic']) == 'ASIA']
for p in asia:
    p['strategy'] = parse_strat(p['magic'])

# Group baskets
asia_sorted = sorted(asia, key=lambda x: (x['magic'], x['open_time']))
baskets = []
current = None
for p in asia_sorted:
    if current is None or p['magic'] != current['magic']:
        current = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
        baskets.append(current)
    else:
        if (p['open_time'] - current['positions'][0]['open_time']).total_seconds() <= 60:
            current['positions'].append(p)
        else:
            current = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
            baskets.append(current)

first_pos = [b['positions'][0] for b in baskets]
glitches = [datetime(2026, 3, 12, 5, 2, 15, tzinfo=timezone.utc), datetime(2026, 3, 12, 5, 5, 19, tzinfo=timezone.utc)]
clean = [p for p in first_pos if p['open_time'] not in glitches]

print("="*100)
print("FULL TP TABLE - ASIA SESSION")
print("="*100)
print(f"Positions: {len(clean)}")
print()

# Fetch data
print("Fetching data...")
pos_data = []
for pos in clean:
    bar_from = pos['open_time'].replace(second=0, microsecond=0)
    bar_to = bar_from + timedelta(minutes=35)
    bars = fetch_m1_bars('XAUUSD+', bar_from, bar_to)
    
    tick_from = pos['open_time']
    tick_to = pos['open_time'] + timedelta(minutes=2)
    ticks = fetch_ticks('XAUUSD+', tick_from, tick_to)
    
    if not bars.empty and len(bars) >= 2 and not ticks.empty:
        norm = pos['lot_size'] * 100
        pos_data.append({
            'pos': pos,
            'bars': bars,
            'ticks': ticks,
            'actual_norm': pos['net_pl'] / norm
        })

print(f"Loaded {len(pos_data)} positions")

# TP values: 20 to 300, per 10 points
tp_values = list(range(20, 301, 10))  # 20, 30, 40, ..., 300

print("\n" + "="*100)
print("RESULTS")
print("="*100)
print(f"\n{'TP (pts)':>10} | {'TP ($)':>8} | {'Hit Count':>10} | {'Hit %':>8} | {'Max Candle':>12}")
print("-" * 65)

all_results = []

for tp_pts in tp_values:
    hits = 0
    misses = 0
    max_candle_hit = 0
    
    for pdata in pos_data:
        hit, candle = find_tp_hit_candle(
            pdata['pos']['open_price'],
            pdata['pos']['direction'],
            tp_pts,
            pdata['pos']['open_time'],
            pdata['bars'],
            pdata['ticks']
        )
        
        if hit:
            hits += 1
            if candle > max_candle_hit:
                max_candle_hit = candle
        else:
            misses += 1
    
    hit_pct = hits / len(pos_data) * 100
    tp_dollars = tp_pts * 0.01
    
    all_results.append({
        'tp_points': tp_pts,
        'tp_dollars': tp_dollars,
        'hits': hits,
        'misses': misses,
        'hit_pct': hit_pct,
        'max_candle': max_candle_hit
    })
    
    print(f"{tp_pts:>10} | ${tp_dollars:>6.2f} | {hits:>5}/{len(pos_data)} | {hit_pct:>7.1f}% | {max_candle_hit:>12}")

mt5.shutdown()
print("\n[COMPLETE]")
