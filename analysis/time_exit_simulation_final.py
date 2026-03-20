#!/usr/bin/env python3
"""
Time-Based Exit Simulation
TP = 20 points, Time cutoffs 2-30 minutes
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
    """
    Simulate position with time-based exit.
    - If TP hit within max_minutes -> Take profit at TP
    - If TP not hit -> Exit at close price of candle at max_minutes
    
    Returns: {'outcome': 'TP_HIT' or 'TIME_EXIT', 'pnl': float, 'exit_time_min': float}
    """
    tp_price_move = tp_points / 100  # points to price
    
    if direction == 'BUY':
        tp_price = open_price + tp_price_move
    else:
        tp_price = open_price - tp_price_move
    
    bars = bars_df.sort_values('time').reset_index(drop=True)
    cutoff_time = entry_time + timedelta(minutes=max_minutes)
    
    # First, check if TP is hit before cutoff
    for i, bar in bars.iterrows():
        candle_num = i + 1
        bar_end = bar['time'] + timedelta(minutes=1)
        
        # Stop if we've passed cutoff
        if bar['time'] > cutoff_time:
            break
        
        if candle_num == 1:
            # First candle: check ticks from entry to min(bar_end, cutoff)
            effective_end = min(bar_end, cutoff_time)
            candle_ticks = ticks_df[(ticks_df['time'] >= entry_time) & (ticks_df['time'] < effective_end)]
            
            if candle_ticks.empty:
                continue
            
            if direction == 'BUY':
                if (candle_ticks['price'] >= tp_price).any():
                    # TP hit - calculate P&L
                    pnl = tp_points * 0.01  # $0.01 per point on 0.01 lot
                    exit_time = (candle_ticks[candle_ticks['price'] >= tp_price].iloc[0]['time'] - entry_time).total_seconds() / 60
                    return {'outcome': 'TP_HIT', 'pnl': pnl, 'exit_time_min': exit_time}
            else:  # SELL
                if (candle_ticks['price'] <= tp_price).any():
                    pnl = tp_points * 0.01
                    exit_time = (candle_ticks[candle_ticks['price'] <= tp_price].iloc[0]['time'] - entry_time).total_seconds() / 60
                    return {'outcome': 'TP_HIT', 'pnl': pnl, 'exit_time_min': exit_time}
        else:
            # Check if cutoff falls within this candle
            if bar['time'] <= cutoff_time < bar_end:
                # Cutoff is mid-candle, check OHLC up to cutoff
                # For simplicity, check if TP hit in this bar
                pass
            
            # Check OHLC
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    pnl = tp_points * 0.01
                    exit_time = (bar['time'] - entry_time).total_seconds() / 60 + 0.5  # Approximate mid-candle
                    return {'outcome': 'TP_HIT', 'pnl': pnl, 'exit_time_min': exit_time}
            else:  # SELL
                if tp_price >= bar['low']:
                    pnl = tp_points * 0.01
                    exit_time = (bar['time'] - entry_time).total_seconds() / 60 + 0.5
                    return {'outcome': 'TP_HIT', 'pnl': pnl, 'exit_time_min': exit_time}
    
    # TP not hit - exit at cutoff time
    # Find price at cutoff
    bars_before_cutoff = bars[bars['time'] <= cutoff_time]
    if bars_before_cutoff.empty:
        return None
    
    last_bar = bars_before_cutoff.iloc[-1]
    
    # If cutoff is mid-candle, use close as approximation
    exit_price = last_bar['close']
    
    if direction == 'BUY':
        pnl = (exit_price - open_price) * 0.01
    else:
        pnl = (open_price - exit_price) * 0.01
    
    return {'outcome': 'TIME_EXIT', 'pnl': pnl, 'exit_time_min': max_minutes}

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
print("TIME-BASED EXIT SIMULATION")
print("="*100)
print(f"TP: 20 points ($0.20) | Positions: {len(clean)}")
print("\nRule: Exit at TP if hit within time limit, else exit at market price")
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

# Time cutoffs
time_cutoffs = list(range(2, 31))  # 2 to 30 minutes
tp_points = 20  # 20 points = $0.20

actual_total = sum(p['actual_norm'] for p in pos_data)

print("\n" + "="*100)
print("RESULTS")
print("="*100)
print(f"\n{'Cutoff':>8} | {'TP Hits':>9} | {'Time Exits':>12} | {'Win Rate':>9} | {'Simulated P&L':>15} | {'vs Actual':>12}")
print("-" * 90)

results = []

for cutoff in time_cutoffs:
    sim_results = []
    
    for pdata in pos_data:
        result = simulate_time_exit(
            pdata['pos']['open_price'],
            pdata['pos']['direction'],
            tp_points,
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
        wins = sum(1 for r in sim_results if r['pnl'] > 0)
        total_pnl = sum(r['pnl'] for r in sim_results)
        win_rate = wins / len(sim_results) * 100
        vs_actual = total_pnl - actual_total
        
        results.append({
            'cutoff': cutoff,
            'tp_hits': tp_hits,
            'time_exits': time_exits,
            'total': len(sim_results),
            'win_rate': win_rate,
            'simulated_pnl': total_pnl,
            'vs_actual': vs_actual
        })
        
        marker = " <-- BEST" if total_pnl == max([x['simulated_pnl'] for x in results]) else ""
        print(f"{cutoff:>6}min | {tp_hits:>4}/{len(sim_results)} | {time_exits:>6}/{len(sim_results)} | "
              f"{win_rate:>7.1f}% | ${total_pnl:>13.2f} | ${vs_actual:>+10.2f}{marker}")

# Summary
print("\n" + "="*100)
print("SUMMARY")
print("="*100)

best = max(results, key=lambda x: x['simulated_pnl'])

print(f"\n[ACTUAL PERFORMANCE]")
print(f"  Total P&L: ${actual_total:.2f}")

print(f"\n[BEST SIMULATED]")
print(f"  Time Cutoff: {best['cutoff']} minutes")
print(f"  TP: $0.20 (20 points)")
print(f"  Simulated P&L: ${best['simulated_pnl']:.2f}")
print(f"  Win Rate: {best['win_rate']:.1f}%")
print(f"  TP Hits: {best['tp_hits']}/{best['total']}")
print(f"  vs Actual: ${best['vs_actual']:+.2f}")

if best['simulated_pnl'] > actual_total:
    print(f"\n[CONCLUSION] Time-based exit is BETTER by ${best['simulated_pnl'] - actual_total:.2f}")
else:
    print(f"\n[CONCLUSION] Current trailing stop is BETTER by ${actual_total - best['simulated_pnl']:.2f}")

mt5.shutdown()

# Save
results_df = pd.DataFrame(results)
results_df.to_csv('time_exit_simulation_tp20.csv', index=False)
print("\n[SAVED] Results saved to time_exit_simulation_tp20.csv")
