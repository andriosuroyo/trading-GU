#!/usr/bin/env python3
"""
Time-Based Exit Simulation with Candle Analysis
- TP hit within N candles = take profit
- TP not hit = exit at close of candle N
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

def simulate_time_exit(open_price, direction, tp_dollars, max_candles, entry_time, bars_df, ticks_df):
    """
    Simulate with time-based exit.
    
    Returns: {
        'outcome': 'TP_HIT' or 'TIME_EXIT',
        'exit_candle': int,
        'pnl': float
    }
    """
    tp_points = tp_dollars / 0.01
    
    if direction == 'BUY':
        tp_price = open_price + tp_points
    else:
        tp_price = open_price - tp_points
    
    bars = bars_df.sort_values('time').reset_index(drop=True)
    
    # Limit to max_candles
    bars = bars.head(max_candles)
    
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
                    return {'outcome': 'TP_HIT', 'exit_candle': 1, 'pnl': tp_dollars}
            else:
                if (candle_ticks['price'] <= tp_price).any():
                    return {'outcome': 'TP_HIT', 'exit_candle': 1, 'pnl': tp_dollars}
        else:
            # Subsequent candles: OHLC check
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    return {'outcome': 'TP_HIT', 'exit_candle': candle_num, 'pnl': tp_dollars}
            else:
                if tp_price >= bar['low']:
                    return {'outcome': 'TP_HIT', 'exit_candle': candle_num, 'pnl': tp_dollars}
    
    # TP not hit - exit at close of last candle
    last_bar = bars.iloc[-1]
    if direction == 'BUY':
        pnl = (last_bar['close'] - open_price) * 0.01
    else:
        pnl = (open_price - last_bar['close']) * 0.01
    
    return {'outcome': 'TIME_EXIT', 'exit_candle': max_candles, 'pnl': pnl}

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
print("TIME-BASED EXIT SIMULATION - ASIA SESSION")
print("="*100)
print(f"Simulating {len(clean)} positions")
print("Rule: Exit at TP if hit within N candles, else exit at close of candle N")
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

# Test parameters
tp_values = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
max_candles_list = [2, 3, 5, 10, 15, 20, 30]

actual_total = sum(p['actual_norm'] for p in pos_data)

print("\n" + "="*100)
print("RESULTS: TargetProfit vs Max Candles")
print("="*100)
print(f"\n{'TP':>8} | {'MaxC':>5} | {'TP Hits':>8} | {'TimeExits':>10} | {'Win%':>7} | {'Total P&L':>11} | {'vs Actual':>10}")
print("-" * 100)

all_results = []

for tp in tp_values:
    for max_c in max_candles_list:
        sim_results = []
        
        for pdata in pos_data:
            result = simulate_time_exit(
                pdata['pos']['open_price'],
                pdata['pos']['direction'],
                tp, max_c,
                pdata['pos']['open_time'],
                pdata['bars'],
                pdata['ticks']
            )
            if result:
                sim_results.append(result)
        
        if sim_results:
            tp_hits = sum(1 for r in sim_results if r['outcome'] == 'TP_HIT')
            time_exits = sum(1 for r in sim_results if r['outcome'] == 'TIME_EXIT')
            total = len(sim_results)
            wr = tp_hits / total * 100
            pnl = sum(r['pnl'] for r in sim_results)
            vs_actual = pnl - actual_total
            
            all_results.append({
                'tp': tp, 'max_candles': max_c, 'tp_hits': tp_hits,
                'time_exits': time_exits, 'total': total, 'win_rate': wr,
                'pnl': pnl, 'vs_actual': vs_actual
            })

# Print results
df = pd.DataFrame(all_results)

for _, r in df.iterrows():
    marker = " <-- BEST" if r['pnl'] == df['pnl'].max() else ""
    print(f"${r['tp']:>6.2f} | {r['max_candles']:>4} | {r['tp_hits']:>4}/{r['total']:<3} | "
          f"{r['time_exits']:>5}/{r['total']:<3} | {r['win_rate']:>6.1f}% | "
          f"${r['pnl']:>9.2f} | ${r['vs_actual']:>+8.2f}{marker}")

# Best by TP
print("\n" + "="*100)
print("OPTIMAL CONFIGURATION BY TARGET PROFIT")
print("="*100)

for tp in tp_values:
    tp_df = df[df['tp'] == tp]
    if tp_df.empty:
        continue
    best = tp_df.loc[tp_df['pnl'].idxmax()]
    print(f"TP ${tp:.2f}: {best['max_candles']:.0f} candles | WR {best['win_rate']:.1f}% | P&L ${best['pnl']:.2f}")

# Best overall
best = df.loc[df['pnl'].idxmax()]
print(f"\n[OVERALL BEST]")
print(f"  TargetProfit: ${best['tp']:.2f}")
print(f"  Max Candles: {best['max_candles']:.0f}")
print(f"  Win Rate: {best['win_rate']:.1f}%")
print(f"  Total P&L: ${best['pnl']:.2f}")
print(f"  vs Actual: ${best['vs_actual']:+.2f}")

print(f"\n[ACTUAL]")
print(f"  Total P&L: ${actual_total:.2f}")
print(f"  Avg per trade: ${actual_total/len(pos_data):.2f}")

if best['pnl'] > actual_total:
    print(f"\n[WINNER] Fixed TP + Time Exit is better by ${best['pnl'] - actual_total:.2f}")
else:
    print(f"\n[WINNER] Current trailing stop is better by ${actual_total - best['pnl']:.2f}")

mt5.shutdown()

# Save
df.to_csv('time_exit_candle_results.csv', index=False)
print("\n[SAVED] Results saved to time_exit_candle_results.csv")
