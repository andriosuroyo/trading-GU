#!/usr/bin/env python3
"""
Trailing Stop Simulation
Simulates trailing stop behavior (not fixed TP)
Position closes when price reverses by X points from max MFE
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

def simulate_trailing_stop(open_price, direction, trail_points, max_candles, entry_time, bars_df, ticks_df):
    """
    Simulate trailing stop.
    - Position tracks MFE
    - Closes when price reverses by trail_points from peak
    - Or at close of max_candles (time limit)
    """
    if direction == 'BUY':
        prices = []
        # First candle: use ticks
        bar = bars_df.iloc[0]
        bar_end = bar['time'] + timedelta(minutes=1)
        candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < bar_end)]
        
        if candle_ticks.empty:
            return None
        
        prices.extend(candle_ticks['price'].tolist())
        
        # Add OHLC from subsequent bars
        for i in range(1, min(max_candles, len(bars_df))):
            bar = bars_df.iloc[i]
            # Add open, high, low, close (sequence matters for simulation)
            prices.extend([bar['open'], bar['high'], bar['low'], bar['close']])
        
        # Simulate trailing stop
        max_price = open_price
        for price in prices:
            if price > max_price:
                max_price = price
            # Check if trail stop hit
            if price <= max_price - trail_points:
                pnl = (price - open_price) * 0.01
                return {'outcome': 'TRAIL_HIT', 'pnl': pnl, 'exit_price': price}
        
        # Time limit - exit at last price
        final_price = prices[-1] if prices else open_price
        pnl = (final_price - open_price) * 0.01
        return {'outcome': 'TIME_EXIT', 'pnl': pnl, 'exit_price': final_price}
        
    else:  # SELL
        prices = []
        bar = bars_df.iloc[0]
        bar_end = bar['time'] + timedelta(minutes=1)
        candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < bar_end)]
        
        if candle_ticks.empty:
            return None
        
        prices.extend(candle_ticks['price'].tolist())
        
        for i in range(1, min(max_candles, len(bars_df))):
            bar = bars_df.iloc[i]
            prices.extend([bar['open'], bar['high'], bar['low'], bar['close']])
        
        min_price = open_price
        for price in prices:
            if price < min_price:
                min_price = price
            if price >= min_price + trail_points:
                pnl = (open_price - price) * 0.01
                return {'outcome': 'TRAIL_HIT', 'pnl': pnl, 'exit_price': price}
        
        final_price = prices[-1] if prices else open_price
        pnl = (open_price - final_price) * 0.01
        return {'outcome': 'TIME_EXIT', 'pnl': pnl, 'exit_price': final_price}

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
print("TRAILING STOP SIMULATION - ASIA SESSION")
print("="*100)
print(f"Positions: {len(clean)}")
print("\nTrailing stop = Position closes when price reverses X points from max MFE")
print()

# Fetch data
print("Fetching data...")
pos_data = []
for pos in clean:
    bar_from = pos['open_time'].replace(second=0, microsecond=0)
    bar_to = bar_from + timedelta(minutes=30)
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

# Test trailing stop values (in points)
# 5 points = $0.05 on 0.01 lot
trail_values = [3, 5, 7, 10, 15, 20, 30, 50]  # points
max_candles_list = [2, 3, 5, 10, 15, 20, 30]

actual_total = sum(p['actual_norm'] for p in pos_data)

print("\n" + "="*100)
print("RESULTS: Trailing Stop Points vs Max Candles")
print("="*100)
print(f"\n{'Trail':>8} | {'MaxC':>5} | {'Trail Hits':>11} | {'Time Exits':>11} | {'Win%':>7} | {'Total P&L':>11} | {'vs Actual':>11}")
print("-" * 105)

results = []

for trail_points in trail_values:
    for max_c in max_candles_list:
        sim_results = []
        
        for pdata in pos_data:
            result = simulate_trailing_stop(
                pdata['pos']['open_price'],
                pdata['pos']['direction'],
                trail_points,
                max_c,
                pdata['pos']['open_time'],
                pdata['bars'],
                pdata['ticks']
            )
            if result:
                sim_results.append(result)
        
        if sim_results:
            trail_hits = sum(1 for r in sim_results if r['outcome'] == 'TRAIL_HIT')
            time_exits = sum(1 for r in sim_results if r['outcome'] == 'TIME_EXIT')
            total_pnl = sum(r['pnl'] for r in sim_results)
            win_rate = sum(1 for r in sim_results if r['pnl'] > 0) / len(sim_results) * 100
            vs_actual = total_pnl - actual_total
            
            results.append({
                'trail_points': trail_points,
                'max_candles': max_c,
                'trail_hits': trail_hits,
                'time_exits': time_exits,
                'total': len(sim_results),
                'win_rate': win_rate,
                'pnl': total_pnl,
                'vs_actual': vs_actual
            })

# Print results
df = pd.DataFrame(results)

for _, r in df.iterrows():
    marker = " <-- BEST" if r['pnl'] == df['pnl'].max() else ""
    print(f"{r['trail_points']:>6}pt | {r['max_candles']:>4} | {r['trail_hits']:>5}/{r['total']:<3} | "
          f"{r['time_exits']:>5}/{r['total']:<3} | {r['win_rate']:>6.1f}% | "
          f"${r['pnl']:>9.2f} | ${r['vs_actual']:>+9.2f}{marker}")

# Summary
print("\n" + "="*100)
print("OPTIMAL BY TRAILING STOP VALUE")
print("="*100)

for trail in trail_values:
    t_df = df[df['trail_points'] == trail]
    if t_df.empty:
        continue
    best = t_df.loc[t_df['pnl'].idxmax()]
    print(f"Trail {trail}pt: {best['max_candles']:.0f}candles | WR {best['win_rate']:.1f}% | P&L ${best['pnl']:.2f}")

# Best overall
best = df.loc[df['pnl'].idxmax()]
print(f"\n[OVERALL BEST]")
print(f"  Trail: {best['trail_points']} points (${best['trail_points']*0.01:.2f})")
print(f"  Max Candles: {best['max_candles']}")
print(f"  Win Rate: {best['win_rate']:.1f}%")
print(f"  Total P&L: ${best['pnl']:.2f}")

print(f"\n[ACTUAL PERFORMANCE]")
print(f"  Total P&L: ${actual_total:.2f}")

if best['pnl'] > actual_total:
    print(f"\n[WINNER] Trailing stop ${best['trail_points']*0.01:.2f} is better by ${best['pnl'] - actual_total:.2f}")
else:
    diff = actual_total - best['pnl']
    print(f"\n[WINNER] Actual trailing stop is better by ${diff:.2f}")
    print(f"  (Current mechanism captures more profit than simulated ${best['trail_points']*0.01:.2f} trail)")

mt5.shutdown()
df.to_csv('trailing_stop_simulation.csv', index=False)
print("\n[SAVED] Results saved to trailing_stop_simulation.csv")
