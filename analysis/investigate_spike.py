#!/usr/bin/env python3
"""
Investigate the Max Candle spike at TP 90-100
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

def find_tp_hit_details(open_price, direction, tp_points, entry_time, bars_df, ticks_df):
    """Find which candle TP is hit in and return details."""
    tp_price_move = tp_points / 100
    
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
                    return True, candle_num, bar['time']
            else:
                if (candle_ticks['price'] <= tp_price).any():
                    return True, candle_num, bar['time']
        else:
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    return True, candle_num, bar['time']
            else:
                if tp_price >= bar['low']:
                    return True, candle_num, bar['time']
    
    return False, None, None

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

print("="*100)
print("INVESTIGATING TP 90-100 SPIKE")
print("="*100)

# Fetch data for all positions
print("\nFetching data...")
pos_data = []
for pos in clean:
    bar_from = pos['open_time'].replace(second=0, microsecond=0)
    bar_to = bar_from + timedelta(minutes=35)
    bars = fetch_m1_bars('XAUUSD+', bar_from, bar_to)
    
    tick_from = pos['open_time']
    tick_to = pos['open_time'] + timedelta(minutes=2)
    ticks = fetch_ticks('XAUUSD+', tick_from, tick_to)
    
    if not bars.empty and len(bars) >= 2 and not ticks.empty:
        pos_data.append({
            'pos': pos,
            'bars': bars,
            'ticks': ticks
        })

print(f"Loaded {len(pos_data)} positions")

# Find positions that hit TP 90 at candle 36
tp_90_hits = []
tp_100_hits = []
tp_110_hits = []

for i, pdata in enumerate(pos_data):
    pos = pdata['pos']
    
    # Check TP 90
    hit_90, candle_90, time_90 = find_tp_hit_details(
        pos['open_price'], pos['direction'], 90,
        pos['open_time'], pdata['bars'], pdata['ticks']
    )
    
    # Check TP 100
    hit_100, candle_100, time_100 = find_tp_hit_details(
        pos['open_price'], pos['direction'], 100,
        pos['open_time'], pdata['bars'], pdata['ticks']
    )
    
    # Check TP 110
    hit_110, candle_110, time_110 = find_tp_hit_details(
        pos['open_price'], pos['direction'], 110,
        pos['open_time'], pdata['bars'], pdata['ticks']
    )
    
    if hit_90:
        tp_90_hits.append({
            'idx': i,
            'time': pos['open_time'],
            'direction': pos['direction'],
            'open': pos['open_price'],
            'candle': candle_90,
            'hit_time': time_90
        })
    
    if hit_100:
        tp_100_hits.append({
            'idx': i,
            'time': pos['open_time'],
            'direction': pos['direction'],
            'open': pos['open_price'],
            'candle': candle_100,
            'hit_time': time_100
        })
    
    if hit_110:
        tp_110_hits.append({
            'idx': i,
            'time': pos['open_time'],
            'direction': pos['direction'],
            'open': pos['open_price'],
            'candle': candle_110,
            'hit_time': time_110
        })

print("\n" + "="*100)
print("TP 90 HITS - Candle Distribution")
print("="*100)
candles_90 = [h['candle'] for h in tp_90_hits]
print(f"Total hits: {len(tp_90_hits)}")
print(f"Max candle: {max(candles_90) if candles_90 else 'N/A'}")
print(f"Candle distribution:")
for c in sorted(set(candles_90)):
    count = candles_90.count(c)
    print(f"  Candle {c}: {count} hits")

print("\nPositions hitting at candle 36 (TP 90):")
for h in tp_90_hits:
    if h['candle'] == 36:
        t = str(h['time'])[:16]
        print(f"  {t} {h['direction']} @ {h['open']:.2f}")

print("\n" + "="*100)
print("TP 100 HITS - Candle Distribution")
print("="*100)
candles_100 = [h['candle'] for h in tp_100_hits]
print(f"Total hits: {len(tp_100_hits)}")
print(f"Max candle: {max(candles_100) if candles_100 else 'N/A'}")
print(f"Candle distribution:")
for c in sorted(set(candles_100)):
    count = candles_100.count(c)
    print(f"  Candle {c}: {count} hits")

print("\nPositions hitting at candle 36 (TP 100):")
for h in tp_100_hits:
    if h['candle'] == 36:
        t = str(h['time'])[:16]
        print(f"  {t} {h['direction']} @ {h['open']:.2f}")

print("\n" + "="*100)
print("TP 110 HITS - Candle Distribution")
print("="*100)
candles_110 = [h['candle'] for h in tp_110_hits]
print(f"Total hits: {len(tp_110_hits)}")
print(f"Max candle: {max(candles_110) if candles_110 else 'N/A'}")
print(f"Candle distribution:")
for c in sorted(set(candles_110)):
    count = candles_110.count(c)
    print(f"  Candle {c}: {count} hits")

# Check if the position that hit TP 90 at candle 36 also hit TP 110
print("\n" + "="*100)
print("COMPARISON: Same position, different TPs")
print("="*100)

# Find positions that hit TP 90/100 but NOT TP 110
hit_90_or_100_not_110 = []
for h90 in tp_90_hits:
    pos_idx = h90['idx']
    # Check if this position hit TP 110
    hit_110_for_this = any(h['idx'] == pos_idx for h in tp_110_hits)
    if not hit_110_for_this:
        hit_90_or_100_not_110.append({
            'tp': 90,
            'candle': h90['candle'],
            'time': h90['time']
        })

for h100 in tp_100_hits:
    pos_idx = h100['idx']
    hit_110_for_this = any(h['idx'] == pos_idx for h in tp_110_hits)
    if not hit_110_for_this:
        hit_90_or_100_not_110.append({
            'tp': 100,
            'candle': h100['candle'],
            'time': h100['time']
        })

print(f"\nPositions that hit TP 90/100 but NOT TP 110: {len(hit_90_or_100_not_110)}")
for item in hit_90_or_100_not_110:
    t = str(item['time'])[:16]
    print(f"  {t}: TP {item['tp']} at candle {item['candle']}, missed TP 110")

mt5.shutdown()
print("\n[COMPLETE]")
