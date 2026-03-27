"""Quick check of tick data availability"""
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

env_vars = load_env()
terminal_path = env_vars.get('MT5_TERMINAL_VANTAGE')
mt5.initialize(path=terminal_path)

print('TICK DATA SOURCE CHECK - VANTAGE')
print('=' * 70)

# Check each date
dates = ['20260313', '20260316', '20260317', '20260318', '20260319', '20260320']

for date_str in dates:
    date = datetime.strptime(date_str, '%Y%m%d').replace(tzinfo=timezone.utc)
    day_start = date.replace(hour=0, minute=0, second=0)
    day_end = day_start + timedelta(days=1)
    
    ticks = mt5.copy_ticks_range('XAUUSD+', day_start, day_end, mt5.COPY_TICKS_ALL)
    
    # Load local
    local_file = f'tick_data/ticks_{date_str}.parquet'
    if os.path.exists(local_file):
        df = pd.read_parquet(local_file)
        local_count = len(df)
    else:
        local_count = 0
    
    if ticks is not None and len(ticks) > 0:
        source_count = len(ticks)
        first = datetime.fromtimestamp(ticks[0][0], tz=timezone.utc)
        last = datetime.fromtimestamp(ticks[-1][0], tz=timezone.utc)
        diff = source_count - local_count
        
        status = "OK" if abs(diff) < 1000 else "MISMATCH"
        print(f'{date_str}: Source={source_count:,} | Local={local_count:,} | Diff={diff:+,} | {status}')
        print(f'       Time range: {first.strftime("%H:%M")} to {last.strftime("%H:%M")} UTC')
    else:
        print(f'{date_str}: Source=NOT AVAILABLE | Local={local_count:,} | KEEP LOCAL')

mt5.shutdown()
