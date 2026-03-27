"""
Replace tick data from March 13-20 with fresh Vantage data.
Ensures no duplicates, validates integrity, backs up old files.
"""
import MetaTrader5 as mt5
import pandas as pd
import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

def load_env():
    """Load environment variables"""
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
    """Connect to Vantage MT5"""
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    print(f"Connected: {info.server} | Account: {info.login}")
    return True

def fetch_tick_data(date):
    """Fetch tick data for a specific date"""
    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    ticks = mt5.copy_ticks_range('XAUUSD+', day_start, day_end, mt5.COPY_TICKS_ALL)
    
    if ticks is None or len(ticks) == 0:
        return None
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    
    # Remove exact duplicates based on timestamp
    df = df.drop_duplicates(subset=['time']).sort_values('time').reset_index(drop=True)
    
    return df

def validate_tick_data(df, date_str):
    """Validate tick data for anomalies"""
    issues = []
    
    # Check 1: Minimum tick count (should be >100K for a full day)
    if len(df) < 100000:
        issues.append(f"Low tick count: {len(df):,} (expected >100K)")
    
    # Check 2: Time range coverage (should cover most of 00:00-23:59)
    time_span = df['time'].max() - df['time'].min()
    if time_span.total_seconds() < 20 * 3600:  # Less than 20 hours
        issues.append(f"Short time span: {time_span} (expected >20h)")
    
    # Check 3: Price anomalies (bid/ask should be within reasonable gold range)
    if df['bid'].min() < 1000 or df['bid'].max() > 10000:
        issues.append(f"Price out of range: {df['bid'].min():.2f} - {df['bid'].max():.2f}")
    
    # Check 4: Negative spreads (bid > ask is invalid)
    negative_spreads = (df['bid'] > df['ask']).sum()
    if negative_spreads > 0:
        issues.append(f"Negative spreads: {negative_spreads} ticks")
    
    # Check 5: Large spreads (>50 points is suspicious)
    spread = df['ask'] - df['bid']
    large_spreads = (spread > 50).sum()
    if large_spreads > len(df) * 0.01:  # More than 1% of ticks
        issues.append(f"Large spreads (>50 pts): {large_spreads} ticks ({large_spreads/len(df)*100:.1f}%)")
    
    # Check 6: Time gaps (>10 minutes during market hours is suspicious)
    time_diffs = df['time'].diff().dt.total_seconds()
    large_gaps = (time_diffs > 600).sum()  # 10 minutes
    if large_gaps > 10:  # More than 10 large gaps
        issues.append(f"Large time gaps (>10min): {large_gaps}")
    
    return issues

def replace_tick_data(dates_to_replace):
    """Replace tick data for specified dates"""
    storage_dir = Path(__file__).parent
    backup_dir = storage_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    results = []
    
    for date_str in dates_to_replace:
        date = datetime.strptime(date_str, '%Y%m%d').replace(tzinfo=timezone.utc)
        filename = storage_dir / f"ticks_{date_str}.parquet"
        backup_file = backup_dir / f"ticks_{date_str}_backup.parquet"
        
        print(f"\n{'='*70}")
        print(f"Processing {date_str}")
        print(f"{'='*70}")
        
        # Step 1: Backup existing file
        if filename.exists():
            shutil.copy2(filename, backup_file)
            old_size = filename.stat().st_size / 1024 / 1024
            print(f"Backed up: {filename.name} ({old_size:.2f} MB) -> backup/")
        
        # Step 2: Fetch fresh data
        print(f"Fetching fresh data from Vantage...")
        df = fetch_tick_data(date)
        
        if df is None or df.empty:
            print(f"ERROR: No data received from Vantage for {date_str}")
            results.append({
                'date': date_str,
                'status': 'FAILED',
                'reason': 'No data from source'
            })
            continue
        
        print(f"Received: {len(df):,} ticks")
        print(f"Time range: {df['time'].min()} to {df['time'].max()}")
        
        # Step 3: Validate
        print(f"Validating...")
        issues = validate_tick_data(df, date_str)
        
        if issues:
            print(f"WARNINGS:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"Validation: PASSED")
        
        # Step 4: Replace file (overwrite, don't merge)
        df.to_parquet(filename, index=False, compression='snappy')
        new_size = filename.stat().st_size / 1024 / 1024
        
        print(f"Saved: {filename.name} ({new_size:.2f} MB)")
        
        # Step 5: Verify written file
        verify_df = pd.read_parquet(filename)
        if len(verify_df) == len(df):
            print(f"Verification: OK ({len(verify_df):,} ticks confirmed)")
            status = 'SUCCESS'
        else:
            print(f"ERROR: Verification failed! Written {len(verify_df)}, expected {len(df)}")
            status = 'VERIFICATION_FAILED'
        
        results.append({
            'date': date_str,
            'status': status,
            'ticks': len(df),
            'size_mb': new_size,
            'issues': issues
        })
    
    return results

def main():
    dates = ['20260313', '20260316', '20260317', '20260318', '20260319', '20260320']
    
    print("="*70)
    print("TICK DATA REPLACEMENT - MARCH 13-20, 2026")
    print("="*70)
    print(f"\nTarget dates: {', '.join(dates)}")
    print("Strategy: Full replacement with validation + backup")
    
    if not connect_mt5():
        print("Failed to connect to MT5. Aborting.")
        return
    
    try:
        results = replace_tick_data(dates)
        
        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        
        success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
        failed_count = len(results) - success_count
        
        for r in results:
            status_icon = "OK" if r['status'] == 'SUCCESS' else "FAIL"
            print(f"{r['date']}: {status_icon} | {r.get('ticks', 0):,} ticks")
            if r.get('issues'):
                for issue in r['issues']:
                    print(f"           WARN: {issue}")
        
        print(f"\nTotal: {success_count} succeeded, {failed_count} failed")
        print(f"Backups saved to: tick_data/backup/")
        
    finally:
        mt5.shutdown()
        print("\nDisconnected from MT5")

if __name__ == "__main__":
    main()
