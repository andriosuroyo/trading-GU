"""
Tick Data Storage Manager
Fetches and stores tick data from Vantage to local storage
Keeps separate files per date, supports multi-file queries, unlimited retention
"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import os
import gzip
from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse
from typing import List, Optional, Tuple

def load_env():
    """Load environment variables"""
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    except:
        pass
    return env_vars

def connect_mt5():
    """Connect to MT5"""
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    return True

def get_tick_data(symbol, from_time, to_time):
    """Fetch tick data from MT5"""
    ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def get_storage_dir() -> Path:
    """Get or create tick data storage directory"""
    storage_dir = Path("tick_data")
    storage_dir.mkdir(exist_ok=True)
    return storage_dir

def get_tick_filename(date: datetime) -> Path:
    """Get filename for a specific date"""
    return get_storage_dir() / f"ticks_{date.strftime('%Y%m%d')}.parquet"

def save_ticks(df: pd.DataFrame, date: datetime) -> Path:
    """Save tick data for a specific date"""
    filename = get_tick_filename(date)
    
    # If file exists, load and merge
    if filename.exists():
        existing_df = pd.read_parquet(filename)
        # Merge and remove duplicates
        combined = pd.concat([existing_df, df]).drop_duplicates(subset=['time']).sort_values('time')
        combined.to_parquet(filename, index=False, compression='snappy')
        print(f"  Merged with existing data: {len(existing_df):,} + {len(df):,} -> {len(combined):,} ticks")
    else:
        df.to_parquet(filename, index=False, compression='snappy')
    
    return filename

def load_ticks_for_date(date: datetime) -> Optional[pd.DataFrame]:
    """Load tick data for a specific date"""
    filename = get_tick_filename(date)
    
    if not filename.exists():
        return None
    
    return pd.read_parquet(filename)

def load_ticks_for_range(from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """
    Load tick data across multiple dates
    Fetches from multiple parquet files and combines them
    """
    storage_dir = get_storage_dir()
    
    # Generate list of dates in range
    dates = []
    current = from_date.date()
    end = to_date.date()
    
    while current <= end:
        dates.append(datetime.combine(current, datetime.min.time(), tzinfo=timezone.utc))
        current += timedelta(days=1)
    
    # Load each day's data
    dataframes = []
    total_ticks = 0
    
    print(f"Loading tick data for {len(dates)} days ({from_date.date()} to {to_date.date()})...")
    
    for date in dates:
        filename = get_tick_filename(date)
        
        if filename.exists():
            df = pd.read_parquet(filename)
            
            # Filter to requested time range
            df = df[(df['time'] >= from_date) & (df['time'] <= to_date)]
            
            if not df.empty:
                dataframes.append(df)
                total_ticks += len(df)
                print(f"  {date.strftime('%Y-%m-%d')}: {len(df):,} ticks")
        else:
            print(f"  {date.strftime('%Y-%m-%d')}: FILE NOT FOUND")
    
    if not dataframes:
        print("No tick data found for the requested range")
        return pd.DataFrame()
    
    # Combine all dataframes
    combined = pd.concat(dataframes, ignore_index=True)
    combined = combined.sort_values('time').reset_index(drop=True)
    
    print(f"\nTotal loaded: {len(combined):,} ticks from {len(dataframes)} files")
    return combined

def load_all_ticks() -> pd.DataFrame:
    """Load all available tick data from storage"""
    storage_dir = get_storage_dir()
    files = sorted(storage_dir.glob("ticks_*.parquet"))
    
    if not files:
        print("No tick data files found")
        return pd.DataFrame()
    
    print(f"Loading all tick data from {len(files)} files...")
    
    dataframes = []
    total_ticks = 0
    
    for f in files:
        try:
            df = pd.read_parquet(f)
            dataframes.append(df)
            total_ticks += len(df)
            
            # Extract date from filename
            date_str = f.stem.replace('ticks_', '')
            print(f"  {date_str}: {len(df):,} ticks")
        except Exception as e:
            print(f"  ERROR loading {f.name}: {e}")
    
    combined = pd.concat(dataframes, ignore_index=True)
    combined = combined.sort_values('time').reset_index(drop=True)
    
    print(f"\nTotal loaded: {len(combined):,} ticks from {len(files)} files")
    print(f"Date range: {combined['time'].min()} to {combined['time'].max()}")
    
    return combined

def get_price_at_time(df: pd.DataFrame, target_time: datetime, tolerance_seconds: int = 2) -> Optional[dict]:
    """
    Get bid/ask price at a specific time from tick data
    Returns the closest tick within tolerance
    """
    if df.empty:
        return None
    
    tolerance = timedelta(seconds=tolerance_seconds)
    mask = (df['time'] >= target_time - tolerance) & (df['time'] <= target_time + tolerance)
    nearby = df[mask]
    
    if nearby.empty:
        return None
    
    # Get closest tick
    closest_idx = (nearby['time'] - target_time).abs().idxmin()
    closest = nearby.loc[closest_idx]
    
    return {
        'time': closest['time'],
        'bid': closest['bid'],
        'ask': closest['ask'],
        'time_diff_ms': abs((closest['time'] - target_time).total_seconds() * 1000)
    }

def estimate_storage():
    """Estimate storage requirements"""
    print("="*80)
    print("STORAGE ESTIMATION")
    print("="*80)
    
    if not connect_mt5():
        return
    
    try:
        now = datetime.now(timezone.utc)
        from_time = now - timedelta(hours=1)
        
        print("\nFetching 1 hour of tick data for estimation...")
        df = get_tick_data('XAUUSD+', from_time, now)
        
        if df is None or df.empty:
            print("No tick data available for estimation")
            return
        
        tick_count = len(df)
        
        # Test compression ratios
        csv_buffer = df.to_csv(index=False)
        csv_size = len(csv_buffer.encode('utf-8'))
        
        parquet_buffer = df.to_parquet(index=False, compression='snappy')
        parquet_size = len(parquet_buffer)
        
        gzipped = gzip.compress(csv_buffer.encode('utf-8'))
        gzip_size = len(gzipped)
        
        print(f"\nTicks in 1 hour: {tick_count:,}")
        print(f"\nStorage format comparison (per hour):")
        print(f"  Raw CSV:              {csv_size:>12,} bytes ({csv_size/tick_count:.1f} bytes/tick)")
        print(f"  Gzipped CSV:          {gzip_size:>12,} bytes ({gzip_size/tick_count:.1f} bytes/tick)")
        print(f"  Parquet (snappy):     {parquet_size:>12,} bytes ({parquet_size/tick_count:.1f} bytes/tick)")
        
        # Daily estimates
        ticks_per_day = tick_count * 24
        print(f"\nEstimated daily storage ({ticks_per_day:,} ticks):")
        print(f"  Raw CSV:              {csv_size * 24 / 1024 / 1024:>8.1f} MB/day")
        print(f"  Gzipped CSV:          {gzip_size * 24 / 1024 / 1024:>8.1f} MB/day")
        print(f"  Parquet (snappy):     {parquet_size * 24 / 1024 / 1024:>8.1f} MB/day")
        
        # Long-term estimates (unlimited retention)
        print(f"\nLong-term storage estimates (Parquet):")
        print(f"  30 days:              {parquet_size * 24 * 30 / 1024 / 1024:>8.1f} MB")
        print(f"  90 days:              {parquet_size * 24 * 90 / 1024 / 1024:>8.1f} MB")
        print(f"  365 days (1 year):    {parquet_size * 24 * 365 / 1024 / 1024 / 1024:>8.1f} GB")
        print(f"  3 years:              {parquet_size * 24 * 365 * 3 / 1024 / 1024 / 1024:>8.1f} GB")
        print(f"  5 years:              {parquet_size * 24 * 365 * 5 / 1024 / 1024 / 1024:>8.1f} GB")
        print(f"  10 years:             {parquet_size * 24 * 365 * 10 / 1024 / 1024 / 1024:>8.1f} GB")
        
        print("\n" + "="*80)
        print("STORAGE RECOMMENDATIONS")
        print("="*80)
        print("With modern hard drives (1-4 TB), storing 10+ years of tick data is feasible.")
        print("Recommended: Keep all data indefinitely (storage is cheap, data is valuable)")
        
    finally:
        mt5.shutdown()

def fetch_and_store_date(target_date: datetime):
    """Fetch and store tick data for a specific date"""
    if not connect_mt5():
        return
    
    try:
        day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        print(f"Fetching tick data for {day_start.date()}...")
        df = get_tick_data('XAUUSD+', day_start, day_end)
        
        if df is not None and not df.empty:
            filename = save_ticks(df, day_start)
            file_size = filename.stat().st_size
            print(f"  Saved {len(df):,} ticks to {filename.name}")
            print(f"  File size: {file_size / 1024 / 1024:.2f} MB")
        else:
            print("  No tick data available")
    
    finally:
        mt5.shutdown()

def fetch_and_store_today():
    """Fetch and store today's tick data"""
    now = datetime.now(timezone.utc)
    fetch_and_store_date(now)

def fetch_and_store_yesterday():
    """Fetch and store yesterday's tick data"""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    fetch_and_store_date(yesterday)

def fetch_historical(days_back: int):
    """Fetch historical tick data for the last N days"""
    if not connect_mt5():
        return
    
    try:
        now = datetime.now(timezone.utc)
        
        for day_offset in range(days_back, -1, -1):
            target_date = now - timedelta(days=day_offset)
            day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            filename = get_tick_filename(day_start)
            
            if filename.exists():
                existing_size = filename.stat().st_size
                existing_df = pd.read_parquet(filename)
                print(f"{day_start.date()}: EXISTS ({len(existing_df):,} ticks, {existing_size/1024/1024:.1f} MB)")
                continue
            
            day_end = day_start + timedelta(days=1)
            
            print(f"{day_start.date()}: Fetching...")
            df = get_tick_data('XAUUSD+', day_start, day_end)
            
            if df is not None and not df.empty:
                filename = save_ticks(df, day_start)
                file_size = filename.stat().st_size
                print(f"  Saved {len(df):,} ticks ({file_size/1024/1024:.1f} MB)")
            else:
                print(f"  No data available")
    
    finally:
        mt5.shutdown()

def list_stored_data():
    """List all stored tick data files"""
    storage_dir = get_storage_dir()
    files = sorted(storage_dir.glob("ticks_*.parquet"))
    
    if not files:
        print("No tick data files found")
        return
    
    print("="*80)
    print("STORED TICK DATA (Separate files per date)")
    print("="*80)
    print(f"\n{'Date':<15} {'Ticks':>12} {'Size (MB)':>12} {'Time Range':<30}")
    print("-"*80)
    
    total_size = 0
    total_ticks = 0
    earliest_date = None
    latest_date = None
    
    for f in files:
        try:
            df = pd.read_parquet(f)
            tick_count = len(df)
            size_mb = f.stat().st_size / 1024 / 1024
            total_size += f.stat().st_size
            total_ticks += tick_count
            
            if not df.empty:
                time_range = f"{df['time'].min().strftime('%H:%M')} - {df['time'].max().strftime('%H:%M')}"
                
                if earliest_date is None or df['time'].min() < earliest_date:
                    earliest_date = df['time'].min()
                if latest_date is None or df['time'].max() > latest_date:
                    latest_date = df['time'].max()
            else:
                time_range = "EMPTY"
            
            date_str = f.stem.replace('ticks_', '')
            print(f"{date_str:<15} {tick_count:>12,} {size_mb:>12.2f} {time_range:<30}")
        except Exception as e:
            print(f"{f.name:<15} {'ERROR':>12} {'':>12} {str(e):<30}")
    
    print("-"*80)
    print(f"{'TOTAL':<15} {total_ticks:>12,} {total_size / 1024 / 1024:>12.2f}")
    print("="*80)
    
    if earliest_date and latest_date:
        days_span = (latest_date - earliest_date).days + 1
        print(f"\nData span: {earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')} ({days_span} days)")
        print(f"Average per day: {total_ticks / len(files):,.0f} ticks, {total_size / len(files) / 1024 / 1024:.1f} MB")

def query_tick_data():
    """Interactive query tool for tick data"""
    print("="*80)
    print("TICK DATA QUERY TOOL")
    print("="*80)
    
    print("\nOptions:")
    print("1. Query specific date")
    print("2. Query date range")
    print("3. Query all available data")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        date_str = input("Enter date (YYYY-MM-DD): ").strip()
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            df = load_ticks_for_date(date)
            if df is not None:
                print(f"\nLoaded {len(df):,} ticks for {date_str}")
                print(df.head())
            else:
                print(f"No data found for {date_str}")
        except ValueError:
            print("Invalid date format")
    
    elif choice == '2':
        from_str = input("Enter start date (YYYY-MM-DD): ").strip()
        to_str = input("Enter end date (YYYY-MM-DD): ").strip()
        try:
            from_date = datetime.strptime(from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            to_date = datetime.strptime(to_str, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
            df = load_ticks_for_range(from_date, to_date)
            if not df.empty:
                print(f"\nLoaded {len(df):,} ticks from {from_str} to {to_str}")
                print(df.head())
        except ValueError:
            print("Invalid date format")
    
    elif choice == '3':
        df = load_all_ticks()
        if not df.empty:
            print(f"\nLoaded {len(df):,} ticks total")
            print(df.head())

def create_scheduler_script():
    """Create scheduler scripts for automatic collection"""
    
    # Hourly collection script
    hourly_script = '''@echo off
REM Tick Data Collection - Hourly Update
cd /d "C:\\Trading_GU"
python tick_storage_manager.py --fetch-today
echo %date% %time% - Hourly update >> tick_data\\collection.log
'''
    
    with open('run_tick_collection.bat', 'w') as f:
        f.write(hourly_script)
    
    # Daily full collection script
    daily_script = '''@echo off
REM Tick Data Collection - Daily Full Fetch
cd /d "C:\\Trading_GU"
python tick_storage_manager.py --fetch-yesterday
echo %date% %time% - Daily fetch completed >> tick_data\\collection.log
'''
    
    with open('run_tick_daily.bat', 'w') as f:
        f.write(daily_script)
    
    print("Created scheduler scripts:")
    print("  - run_tick_collection.bat (for hourly updates)")
    print("  - run_tick_daily.bat (for daily full fetch)")
    print("\nTo schedule:")
    print("1. Open Task Scheduler (taskschd.msc)")
    print("2. Create tasks to run these scripts hourly/daily")

def show_storage_stats():
    """Show storage statistics"""
    storage_dir = get_storage_dir()
    
    if not storage_dir.exists():
        print("No tick data storage found")
        return
    
    files = list(storage_dir.glob("ticks_*.parquet"))
    
    if not files:
        print("No tick data files found")
        return
    
    total_size = sum(f.stat().st_size for f in files)
    total_size_mb = total_size / 1024 / 1024
    total_size_gb = total_size / 1024 / 1024 / 1024
    
    print("="*80)
    print("STORAGE STATISTICS")
    print("="*80)
    print(f"\nTotal files: {len(files)}")
    print(f"Total size: {total_size_mb:.1f} MB ({total_size_gb:.2f} GB)")
    print(f"Average file size: {total_size_mb / len(files):.1f} MB")
    
    # Estimate future storage
    daily_avg_mb = total_size_mb / len(files)
    print(f"\nProjected storage needs:")
    print(f"  1 year:  {daily_avg_mb * 365 / 1024:.1f} GB")
    print(f"  3 years: {daily_avg_mb * 365 * 3 / 1024:.1f} GB")
    print(f"  5 years: {daily_avg_mb * 365 * 5 / 1024:.1f} GB")
    print(f"  10 years: {daily_avg_mb * 365 * 10 / 1024:.1f} GB")
    
    # Check disk space
    import shutil
    disk = shutil.disk_usage(storage_dir)
    free_gb = disk.free / 1024 / 1024 / 1024
    
    print(f"\nDisk space:")
    print(f"  Free: {free_gb:.1f} GB")
    print(f"  Can store approx {free_gb / (daily_avg_mb * 365 / 1024):.0f} more years of data")

def main():
    parser = argparse.ArgumentParser(description='Tick Data Storage Manager')
    parser.add_argument('--estimate', action='store_true', help='Estimate storage requirements')
    parser.add_argument('--fetch-today', action='store_true', help='Fetch and store today\'s data')
    parser.add_argument('--fetch-yesterday', action='store_true', help='Fetch and store yesterday\'s data')
    parser.add_argument('--fetch-date', type=str, metavar='YYYY-MM-DD', help='Fetch specific date')
    parser.add_argument('--fetch-history', type=int, metavar='DAYS', help='Fetch last N days')
    parser.add_argument('--list', action='store_true', help='List all stored tick data')
    parser.add_argument('--query', action='store_true', help='Interactive query tool')
    parser.add_argument('--load-range', nargs=2, metavar=('FROM', 'TO'), help='Load date range (YYYY-MM-DD)')
    parser.add_argument('--load-all', action='store_true', help='Load all available tick data')
    parser.add_argument('--stats', action='store_true', help='Show storage statistics')
    parser.add_argument('--create-scheduler', action='store_true', help='Create scheduler scripts')
    
    args = parser.parse_args()
    
    if args.estimate:
        estimate_storage()
    elif args.fetch_today:
        fetch_and_store_today()
    elif args.fetch_yesterday:
        fetch_and_store_yesterday()
    elif args.fetch_date:
        try:
            date = datetime.strptime(args.fetch_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            fetch_and_store_date(date)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
    elif args.fetch_history:
        fetch_historical(args.fetch_history)
    elif args.list:
        list_stored_data()
    elif args.query:
        query_tick_data()
    elif args.load_range:
        try:
            from_date = datetime.strptime(args.load_range[0], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            to_date = datetime.strptime(args.load_range[1], '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
            df = load_ticks_for_range(from_date, to_date)
            print(f"\nData loaded into variable 'df' with {len(df):,} rows")
            print(df.head())
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
    elif args.load_all:
        df = load_all_ticks()
        print(f"\nData loaded into variable 'df' with {len(df):,} rows")
    elif args.stats:
        show_storage_stats()
    elif args.create_scheduler:
        create_scheduler_script()
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python tick_storage_manager.py --estimate")
        print("  python tick_storage_manager.py --fetch-today")
        print("  python tick_storage_manager.py --fetch-history 7")
        print("  python tick_storage_manager.py --load-range 2026-03-10 2026-03-16")
        print("  python tick_storage_manager.py --load-all")
        print("  python tick_storage_manager.py --query")

if __name__ == "__main__":
    main()
