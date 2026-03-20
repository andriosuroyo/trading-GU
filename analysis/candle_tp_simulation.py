#!/usr/bin/env python3
"""
Candle-Based TP Simulation
- First candle: Tick-level analysis from entry second
- Subsequent candles: OHLC check (TP within High-Low range)
"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import MetaTrader5 as mt5
import gu_tools
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

def fetch_m1_bars(symbol, from_time, to_time):
    """Fetch M1 bars."""
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def fetch_ticks(symbol, from_time, to_time):
    """Fetch tick data."""
    ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['price'] = (df['bid'] + df['ask']) / 2
    return df

def simulate_tp_hit(open_price, direction, tp_dollars, entry_time, bars_df, ticks_df):
    """
    Simulate when TP is hit using candle-based approach.
    
    Returns: {
        'tp_hit': bool,
        'candle_number': int (1, 2, 3... or None if not hit),
        'exit_price': float,
        'pnl': float
    }
    """
    tp_points = tp_dollars / 0.01  # $0.01 = 1 point on 0.01 lot
    
    if direction == 'BUY':
        tp_price = open_price + tp_points
    else:  # SELL
        tp_price = open_price - tp_points
    
    # Sort bars by time
    bars = bars_df.sort_values('time').reset_index(drop=True)
    
    for i, bar in bars.iterrows():
        candle_num = i + 1  # 1-based
        
        if candle_num == 1:
            # First candle: use tick data from entry time
            bar_end = bar['time'] + timedelta(minutes=1)
            candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < bar_end)]
            
            if candle_ticks.empty:
                continue
            
            # Check if TP hit in first candle
            if direction == 'BUY':
                hit = (candle_ticks['price'] >= tp_price).any()
                if hit:
                    hit_time = candle_ticks[candle_ticks['price'] >= tp_price].iloc[0]['time']
                    return {'tp_hit': True, 'candle_number': 1, 'exit_price': tp_price, 'pnl': tp_dollars}
            else:  # SELL
                hit = (candle_ticks['price'] <= tp_price).any()
                if hit:
                    hit_time = candle_ticks[candle_ticks['price'] <= tp_price].iloc[0]['time']
                    return {'tp_hit': True, 'candle_number': 1, 'exit_price': tp_price, 'pnl': tp_dollars}
        else:
            # Subsequent candles: check if TP within High-Low range
            if direction == 'BUY':
                # For BUY: TP is above entry, check if price reached that high
                if tp_price <= bar['high']:
                    return {'tp_hit': True, 'candle_number': candle_num, 'exit_price': tp_price, 'pnl': tp_dollars}
            else:  # SELL
                # For SELL: TP is below entry, check if price reached that low
                if tp_price >= bar['low']:
                    return {'tp_hit': True, 'candle_number': candle_num, 'exit_price': tp_price, 'pnl': tp_dollars}
    
    # TP not hit
    return {'tp_hit': False, 'candle_number': None, 'exit_price': None, 'pnl': 0}

# Connect
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    exit(1)

# Get Asia positions
date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
positions = gu_tools.fetch_positions(date_from, datetime.now(timezone.utc))

def parse_sess(m):
    sess = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    return sess.get(str(int(m))[7] if len(str(int(m))) > 7 else '0', 'UNKNOWN')

def parse_strat(m):
    strat = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    return strat.get(str(int(m))[6] if len(str(int(m))) > 6 else '0', 'UNKNOWN')

# Filter Asia
asia = [p for p in positions if str(p['magic']).startswith('282603') and parse_sess(p['magic']) == 'ASIA']
for p in asia:
    p['strategy'] = parse_strat(p['magic'])

# Group by basket
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
print("CANDLE-BASED TP SIMULATION - ASIA SESSION")
print("="*100)
print(f"Analyzing {len(clean)} first positions")
print("\nMethod:")
print("  - Candle 1: Tick-level analysis from entry second")
print("  - Candles 2+: OHLC check (TP within High-Low range)")
print()

# Prepare position data with pre-fetched bars and ticks
print("Fetching M1 bars and tick data...")
pos_data = []

for pos in clean:
    # Fetch 30 minutes of M1 bars
    bar_from = pos['open_time'].replace(second=0, microsecond=0)  # Start of minute
    bar_to = bar_from + timedelta(minutes=30)
    bars = fetch_m1_bars('XAUUSD+', bar_from, bar_to)
    
    # Fetch ticks for first 2 minutes (for candle 1 analysis)
    tick_from = pos['open_time']
    tick_to = pos['open_time'] + timedelta(minutes=2)
    ticks = fetch_ticks('XAUUSD+', tick_from, tick_to)
    
    if not bars.empty and not ticks.empty:
        norm = pos['lot_size'] * 100
        pos_data.append({
            'pos': pos,
            'bars': bars,
            'ticks': ticks,
            'actual_norm': pos['net_pl'] / norm
        })
    
    if len(pos_data) % 10 == 0:
        print(f"  Loaded {len(pos_data)}/{len(clean)}...")

print(f"\nSuccessfully loaded {len(pos_data)} positions")

# TP values to test (based on realistic MFE from previous analysis)
tp_values = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.80, 1.00]

# Run simulation
print("\n" + "="*100)
print("SIMULATION RESULTS")
print("="*100)

results = []
actual_total = sum(p['actual_norm'] for p in pos_data)

for tp in tp_values:
    tp_results = []
    
    for pdata in pos_data:
        result = simulate_tp_hit(
            pdata['pos']['open_price'],
            pdata['pos']['direction'],
            tp,
            pdata['pos']['open_time'],
            pdata['bars'],
            pdata['ticks']
        )
        
        if result:
            result['tp'] = tp
            result['actual'] = pdata['actual_norm']
            result['strategy'] = pdata['pos']['strategy']
            tp_results.append(result)
    
    if tp_results:
        hits = sum(1 for r in tp_results if r['tp_hit'])
        total = len(tp_results)
        wr = hits / total * 100
        pnl = sum(r['pnl'] for r in tp_results)
        
        # Candle distribution
        candle_dist = {}
        for r in tp_results:
            if r['tp_hit']:
                c = r['candle_number']
                candle_dist[c] = candle_dist.get(c, 0) + 1
        
        results.append({
            'tp': tp,
            'hits': hits,
            'total': total,
            'win_rate': wr,
            'pnl': pnl,
            'vs_actual': pnl - actual_total,
            'candle_dist': candle_dist
        })

# Print results
print(f"\n{'TP':>8} | {'Hits':>6} | {'Total':>6} | {'Win%':>7} | {'P&L':>10} | {'vs Actual':>10} | {'Candle Dist'}")
print("-" * 110)

for r in results:
    dist_str = ', '.join([f"C{k}:{v}" for k, v in sorted(r['candle_dist'].items())]) if r['candle_dist'] else '-'
    marker = " <-- BEST" if r['pnl'] == max(x['pnl'] for x in results) else ""
    print(f"${r['tp']:>6.2f} | {r['hits']:>6} | {r['total']:>6} | {r['win_rate']:>6.1f}% | "
          f"${r['pnl']:>8.2f} | ${r['vs_actual']:>+8.2f} | {dist_str}{marker}")

# Best result
best = max(results, key=lambda x: x['pnl'])
print(f"\n[OPTIMAL]")
print(f"  TargetProfit: ${best['tp']:.2f}")
print(f"  Win Rate: {best['win_rate']:.1f}% ({best['hits']}/{best['total']})")
print(f"  Total P&L: ${best['pnl']:.2f}")
print(f"  vs Actual: ${best['vs_actual']:+.2f}")
print(f"  Candle Distribution: {best['candle_dist']}")

print(f"\n[ACTUAL PERFORMANCE]")
print(f"  Total P&L: ${actual_total:.2f}")
print(f"  Avg per trade: ${actual_total/len(pos_data):.2f}")

if best['pnl'] > actual_total:
    print(f"\n[CONCLUSION] Fixed TP ${best['tp']:.2f} is BETTER by ${best['pnl'] - actual_total:.2f}")
else:
    print(f"\n[CONCLUSION] Trailing stop is BETTER by ${actual_total - best['pnl']:.2f}")

mt5.shutdown()

# Save results
results_df = pd.DataFrame([{k: v for k, v in r.items() if k != 'candle_dist'} for r in results])
results_df.to_csv('candle_tp_simulation.csv', index=False)
print("\n[SAVED] Results saved to candle_tp_simulation.csv")
