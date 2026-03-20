#!/usr/bin/env python3
"""
Trace the outlier position step by step
2026-03-12 08:41 SELL @ 5152.55
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

# Connect
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    exit(1)

# The outlier position
outlier_time = datetime(2026, 3, 12, 8, 41, 0, tzinfo=timezone.utc)
open_price = 5152.55
direction = 'SELL'

print("="*100)
print("TRACING OUTLIER POSITION")
print("="*100)
print(f"Time: {outlier_time}")
print(f"Direction: {direction}")
print(f"Open Price: {open_price}")
print()

# Fetch data
bar_from = outlier_time.replace(second=0, microsecond=0)
bar_to = bar_from + timedelta(minutes=40)
bars = fetch_m1_bars('XAUUSD+', bar_from, bar_to)

tick_from = outlier_time
tick_to = outlier_time + timedelta(minutes=5)
ticks = fetch_ticks('XAUUSD+', tick_from, tick_to)

print(f"Fetched {len(bars)} M1 bars")
print(f"Fetched {len(ticks)} ticks")

# Print first few bars
print("\n" + "="*100)
print("M1 BARS (first 10)")
print("="*100)
print(f"{'Candle #':<10} {'Time':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10}")
print("-" * 80)

for i, bar in bars.head(10).iterrows():
    candle_num = i + 1
    print(f"{candle_num:<10} {str(bar['time']):<20} {bar['open']:<10.2f} {bar['high']:<10.2f} {bar['low']:<10.2f} {bar['close']:<10.2f}")

# Show remaining bars count
if len(bars) > 10:
    print(f"... ({len(bars) - 10} more bars)")

# Print tick data for first candle
print("\n" + "="*100)
print("TICKS (first 2 minutes)")
print("="*100)
print(f"{'Time':<25} {'Price':<10}")
print("-" * 40)

for _, tick in ticks.head(20).iterrows():
    print(f"{str(tick['time']):<25} {tick['price']:<10.2f}")

if len(ticks) > 20:
    print(f"... ({len(ticks) - 20} more ticks)")

# Now check each TP level manually
print("\n" + "="*100)
print("TP HIT ANALYSIS (manual check)")
print("="*100)

tp_levels = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110]

for tp_pts in tp_levels:
    tp_price_move = tp_pts / 100
    
    if direction == 'BUY':
        tp_price = open_price + tp_price_move
    else:  # SELL
        tp_price = open_price - tp_price_move
    
    print(f"\nTP {tp_pts} points (${tp_pts*0.01:.2f}):")
    print(f"  Target price: {tp_price:.2f}")
    
    # Check each candle
    found = False
    for i, bar in bars.iterrows():
        candle_num = i + 1
        
        if candle_num == 1:
            # Check ticks
            bar_end = bar['time'] + timedelta(minutes=1)
            candle_ticks = ticks[(ticks['time'] >= outlier_time) & (ticks['time'] < bar_end)]
            
            if not candle_ticks.empty:
                if direction == 'BUY':
                    hit = (candle_ticks['price'] >= tp_price).any()
                    if hit:
                        hit_price = candle_ticks[candle_ticks['price'] >= tp_price].iloc[0]['price']
                        print(f"  [HIT] Candle 1 at price {hit_price:.2f}")
                        found = True
                        break
                else:  # SELL
                    hit = (candle_ticks['price'] <= tp_price).any()
                    if hit:
                        hit_price = candle_ticks[candle_ticks['price'] <= tp_price].iloc[0]['price']
                        print(f"  [HIT] Candle 1 at price {hit_price:.2f}")
                        found = True
                        break
        else:
            # Check OHLC
            if direction == 'BUY':
                if tp_price <= bar['high']:
                    print(f"  [HIT] Candle {candle_num} (high: {bar['high']:.2f})")
                    found = True
                    break
            else:  # SELL
                if tp_price >= bar['low']:
                    print(f"  [HIT] Candle {candle_num} (low: {bar['low']:.2f})")
                    found = True
                    break
        
        # Safety break
        if candle_num > 36:
            print(f"  [NOT FOUND] First 36 candles")
            break
    
    if not found:
        print(f"  [MISS] Not hit")

# Check the price range of this position
print("\n" + "="*100)
print("PRICE RANGE ANALYSIS")
print("="*100)

all_highs = bars['high'].tolist()
all_lows = bars['low'].tolist()

# Include first candle ticks
bar0_end = bars.iloc[0]['time'] + timedelta(minutes=1)
first_candle_ticks = ticks[(ticks['time'] >= outlier_time) & (ticks['time'] < bar0_end)]
if not first_candle_ticks.empty:
    all_highs.extend(first_candle_ticks['price'].tolist())
    all_lows.extend(first_candle_ticks['price'].tolist())

max_price = max(all_highs)
min_price = min(all_lows)

print(f"Open price: {open_price:.2f}")
print(f"Max price: {max_price:.2f}")
print(f"Min price: {min_price:.2f}")

if direction == 'SELL':
    max_move = open_price - min_price
    print(f"Max favorable move (SELL): {max_move:.2f} price = {max_move*100:.0f} points")
else:
    max_move = max_price - open_price
    print(f"Max favorable move (BUY): {max_move:.2f} price = {max_move*100:.0f} points")

mt5.shutdown()
print("\n[COMPLETE]")
