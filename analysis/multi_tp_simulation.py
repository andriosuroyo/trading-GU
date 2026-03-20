#!/usr/bin/env python3
"""
Multi-TP Simulation
TP levels: 30, 40, 50, ... 300 points
Time cutoffs: 2-30 minutes
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

def simulate_time_exit(open_price, direction, tp_points, max_minutes, entry_time, bars_df, ticks_df):
    """Simulate position with time-based exit."""
    tp_price_move = tp_points / 100
    
    if direction == 'BUY':
        tp_price = open_price + tp_price_move
    else:
        tp_price = open_price - tp_price_move
    
    bars = bars_df.sort_values('time').reset_index(drop=True)
    cutoff_time = entry_time + timedelta(minutes=max_minutes)
    
    # Check if TP is hit before cutoff
    for i, bar in bars.iterrows():
        candle_num = i + 1
        bar_end = bar['time'] + timedelta(minutes=1)
        
        if bar['time'] > cutoff_time:
            break
        
        if candle_num == 1:
            effective_end = min(bar_end, cutoff_time)
            candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < effective_end)]
            
            if candle_ticks.empty:
                continue
            
            if direction == 'BUY':
                if (candle_ticks['price'] >= tp_price).any():
                    pnl = tp_points * 0.01
                    return {'outcome': 'TP_HIT', 'pnl': pnl}
            else:
                if (candle_ticks['price'] <= tp_price).any():
                    pnl = tp_points * 0.01
                    return {'outcome': 'TP_HIT', 'pnl': pnl}
        else:
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    pnl = tp_points * 0.01
                    return {'outcome': 'TP_HIT', 'pnl': pnl}
            else:
                if tp_price >= bar['low']:
                    pnl = tp_points * 0.01
                    return {'outcome': 'TP_HIT', 'pnl': pnl}
    
    # TP not hit - exit at cutoff
    bars_before_cutoff = bars[bars['time'] <= cutoff_time]
    if bars_before_cutoff.empty:
        return None
    
    last_bar = bars_before_cutoff.iloc[-1]
    exit_price = last_bar['close']
    
    if direction == 'BUY':
        pnl = (exit_price - open_price) * 0.01
    else:
        pnl = (open_price - exit_price) * 0.01
    
    return {'outcome': 'TIME_EXIT', 'pnl': pnl}

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
print("MULTI-TP SIMULATION - ASIA SESSION")
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
actual_total = sum(p['actual_norm'] for p in pos_data)

# TP values: 30 to 300, step 10
tp_values = list(range(30, 301, 10))
time_cutoffs = [5, 10, 15, 20, 30]  # Key time cutoffs to test

print("\n" + "="*100)
print("RESULTS BY TP LEVEL")
print("="*100)

all_results = []

for tp in tp_values:
    print(f"\n--- TP = {tp} points (${tp*0.01:.2f}) ---")
    print(f"{'Time':>8} | {'TP Hits':>9} | {'Losses':>8} | {'Win%':>8} | {'Sim P&L':>12} | {'vs Actual':>10}")
    print("-" * 75)
    
    for cutoff in time_cutoffs:
        sim_results = []
        
        for pdata in pos_data:
            result = simulate_time_exit(
                pdata['pos']['open_price'],
                pdata['pos']['direction'],
                tp, cutoff,
                pdata['pos']['open_time'],
                pdata['bars'], pdata['ticks']
            )
            if result:
                sim_results.append(result)
        
        if sim_results:
            tp_hits = sum(1 for r in sim_results if r['outcome'] == 'TP_HIT')
            losses = sum(1 for r in sim_results if r['pnl'] < 0)
            wins = sum(1 for r in sim_results if r['pnl'] > 0)
            win_rate = wins / len(sim_results) * 100
            total_pnl = sum(r['pnl'] for r in sim_results)
            vs_actual = total_pnl - actual_total
            
            all_results.append({
                'tp': tp, 'cutoff': cutoff, 'tp_hits': tp_hits, 'losses': losses,
                'total': len(sim_results), 'win_rate': win_rate,
                'sim_pnl': total_pnl, 'vs_actual': vs_actual
            })
            
            print(f"{cutoff:>6}min | {tp_hits:>4}/{len(sim_results)} | {losses:>5}/{len(sim_results)} | "
                  f"{win_rate:>7.1f}% | ${total_pnl:>10.2f} | ${vs_actual:>+8.2f}")

# Find optimal for each TP
print("\n" + "="*100)
print("OPTIMAL TIME CUTOFF BY TP LEVEL")
print("="*100)
print(f"\n{'TP (pts)':>10} | {'TP ($)':>8} | {'Best Time':>10} | {'Win%':>8} | {'Losses':>8} | {'Sim P&L':>12}")
print("-" * 80)

for tp in tp_values:
    tp_data = [r for r in all_results if r['tp'] == tp]
    if not tp_data:
        continue
    best = max(tp_data, key=lambda x: x['sim_pnl'])
    print(f"{tp:>10} | ${tp*0.01:>6.2f} | {best['cutoff']:>7}min | {best['win_rate']:>7.1f}% | "
          f"{best['losses']:>5}/{best['total']} | ${best['sim_pnl']:>10.2f}")

# Best overall
best_overall = max(all_results, key=lambda x: x['sim_pnl'])
print("\n" + "="*100)
print("BEST OVERALL CONFIGURATION")
print("="*100)
print(f"TP: {best_overall['tp']} points (${best_overall['tp']*0.01:.2f})")
print(f"Time Cutoff: {best_overall['cutoff']} minutes")
print(f"TP Hits: {best_overall['tp_hits']}/{best_overall['total']}")
print(f"Losses: {best_overall['losses']}/{best_overall['total']}")
print(f"Win Rate: {best_overall['win_rate']:.1f}%")
print(f"Simulated P&L: ${best_overall['sim_pnl']:.2f}")
print(f"vs Actual: ${best_overall['vs_actual']:+.2f}")

print(f"\n[ACTUAL PERFORMANCE]")
print(f"Total P&L: ${actual_total:.2f}")

mt5.shutdown()

# Save
results_df = pd.DataFrame(all_results)
results_df.to_csv('multi_tp_simulation.csv', index=False)
print("\n[SAVED] Results saved to multi_tp_simulation.csv")
