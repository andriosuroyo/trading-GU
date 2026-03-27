import sys
import os
import pandas as pd
from datetime import datetime, timezone

sys.path.append(r'c:\Trading_GU')
import gu_tools

def categorize_dst(dt):
    """
    Returns the DST state and the NY active settings based on the timeline.
    dt must be a UTC datetime object.
    
    Returns: (DST_State, NY_Setting)
    """
    # 2026 boundaries
    # US EDT begins: Mar 8
    # UK BST begins: Mar 29
    # UK BST ends: Oct 25
    # US EDT ends: Nov 1
    
    if dt < datetime(2026, 3, 8, tzinfo=timezone.utc):
        return "Winter_Baseline", "17-22"
    elif dt < datetime(2026, 3, 29, tzinfo=timezone.utc):
        return "US_EDT_Only", "17-21"
    elif dt < datetime(2026, 10, 25, tzinfo=timezone.utc):
        return "US_EDT_UK_BST", "16-21"
    elif dt < datetime(2026, 11, 1, tzinfo=timezone.utc):
        return "US_EDT_Only", "17-21"
    else:
        return "Winter_Baseline", "17-22"

def filter_invalid_trades(df):
    if df.empty: return df
    initial_count = len(df)
    
    # 1. Glitches (Simultaneous BUY/SELL)
    df['open_time_sec'] = df['open_time_utc']
    glitch_groups = df.groupby(['magic', 'open_time_sec'])['direction'].nunique()
    glitched = glitch_groups[glitch_groups > 1].reset_index()
    if not glitched.empty:
        # Create a set of (magic, open_time_sec) tuples to drop
        drop_tuples = set(zip(glitched['magic'], glitched['open_time_sec']))
        df = df[~df[['magic', 'open_time_sec']].apply(tuple, axis=1).isin(drop_tuples)]
        
    # 2. Unmanaged carry-over trades
    def is_carried(row):
        sess = row['session']
        if sess == 'UNKNOWN': return False
        
        close_hr = pd.to_datetime(row['close_time_utc']).hour
        if sess == 'ASIA':
            if close_hr >= 6: return True
        elif sess == 'LONDON':
            if close_hr >= 12: return True
        elif sess == 'NY':
            end_hr = 22 if row['ny_intended_setting'] == '17-22' else 21
            if close_hr >= end_hr: return True
        return False
        
    mask = df.apply(is_carried, axis=1)
    df = df[~mask]
    
    dropped = initial_count - len(df)
    if dropped > 0:
        print(f"Filtered {dropped} invalid glitch/unmanaged trades from history.")
    
    return df.drop(columns=['open_time_sec'])

def export_utc_history():
    if not gu_tools.connect_mt5():
        print("Failed to connect to MT5.")
        return

    # We want ALL history. Let's pull from Jan 1 2026 to present.
    date_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
    date_to = datetime.now(timezone.utc)
    
    positions = gu_tools.fetch_positions(date_from, date_to)
    
    if not positions:
        print("No positions found.")
        gu_tools.mt5.shutdown()
        return
        
    df = pd.DataFrame(positions)
    
    # 1. Standardize Timestamps
    # 'open_time' and 'close_time' from gu_tools are already UTC datetime objects
    # Let's enforce the display format so there's zero ambiguity
    
    # Extract UTC features for analysis
    df['open_time_utc'] = df['open_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['close_time_utc'] = df['close_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['open_hour_utc'] = df['open_time'].dt.hour
    
    # 2. Add Contextual Tags
    states = df['open_time'].apply(categorize_dst)
    df['dst_state'] = [x[0] for x in states]
    df['ny_intended_setting'] = [x[1] for x in states]
    
    # We can also add a session tag based on magic (if it's a standard GU magic)
    def determine_session(magic):
        m = str(magic)
        if m.startswith('282603'):
            ending = m[-1]
            if ending == '1': return "ASIA"
            if ending == '2': return "LONDON"
            if ending == '3': return "NY"
            # Some tests use 0 or 5 or 6, let's just mark them by time if we don't know
            if 2 <= df['open_hour_utc'][df['magic'] == magic].iloc[0] <= 6: return "ASIA"
            if 7 <= df['open_hour_utc'][df['magic'] == magic].iloc[0] <= 12: return "LONDON"
            if 15 <= df['open_hour_utc'][df['magic'] == magic].iloc[0] <= 22: return "NY"
        return "UNKNOWN"
    
    df['session'] = df['magic'].apply(determine_session)
    
    # Cleanup and reorder columns
    cols = [
        'pos_id', 'magic', 'session', 'symbol', 'direction', 'volume', 
        'open_time_utc', 'open_hour_utc', 'close_time_utc', 
        'open_price', 'close_price', 'profit',
        'dst_state', 'ny_intended_setting'
    ]
    df = df[cols]
    
    # Filter Invalid Trades
    df = filter_invalid_trades(df)
    
    # Save to CSV
    export_path = r'c:\Trading_GU\utc_history.csv'
    df.to_csv(export_path, index=False)
    
    print(f"Successfully exported {len(df)} positions to {export_path}")
    print("All timestamps are rigidly set in absolute UTC+0.")
    print("Added contextual columns: dst_state, ny_intended_setting")
    
    gu_tools.mt5.shutdown()

if __name__ == "__main__":
    export_utc_history()
