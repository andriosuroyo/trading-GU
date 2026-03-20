#!/usr/bin/env python3
"""
Comprehensive Simulation - CORRECTED Scale
1. TP simulation ($0.20 = 20 points)
2. Time-based exit simulation
3. MFE capture analysis
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

def simulate_tp_hit(open_price, direction, tp_points, entry_time, bars_df, ticks_df):
    """Simulate when TP is hit. Returns (hit, candle_num, exit_price) or (False, None, None)"""
    if direction == 'BUY':
        tp_price = open_price + tp_points
    else:
        tp_price = open_price - tp_points
    
    bars = bars_df.sort_values('time').reset_index(drop=True)
    
    for i, bar in bars.iterrows():
        candle_num = i + 1
        
        if candle_num == 1:
            # First candle: tick analysis
            bar_end = bar['time'] + timedelta(minutes=1)
            candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < bar_end)]
            if candle_ticks.empty:
                continue
            
            if direction == 'BUY':
                if (candle_ticks['price'] >= tp_price).any():
                    return True, 1, tp_price
            else:
                if (candle_ticks['price'] <= tp_price).any():
                    return True, 1, tp_price
        else:
            # Subsequent candles: OHLC check
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    return True, candle_num, tp_price
            else:
                if tp_price >= bar['low']:
                    return True, candle_num, tp_price
    
    return False, None, None

def simulate_time_exit(open_price, direction, tp_points, max_candles, entry_time, bars_df, ticks_df):
    """Simulate with time-based exit. Returns pnl and outcome."""
    tp_hit, hit_candle, exit_price = simulate_tp_hit(open_price, direction, tp_points, entry_time, bars_df, ticks_df)
    
    if tp_hit and hit_candle <= max_candles:
        # TP hit within time limit
        pnl = tp_points * 0.01  # $0.01 per point on 0.01 lot
        return {'outcome': 'TP_HIT', 'pnl': pnl, 'exit_candle': hit_candle}
    else:
        # Exit at close of max_candles bar
        bars = bars_df.sort_values('time').reset_index(drop=True)
        if len(bars) < max_candles:
            return None
        
        exit_bar = bars.iloc[max_candles - 1]
        exit_price = exit_bar['close']
        
        if direction == 'BUY':
            pnl = (exit_price - open_price) * 0.01
        else:
            pnl = (open_price - exit_price) * 0.01
        
        return {'outcome': 'TIME_EXIT', 'pnl': pnl, 'exit_candle': max_candles}

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
print("COMPREHENSIVE SIMULATION - ASIA SESSION (CORRECTED SCALE)")
print("="*100)
print(f"Positions: {len(clean)}")
print("\nScale: 1 point = $0.01 on 0.01 lot")
print("      $0.20 TP = 20 points")
print()

# Fetch data
print("Fetching M1 bars and tick data...")
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

# ============================================================================
# PART 1: TP SIMULATION (when does TP hit?)
# ============================================================================
print("\n" + "="*100)
print("PART 1: TARGET PROFIT HIT ANALYSIS")
print("="*100)

tp_values_points = [10, 15, 20, 25, 30, 40, 50, 75, 100]  # points = cents on 0.01 lot

print(f"\n{'TP (pts)':>10} | {'TP ($)':>8} | {'Hit Count':>10} | {'Hit %':>8} | {'Avg Candle':>12}")
print("-" * 70)

tp_results = []
for tp_pts in tp_values_points:
    hits = 0
    total_candles = 0
    hit_positions = []
    
    for pdata in pos_data:
        hit, candle, price = simulate_tp_hit(
            pdata['pos']['open_price'],
            pdata['pos']['direction'],
            tp_pts / 100,  # Convert points to price (e.g., 20 points = 0.20 price)
            pdata['pos']['open_time'],
            pdata['bars'],
            pdata['ticks']
        )
        
        if hit:
            hits += 1
            total_candles += candle
            hit_positions.append({'candle': candle, 'tp': tp_pts})
    
    hit_pct = hits / len(pos_data) * 100
    avg_candle = total_candles / hits if hits > 0 else 0
    tp_dollars = tp_pts * 0.01
    
    tp_results.append({
        'tp_points': tp_pts,
        'tp_dollars': tp_dollars,
        'hits': hits,
        'hit_pct': hit_pct,
        'avg_candle': avg_candle
    })
    
    print(f"{tp_pts:>10} | ${tp_dollars:>6.2f} | {hits:>5}/{len(pos_data)} | {hit_pct:>7.1f}% | {avg_candle:>11.1f}")

# ============================================================================
# PART 2: TIME-BASED EXIT SIMULATION
# ============================================================================
print("\n" + "="*100)
print("PART 2: TIME-BASED EXIT SIMULATION")
print("="*100)
print("\nIf TP not hit within N candles, exit at close of candle N")

tp_test = 20  # 20 points = $0.20
time_limits = [2, 3, 5, 10, 15, 20, 30]

print(f"\nTP = {tp_test} points (${tp_test*0.01:.2f})")
print(f"\n{'Max Candles':>12} | {'TP Hits':>10} | {'Time Exits':>12} | {'Win%':>8} | {'Total P&L':>12} | {'vs Actual':>12}")
print("-" * 90)

time_results = []
for max_c in time_limits:
    results = []
    for pdata in pos_data:
        r = simulate_time_exit(
            pdata['pos']['open_price'],
            pdata['pos']['direction'],
            tp_test / 100,
            max_c,
            pdata['pos']['open_time'],
            pdata['bars'],
            pdata['ticks']
        )
        if r:
            results.append(r)
    
    if results:
        tp_hits = sum(1 for r in results if r['outcome'] == 'TP_HIT')
        time_exits = sum(1 for r in results if r['outcome'] == 'TIME_EXIT')
        wins = sum(1 for r in results if r['pnl'] > 0)
        total_pnl = sum(r['pnl'] for r in results)
        win_rate = wins / len(results) * 100
        vs_actual = total_pnl - actual_total
        
        time_results.append({
            'max_candles': max_c,
            'tp_hits': tp_hits,
            'time_exits': time_exits,
            'win_rate': win_rate,
            'pnl': total_pnl,
            'vs_actual': vs_actual
        })
        
        marker = " <-- BEST" if total_pnl == max([x['pnl'] for x in time_results]) else ""
        print(f"{max_c:>12} | {tp_hits:>5}/{len(results)} | {time_exits:>6}/{len(results)} | "
              f"{win_rate:>7.1f}% | ${total_pnl:>10.2f} | ${vs_actual:>+10.2f}{marker}")

# ============================================================================
# PART 3: MFE CAPTURE ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("PART 3: MFE CAPTURE ANALYSIS")
print("="*100)

# Calculate MFE for each position using the bars
capture_data = []
for pdata in pos_data:
    pos = pdata['pos']
    bars = pdata['bars'].sort_values('time')
    
    if len(bars) < 2:
        continue
    
    # Calculate MFE from all bars
    if pos['direction'] == 'BUY':
        max_price = bars['high'].max()
        mfe_points = (max_price - pos['open_price']) * 100  # Convert to points
    else:
        min_price = bars['low'].min()
        mfe_points = (pos['open_price'] - min_price) * 100
    
    actual_pnl_points = pdata['actual_norm'] / 0.01  # Convert $ to points
    capture_pct = (actual_pnl_points / mfe_points * 100) if mfe_points > 0 else 0
    
    capture_data.append({
        'mfe_points': mfe_points,
        'actual_pnl_points': actual_pnl_points,
        'capture_pct': capture_pct,
        'actual_pnl_dollars': pdata['actual_norm']
    })

capture_df = pd.DataFrame(capture_data)

print(f"\n{'Metric':<30} {'Value':>15}")
print("-" * 50)
print(f"{'Average MFE (points)':<30} {capture_df['mfe_points'].mean():>14.1f}")
print(f"{'Average Actual P&L (points)':<30} {capture_df['actual_pnl_points'].mean():>14.1f}")
print(f"{'Average MFE Capture %':<30} {capture_df['capture_pct'].mean():>13.1f}%")
print(f"{'Median MFE Capture %':<30} {capture_df['capture_pct'].median():>13.1f}%")

print("\nMFE Capture Distribution:")
bins = [0, 25, 50, 75, 100, 150, 999]
labels = ['0-25%', '25-50%', '50-75%', '75-100%', '100-150%', '150%+']
for i in range(len(bins)-1):
    mask = (capture_df['capture_pct'] >= bins[i]) & (capture_df['capture_pct'] < bins[i+1])
    count = mask.sum()
    pct = count / len(capture_df) * 100
    print(f"  {labels[i]:<10}: {count:>3} ({pct:>5.1f}%)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*100)
print("SUMMARY")
print("="*100)

best_time = max(time_results, key=lambda x: x['pnl'])

print(f"\n[ACTUAL PERFORMANCE]")
print(f"  Total P&L: ${actual_total:.2f}")
print(f"  Avg per trade: ${actual_total/len(pos_data):.2f}")

print(f"\n[BEST SIMULATED]")
print(f"  TP: ${tp_test*0.01:.2f} ({tp_test} points)")
print(f"  Max Candles: {best_time['max_candles']}")
print(f"  Total P&L: ${best_time['pnl']:.2f}")
print(f"  Win Rate: {best_time['win_rate']:.1f}%")
print(f"  vs Actual: ${best_time['vs_actual']:+.2f}")

if best_time['pnl'] > actual_total:
    print(f"\n[CONCLUSION] Fixed TP + Time Exit is BETTER")
else:
    diff = actual_total - best_time['pnl']
    print(f"\n[CONCLUSION] Current trailing stop is BETTER by ${diff:.2f}")
    print(f"  The EA captures more profit than ${tp_test*0.01:.2f} fixed TP")

mt5.shutdown()

# Save results
results_summary = {
    'tp_analysis': pd.DataFrame(tp_results),
    'time_analysis': pd.DataFrame(time_results),
    'capture_analysis': capture_df
}

for name, df in results_summary.items():
    df.to_csv(f'{name}_results.csv', index=False)

print("\n[SAVED] Results saved to CSV files")
