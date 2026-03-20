#!/usr/bin/env python3
"""
Multi-TP Candle Close Analysis
TP levels: 30, 40, 50, ... 300 points
Time cutoffs: 2-30 minutes
Uses candle close for time exits
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
print("MULTI-TP CANDLE CLOSE ANALYSIS - ASIA SESSION")
print("="*120)
print(f"Positions: {len(clean)}")
print("\nFor each TP: If hit within cutoff -> take TP, else exit at candle close")
print()

# Fetch data
print("Fetching data...")
pos_data = []
for pos in clean:
    bar_from = pos['open_time'].replace(second=0, microsecond=0)
    bar_to = bar_from + timedelta(minutes=35)
    bars = fetch_m1_bars('XAUUSD+', bar_from, bar_to)
    
    if not bars.empty and len(bars) >= 2:
        norm = pos['lot_size'] * 100
        pos_data.append({
            'pos': pos,
            'bars': bars,
            'actual_norm': pos['net_pl'] / norm
        })

print(f"Loaded {len(pos_data)} positions")
actual_total = sum(p['actual_norm'] for p in pos_data)

# TP values and time cutoffs
tp_values = list(range(30, 301, 10))  # 30, 40, 50, ... 300
time_cutoffs = [2, 3, 5, 10, 15, 20, 30]

print("\n" + "="*120)
print("RESULTS BY TP LEVEL")
print("="*120)

all_results = []

for tp in tp_values:
    print(f"\n{'='*80}")
    print(f"TP = {tp} points (${tp*0.01:.2f})")
    print(f"{'='*80}")
    print(f"{'Cutoff':>8} | {'TP Hits':>9} | {'Misses':>8} | {'Win%':>8} | {'Avg Miss P&L':>14} | {'Total P&L':>12}")
    print("-" * 85)
    
    for cutoff in time_cutoffs:
        tp_hits = 0
        misses = 0
        miss_pnls = []
        total_pnl = 0
        
        for pdata in pos_data:
            pos = pdata['pos']
            bars = pdata['bars'].sort_values('time').reset_index(drop=True)
            
            # Check if TP hit within cutoff
            tp_hit = False
            tp_price_move = tp / 100
            
            if pos['direction'] == 'BUY':
                tp_price = pos['open_price'] + tp_price_move
            else:
                tp_price = pos['open_price'] - tp_price_move
            
            for j, bar in bars.iterrows():
                candle_num = j + 1
                if candle_num > cutoff:
                    break
                
                if pos['direction'] == 'BUY':
                    if bar['high'] >= tp_price:
                        tp_hit = True
                        break
                else:
                    if bar['low'] <= tp_price:
                        tp_hit = True
                        break
            
            if tp_hit:
                total_pnl += tp * 0.01
                tp_hits += 1
            else:
                # Exit at close of cutoff candle
                if cutoff <= len(bars):
                    exit_price = bars.iloc[cutoff - 1]['close']
                else:
                    exit_price = bars.iloc[-1]['close']
                
                if pos['direction'] == 'BUY':
                    pnl = (exit_price - pos['open_price']) * 0.01
                else:
                    pnl = (pos['open_price'] - exit_price) * 0.01
                
                total_pnl += pnl
                misses += 1
                miss_pnls.append(pnl)
        
        win_rate = (tp_hits + sum(1 for p in miss_pnls if p > 0)) / len(pos_data) * 100
        avg_miss_pnl = sum(miss_pnls) / len(miss_pnls) if miss_pnls else 0
        
        all_results.append({
            'tp': tp,
            'cutoff': cutoff,
            'tp_hits': tp_hits,
            'misses': misses,
            'win_rate': win_rate,
            'avg_miss_pnl': avg_miss_pnl,
            'total_pnl': total_pnl
        })
        
        print(f"{cutoff:>6}min | {tp_hits:>4}/{len(pos_data)} | {misses:>4}/{len(pos_data)} | "
              f"{win_rate:>7.1f}% | ${avg_miss_pnl:>12.2f} | ${total_pnl:>10.2f}")

# Summary table
print("\n" + "="*120)
print("SUMMARY: BEST TIME CUTOFF BY TP")
print("="*120)
print(f"\n{'TP (pts)':>10} | {'TP ($)':>8} | {'Best Time':>10} | {'TP Hits':>9} | {'Misses':>8} | {'Win%':>8} | {'Total P&L':>12}")
print("-" * 100)

best_by_tp = []
for tp in tp_values:
    tp_data = [r for r in all_results if r['tp'] == tp]
    if not tp_data:
        continue
    best = max(tp_data, key=lambda x: x['total_pnl'])
    best_by_tp.append(best)
    print(f"{tp:>10} | ${tp*0.01:>6.2f} | {best['cutoff']:>7}min | {best['tp_hits']:>4}/{len(pos_data)} | "
          f"{best['misses']:>4}/{len(pos_data)} | {best['win_rate']:>7.1f}% | ${best['total_pnl']:>10.2f}")

# Find best overall
best_overall = max(best_by_tp, key=lambda x: x['total_pnl'])
print(f"\n{'='*120}")
print("BEST OVERALL CONFIGURATION")
print(f"{'='*120}")
print(f"TP: {best_overall['tp']} points (${best_overall['tp']*0.01:.2f})")
print(f"Time Cutoff: {best_overall['cutoff']} minutes")
print(f"TP Hits: {best_overall['tp_hits']}/{len(pos_data)}")
print(f"Misses: {best_overall['misses']}/{len(pos_data)}")
print(f"Win Rate: {best_overall['win_rate']:.1f}%")
print(f"Avg Miss P&L: ${best_overall['avg_miss_pnl']:.2f}")
print(f"Total P&L: ${best_overall['total_pnl']:.2f}")

print(f"\n{'='*120}")
print("ACTUAL PERFORMANCE COMPARISON")
print(f"{'='*120}")
print(f"Actual P&L (trailing stop): ${actual_total:.2f}")
print(f"Best Simulated P&L: ${best_overall['total_pnl']:.2f}")
print(f"Difference: ${best_overall['total_pnl'] - actual_total:+.2f}")

mt5.shutdown()

# Save
results_df = pd.DataFrame(all_results)
results_df.to_csv('multi_tp_candle_close_results.csv', index=False)
print(f"\n[SAVED] Results saved to multi_tp_candle_close_results.csv")
