#!/usr/bin/env python3
"""
Time Cutoff Comparison - Side by Side Analysis
Single TP value ($0.20), varying time cutoffs from 2-30 minutes
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

def simulate_with_cutoff(open_price, direction, tp_dollars, cutoff_minutes, entry_time, bars_df, ticks_df):
    """Simulate position with specific time cutoff."""
    tp_points = tp_dollars / 0.01
    
    if direction == 'BUY':
        tp_price = open_price + tp_points
    else:
        tp_price = open_price - tp_points
    
    # Get bars within cutoff
    bars = bars_df.sort_values('time').reset_index(drop=True)
    cutoff_time = entry_time + timedelta(minutes=cutoff_minutes)
    
    tp_hit = False
    hit_candle = None
    
    for i, bar in bars.iterrows():
        candle_num = i + 1
        bar_end = bar['time'] + timedelta(minutes=1)
        
        # Stop if we've passed cutoff
        if bar['time'] > cutoff_time:
            break
        
        if candle_num == 1:
            # First candle: use ticks from entry
            candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < min(bar_end, cutoff_time))]
            if candle_ticks.empty:
                continue
            
            if direction == 'BUY':
                if (candle_ticks['price'] >= tp_price).any():
                    tp_hit = True
                    hit_candle = 1
                    break
            else:
                if (candle_ticks['price'] <= tp_price).any():
                    tp_hit = True
                    hit_candle = 1
                    break
        else:
            # Check if cutoff falls within this candle
            effective_end = min(bar_end, cutoff_time)
            
            # For candles after first, check OHLC
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    tp_hit = True
                    hit_candle = candle_num
                    break
            else:
                if tp_price >= bar['low']:
                    tp_hit = True
                    hit_candle = candle_num
                    break
    
    if tp_hit:
        return {'outcome': 'TP_HIT', 'pnl': tp_dollars, 'hit_candle': hit_candle}
    else:
        # Exit at cutoff time - find price at cutoff
        # Use close of last bar before cutoff
        bars_before_cutoff = bars[bars['time'] <= cutoff_time]
        if bars_before_cutoff.empty:
            return None
        
        last_bar = bars_before_cutoff.iloc[-1]
        
        # If cutoff is mid-candle, estimate price
        if cutoff_time < last_bar['time'] + timedelta(minutes=1):
            # Simple estimate: use close (conservative)
            exit_price = last_bar['close']
        else:
            exit_price = last_bar['close']
        
        if direction == 'BUY':
            pnl = (exit_price - open_price) * 0.01
        else:
            pnl = (open_price - exit_price) * 0.01
        
        return {'outcome': 'TIME_EXIT', 'pnl': pnl, 'hit_candle': None}

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
print("TIME CUTOFF COMPARISON - ASIA SESSION")
print("="*100)
print(f"TP Setting: $0.20 | Positions: {len(clean)}")
print()

# Fetch data
print("Fetching M1 bars and tick data...")
pos_data = []
for pos in clean:
    bar_from = pos['open_time'].replace(second=0, microsecond=0)
    bar_to = bar_from + timedelta(minutes=35)  # Extra buffer
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

# Test cutoffs from 2-30 minutes
cutoffs = list(range(2, 31))
tp_value = 0.20

actual_total = sum(p['actual_norm'] for p in pos_data)

results = []

for cutoff in cutoffs:
    sim_results = []
    
    for pdata in pos_data:
        result = simulate_with_cutoff(
            pdata['pos']['open_price'],
            pdata['pos']['direction'],
            tp_value,
            cutoff,
            pdata['pos']['open_time'],
            pdata['bars'],
            pdata['ticks']
        )
        if result:
            sim_results.append(result)
    
    if sim_results:
        tp_hits = sum(1 for r in sim_results if r['outcome'] == 'TP_HIT')
        time_exits = sum(1 for r in sim_results if r['outcome'] == 'TIME_EXIT')
        total_pnl = sum(r['pnl'] for r in sim_results)
        win_rate = tp_hits / len(sim_results) * 100
        vs_actual = total_pnl - actual_total
        
        results.append({
            'cutoff': cutoff,
            'tp_hits': tp_hits,
            'time_exits': time_exits,
            'total': len(sim_results),
            'win_rate': win_rate,
            'pnl': total_pnl,
            'vs_actual': vs_actual
        })

mt5.shutdown()

# Print results
print("\n" + "="*100)
print("SIDE-BY-SIDE COMPARISON")
print("="*100)
print(f"\n{'Cutoff':>8} | {'TP Hits':>8} | {'Time Exits':>11} | {'Win Rate':>9} | {'Total P&L':>11} | {'vs Actual':>11} | {'Status'}")
print("-" * 105)

for r in results:
    if r['pnl'] > actual_total:
        status = "BETTER"
    elif r['pnl'] > 0:
        status = "WORSE"
    else:
        status = "LOSS"
    
    marker = " <-- BEST" if r['pnl'] == max(x['pnl'] for x in results) else ""
    
    print(f"{r['cutoff']:>6}min | {r['tp_hits']:>4}/{r['total']:<3} | {r['time_exits']:>5}/{r['total']:<3} | "
          f"{r['win_rate']:>7.1f}% | ${r['pnl']:>9.2f} | ${r['vs_actual']:>+9.2f} | {status}{marker}")

# Actual for comparison
print("-" * 105)
print(f"{'ACTUAL':>8} | {'N/A':>8} | {'Trailing':>11} | {'91.9%':>9} | ${actual_total:>9.2f} | {'--':>11} | {'REFERENCE'}")

# Summary stats
print("\n" + "="*100)
print("ANALYSIS")
print("="*100)

pnls = [r['pnl'] for r in results]
print(f"\nP&L Range: ${min(pnls):.2f} to ${max(pnls):.2f}")
print(f"Best Cutoff: {results[pnls.index(max(pnls))]['cutoff']} minutes (${max(pnls):.2f})")
print(f"Worst Cutoff: {results[pnls.index(min(pnls))]['cutoff']} minutes (${min(pnls):.2f})")

# Find crossover points
positive = [r for r in results if r['pnl'] > 0]
if positive:
    print(f"\nCutoffs with Positive P&L: {len(positive)}")
    print(f"  Range: {min(r['cutoff'] for r in positive)} to {max(r['cutoff'] for r in positive)} minutes")

# Compare to actual
better_than_actual = [r for r in results if r['pnl'] > actual_total]
print(f"\nCutoffs Better Than Actual: {len(better_than_actual)}")
if better_than_actual:
    best_better = max(better_than_actual, key=lambda x: x['pnl'])
    print(f"  Best: {best_better['cutoff']} min (+${best_better['pnl'] - actual_total:.2f})")
else:
    closest = max(results, key=lambda x: x['pnl'])
    print(f"  None - Closest: {closest['cutoff']} min ({closest['pnl'] - actual_total:+.2f})")

# Save
results_df = pd.DataFrame(results)
results_df.to_csv('time_cutoff_comparison.csv', index=False)
print("\n[SAVED] Results saved to time_cutoff_comparison.csv")
