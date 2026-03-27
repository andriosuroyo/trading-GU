"""Check BlackBull tick data availability and quality"""
import MetaTrader5 as mt5
import os
from datetime import datetime, timezone, timedelta
import pandas as pd

def load_env():
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def connect_blackbull():
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_BLACKBULL")
    if not mt5.initialize(path=terminal_path):
        print(f"BlackBull MT5 init failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    print(f"Connected to BlackBull: {info.server} | Account: {info.login}")
    return True

def check_symbol():
    """Check available gold symbols on BlackBull"""
    symbols = mt5.symbols_get()
    gold_symbols = [s.name for s in symbols if 'XAU' in s.name or 'GOLD' in s.name]
    print("\nAvailable Gold Symbols on BlackBull:")
    for s in gold_symbols[:10]:  # Limit output
        info = mt5.symbol_info(s)
        if info:
            print(f"  {s}: spread={info.spread}, trade_allowed={info.trade_mode}")
    return gold_symbols

def fetch_tick_sample(date):
    """Fetch tick data sample for a date"""
    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    # Try XAUUSDp first (BlackBull convention)
    symbol = "XAUUSDp"
    ticks = mt5.copy_ticks_range(symbol, day_start, day_end, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        # Try XAUUSD+
        symbol = "XAUUSD+"
        ticks = mt5.copy_ticks_range(symbol, day_start, day_end, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        return None, None
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    
    return df, symbol

def main():
    print("="*70)
    print("BLACKBULL TICK DATA CHECK")
    print("="*70)
    
    if not connect_blackbull():
        return
    
    try:
        # Check symbols
        gold_symbols = check_symbol()
        
        # Check tick data for recent dates
        print("\n" + "="*70)
        print("TICK DATA AVAILABILITY")
        print("="*70)
        
        dates_to_check = [
            datetime(2026, 3, 13, tzinfo=timezone.utc),
            datetime(2026, 3, 16, tzinfo=timezone.utc),
            datetime(2026, 3, 17, tzinfo=timezone.utc),
            datetime(2026, 3, 18, tzinfo=timezone.utc),
            datetime(2026, 3, 19, tzinfo=timezone.utc),
            datetime(2026, 3, 20, tzinfo=timezone.utc),
        ]
        
        for date in dates_to_check:
            df, symbol_used = fetch_tick_sample(date)
            
            if df is not None:
                print(f"\n{date.date()}:")
                print(f"  Symbol: {symbol_used}")
                print(f"  Ticks: {len(df):,}")
                print(f"  Time: {df['time'].min()} to {df['time'].max()}")
                print(f"  Bid range: {df['bid'].min():.2f} - {df['bid'].max():.2f}")
                print(f"  Sample rate: {len(df)/24:,.0f} ticks/hour")
            else:
                print(f"\n{date.date()}: No tick data available")
        
        # Cross-check with Vantage for price alignment
        print("\n" + "="*70)
        print("CROSS-BROKER PRICE CHECK (Mar 20 sample)")
        print("="*70)
        
        # Get BlackBull price at specific time
        sample_time = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        bb_ticks = mt5.copy_ticks_range("XAUUSDp", sample_time - timedelta(minutes=1), 
                                        sample_time + timedelta(minutes=1), mt5.COPY_TICKS_ALL)
        
        if bb_ticks is not None and len(bb_ticks) > 0:
            bb_df = pd.DataFrame(bb_ticks)
            bb_df['time'] = pd.to_datetime(bb_df['time'], unit='s', utc=True)
            # Find closest tick
            closest_idx = (bb_df['time'] - sample_time).abs().idxmin()
            bb_price = bb_df.loc[closest_idx, 'bid']
            print(f"BlackBull XAUUSDp at {sample_time}: {bb_price:.2f}")
        else:
            print("BlackBull: No tick data at sample time")
        
    finally:
        mt5.shutdown()
        print("\nDisconnected from BlackBull")

if __name__ == "__main__":
    main()
