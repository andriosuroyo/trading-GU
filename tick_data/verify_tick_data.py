"""Verify existing tick data files against Vantage source"""
import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def connect_mt5():
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    return True

def verify_file(filepath):
    """Verify a single tick data file"""
    try:
        df = pd.read_parquet(filepath)
        
        # Basic stats
        stats = {
            'file': filepath.name,
            'rows': len(df),
            'columns': list(df.columns),
            'time_min': df['time'].min(),
            'time_max': df['time'].max(),
            'bid_min': df['bid'].min(),
            'bid_max': df['bid'].max(),
            'ask_min': df['ask'].min(),
            'ask_max': df['ask'].max(),
            'nulls': df.isnull().sum().sum(),
        }
        
        # Check for time gaps (shouldn't be gaps > 5 minutes during trading hours)
        df_sorted = df.sort_values('time')
        time_diffs = df_sorted['time'].diff().dt.total_seconds()
        large_gaps = time_diffs[time_diffs > 300]  # gaps > 5 minutes
        stats['large_gaps'] = len(large_gaps)
        if len(large_gaps) > 0:
            stats['max_gap_min'] = time_diffs.max() / 60
        
        # Check for price anomalies
        price_spread = df['ask'] - df['bid']
        stats['avg_spread'] = price_spread.mean()
        stats['max_spread'] = price_spread.max()
        
        # Sample rate (ticks per minute during active hours)
        duration_hours = (stats['time_max'] - stats['time_min']).total_seconds() / 3600
        if duration_hours > 0:
            stats['ticks_per_hour'] = stats['rows'] / duration_hours
        
        return stats
    except Exception as e:
        return {'file': filepath.name, 'error': str(e)}

def check_source_availability(date_str):
    """Check if Vantage has tick data for this date"""
    try:
        date = datetime.strptime(date_str, '%Y%m%d').replace(tzinfo=timezone.utc)
        day_start = date.replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)
        
        ticks = mt5.copy_ticks_range('XAUUSD+', day_start, day_end, mt5.COPY_TICKS_ALL)
        if ticks is None or len(ticks) == 0:
            return {'available': False, 'count': 0}
        
        # Get actual time range
        first_tick = datetime.fromtimestamp(ticks[0][0], tz=timezone.utc)
        last_tick = datetime.fromtimestamp(ticks[-1][0], tz=timezone.utc)
        
        return {
            'available': True, 
            'count': len(ticks),
            'first': first_tick,
            'last': last_tick
        }
    except Exception as e:
        return {'available': False, 'error': str(e)}

def main():
    print("=" * 80)
    print("TICK DATA VERIFICATION REPORT")
    print("=" * 80)
    
    # Check all stored files
    storage_dir = Path(__file__).parent
    files = sorted(storage_dir.glob("ticks_*.parquet"))
    
    print(f"\nFound {len(files)} tick data files\n")
    
    # First verify file integrity
    print("-" * 80)
    print("LOCAL FILE INTEGRITY CHECK")
    print("-" * 80)
    
    file_stats = []
    for f in files:
        stats = verify_file(f)
        file_stats.append(stats)
        
        if 'error' in stats:
            print(f"\n{stats['file']}: ERROR - {stats['error']}")
        else:
            print(f"\n{stats['file']}:")
            print(f"  Rows: {stats['rows']:,}")
            print(f"  Time: {stats['time_min']} to {stats['time_max']}")
            print(f"  Bid range: {stats['bid_min']:.2f} - {stats['bid_max']:.2f}")
            print(f"  Avg spread: {stats['avg_spread']:.2f} pts")
            print(f"  Large time gaps (>5min): {stats['large_gaps']}")
            if 'ticks_per_hour' in stats:
                print(f"  Ticks/hour: {stats['ticks_per_hour']:,.0f}")
    
    # Connect to MT5 and verify against source
    print("\n" + "=" * 80)
    print("SOURCE AVAILABILITY CHECK (Vantage)")
    print("=" * 80)
    
    if not connect_mt5():
        print("Failed to connect to MT5")
        return
    
    try:
        info = mt5.account_info()
        print(f"\nConnected: {info.server} | Account: {info.login}")
        
        for f in files:
            date_str = f.stem.replace('ticks_', '')
            source_info = check_source_availability(date_str)
            
            print(f"\n{date_str}:")
            if source_info.get('available'):
                print(f"  Source AVAILABLE: {source_info['count']:,} ticks")
                print(f"  Time range: {source_info['first']} to {source_info['last']}")
                
                # Compare with local
                local_stats = next((s for s in file_stats if s['file'] == f.name), None)
                if local_stats and 'rows' in local_stats:
                    local_count = local_stats['rows']
                    diff = source_info['count'] - local_count
                    if abs(diff) > 1000:  # Significant difference
                        print(f"  LOCAL: {local_count:,} ticks")
                        print(f"  DIFFERENCE: {diff:+,} ticks ({diff/source_info['count']*100:+.1f}%)")
                        print(f"  STATUS: ⚠️ SIGNIFICANT MISMATCH")
                    else:
                        print(f"  LOCAL: {local_count:,} ticks ✓ MATCH")
            else:
                print(f"  Source: NOT AVAILABLE")
                print(f"  STATUS: ⚠️ CANNOT VERIFY - Source data expired")
    
    finally:
        mt5.shutdown()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY & OPTIONS")
    print("=" * 80)
    
    print("""
REPLACEMENT OPTIONS:

1. SAFE TO REPLACE (Source data confirmed available):
   - Files where source shows more ticks than local
   - These can be re-fetched from Vantage

2. KEEP LOCAL (Source data NOT available):
   - Older dates where Vantage no longer has tick history
   - These are irreplaceable - DO NOT DELETE

3. PARTIAL DAYS:
   - Files with incomplete time coverage
   - Can be supplemented but not fully replaced
""")

if __name__ == "__main__":
    main()
