#!/usr/bin/env python3
"""
Verify tick data accuracy against M1 OHLC
And calculate correct MFE/MAE
"""
import sys
sys.path.insert(0, r'c:\Trading_GU')
import MetaTrader5 as mt5
import gu_tools
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

def fetch_ticks_range(symbol, from_time, to_time):
    """Fetch tick data for a time range."""
    ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # XAUUSD+ ticks don't have 'last', use bid/ask average
    if 'last' in df.columns:
        # Check if last is valid (non-zero)
        if df['last'].max() > 0:
            df['price'] = df['last']
        else:
            df['price'] = (df['bid'] + df['ask']) / 2
    else:
        df['price'] = (df['bid'] + df['ask']) / 2
    
    return df

def fetch_m1_bars(symbol, from_time, to_time):
    """Fetch M1 bars."""
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def calculate_mfe_mae_ticks(open_price, direction, ticks_df, holding_minutes=30):
    """Calculate MFE/MAE from tick data."""
    if ticks_df.empty:
        return None
    
    start_time = ticks_df['time'].iloc[0]
    end_time = start_time + timedelta(minutes=holding_minutes)
    window = ticks_df[ticks_df['time'] <= end_time].copy()
    
    if window.empty:
        return None
    
    max_price = window['price'].max()
    min_price = window['price'].min()
    close_price = window['price'].iloc[-1]
    
    if direction == 'BUY':
        mfe = max_price - open_price
        mae = open_price - min_price
        pnl = close_price - open_price
    else:  # SELL
        mfe = open_price - min_price
        mae = max_price - open_price
        pnl = open_price - close_price
    
    return {
        'mfe_points': mfe,
        'mae_points': mae,
        'pnl_points': pnl,
        'close_price': close_price,
        'max_price': max_price,
        'min_price': min_price,
        'tick_count': len(window)
    }

def calculate_mfe_mae_bars(open_price, direction, bars_df, holding_minutes=30):
    """Calculate MFE/MAE from M1 bar data."""
    if bars_df.empty:
        return None
    
    start_time = bars_df['time'].iloc[0]
    end_time = start_time + timedelta(minutes=holding_minutes)
    window = bars_df[bars_df['time'] <= end_time].copy()
    
    if window.empty:
        return None
    
    max_high = window['high'].max()
    min_low = window['low'].min()
    close_price = window['close'].iloc[-1]
    
    if direction == 'BUY':
        mfe = max_high - open_price
        mae = open_price - min_low
        pnl = close_price - open_price
    else:  # SELL
        mfe = open_price - min_low
        mae = max_high - open_price
        pnl = open_price - close_price
    
    return {
        'mfe_points': mfe,
        'mae_points': mae,
        'pnl_points': pnl,
        'close_price': close_price,
        'max_high': max_high,
        'min_low': min_low,
        'bar_count': len(window)
    }

# Connect to MT5
if not gu_tools.connect_mt5(r'C:\Program Files\MetaTrader 5\terminal64.exe'):
    print('Failed to connect')
    exit(1)

# Test with a sample position: 2026-03-11 02:07:00 MH SELL @ 5194.74
# Fetch 35 minutes of data
test_time = datetime(2026, 3, 11, 2, 7, 0, tzinfo=timezone.utc)
from_time = test_time
to_time = test_time + timedelta(minutes=35)

print("="*100)
print("TICK DATA VERIFICATION")
print("="*100)
print(f"\nTest period: {from_time} to {to_time}")
print(f"Symbol: XAUUSD+")

# Fetch ticks
ticks = fetch_ticks_range('XAUUSD+', from_time, to_time)
print(f"\nTicks fetched: {len(ticks)}")

if not ticks.empty:
    print(f"\nTick data summary:")
    print(f"  Time range: {ticks['time'].min()} to {ticks['time'].max()}")
    print(f"  Price range: {ticks['price'].min():.2f} to {ticks['price'].max():.2f}")
    print(f"  First tick: {ticks.iloc[0]['time']} @ {ticks.iloc[0]['price']:.2f}")
    print(f"  Last tick: {ticks.iloc[-1]['time']} @ {ticks.iloc[-1]['price']:.2f}")

# Fetch M1 bars
bars = fetch_m1_bars('XAUUSD+', from_time, to_time)
print(f"\nM1 bars fetched: {len(bars)}")

if not bars.empty:
    print(f"\nM1 bar data summary:")
    print(f"  Time range: {bars['time'].min()} to {bars['time'].max()}")
    print(f"  OHLC: {bars['open'].iloc[0]:.2f} / {bars['high'].max():.2f} / {bars['low'].min():.2f} / {bars['close'].iloc[-1]:.2f}")
    
    # Compare tick OHLC to bar OHLC
    print("\n" + "-"*80)
    print("COMPARISON: Tick-derived OHLC vs M1 Bar OHLC")
    print("-"*80)
    
    for i, bar in bars.iterrows():
        bar_start = bar['time']
        bar_end = bar_start + timedelta(minutes=1)
        
        # Get ticks for this bar
        bar_ticks = ticks[(ticks['time'] >= bar_start) & (ticks['time'] < bar_end)]
        
        if len(bar_ticks) > 0:
            tick_open = bar_ticks.iloc[0]['price']
            tick_high = bar_ticks['price'].max()
            tick_low = bar_ticks['price'].min()
            tick_close = bar_ticks.iloc[-1]['price']
            
            print(f"\nBar {bar_start.strftime('%H:%M')}:")
            print(f"  Bar OHLC:  {bar['open']:.2f} / {bar['high']:.2f} / {bar['low']:.2f} / {bar['close']:.2f}")
            print(f"  Tick OHLC: {tick_open:.2f} / {tick_high:.2f} / {tick_low:.2f} / {tick_close:.2f}")
            print(f"  Ticks: {len(bar_ticks)}")
            
            # Check match
            match_high = abs(bar['high'] - tick_high) < 0.01
            match_low = abs(bar['low'] - tick_low) < 0.01
            match = match_high and match_low
            print(f"  Match: {'YES' if match else 'NO'}")
            
            if i >= 2:  # Only show first 3 bars
                print("  ... (truncated)")
                break

# Now calculate MFE/MAE for a sample position
print("\n" + "="*100)
print("MFE/MAE CALCULATION TEST")
print("="*100)

open_price = 5194.74
direction = 'SELL'

print(f"\nPosition: {direction} @ {open_price}")
print(f"Point value for 0.01 lot: $0.01 per point")

# Calculate from ticks
tick_result = calculate_mfe_mae_ticks(open_price, direction, ticks, 30)
if tick_result:
    print(f"\nFrom TICK data (30 min):")
    print(f"  MFE: {tick_result['mfe_points']:.2f} points = ${tick_result['mfe_points'] * 0.01:.2f} (0.01 lot)")
    print(f"  MAE: {tick_result['mae_points']:.2f} points = ${tick_result['mae_points'] * 0.01:.2f} (0.01 lot)")
    print(f"  PnL at 30min: {tick_result['pnl_points']:.2f} points = ${tick_result['pnl_points'] * 0.01:.2f} (0.01 lot)")
    print(f"  Price range: {tick_result['min_price']:.2f} - {tick_result['max_price']:.2f}")

# Calculate from bars
bar_result = calculate_mfe_mae_bars(open_price, direction, bars, 30)
if bar_result:
    print(f"\nFrom M1 BAR data (30 min):")
    print(f"  MFE: {bar_result['mfe_points']:.2f} points = ${bar_result['mfe_points'] * 0.01:.2f} (0.01 lot)")
    print(f"  MAE: {bar_result['mae_points']:.2f} points = ${bar_result['mae_points'] * 0.01:.2f} (0.01 lot)")
    print(f"  PnL at 30min: {bar_result['pnl_points']:.2f} points = ${bar_result['pnl_points'] * 0.01:.2f} (0.01 lot)")

# Compare
if tick_result and bar_result:
    print("\n" + "-"*80)
    print("COMPARISON:")
    print(f"  MFE diff: {abs(tick_result['mfe_points'] - bar_result['mfe_points']):.2f} points")
    print(f"  MAE diff: {abs(tick_result['mae_points'] - bar_result['mae_points']):.2f} points")
    print(f"  PnL diff: {abs(tick_result['pnl_points'] - bar_result['pnl_points']):.2f} points")
    
    if abs(tick_result['mfe_points'] - bar_result['mfe_points']) < 0.1:
        print("\n[VERIFIED] Tick data matches M1 bars within 0.1 points")
    else:
        print("\n[WARNING] Tick data differs from M1 bars!")

mt5.shutdown()
print("\n[COMPLETE]")
