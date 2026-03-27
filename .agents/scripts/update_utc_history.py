import sys
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

sys.path.append(r'c:\Trading_GU')
sys.path.append(r'c:\Trading_GU\.agents\scripts')
import gu_tools
from history_filters import filter_invalid_trades

def categorize_dst(dt):
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

def determine_session(magic, hour=None):
    m = str(magic)
    if m.startswith('282603'):
        ending = m[-1]
        if ending == '1': return "ASIA"
        if ending == '2': return "LONDON"
        if ending == '3': return "NY"
        
        if hour is not None:
            if 2 <= hour <= 6: return "ASIA"
            if 7 <= hour <= 12: return "LONDON"
            if 15 <= hour <= 22: return "NY"
    return "UNKNOWN"

def update_utc_history():
    history_path = r'c:\Trading_GU\utc_history.csv'
    
    # Load existing if available
    if os.path.exists(history_path):
        df_old = pd.read_csv(history_path)
        # Find latest close_time to optimize MT5 fetch. If empty, fetch all year.
        if not df_old.empty:
            last_date_str = df_old['close_time_utc'].max()
            date_from = datetime.strptime(last_date_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) - timedelta(days=2)
        else:
            date_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
    else:
        df_old = pd.DataFrame()
        date_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
        
    date_to = datetime.now(timezone.utc)
    
    print(f"Connecting to MT5 to fetch positions from {date_from.strftime('%Y-%m-%d')}...")
    if not gu_tools.connect_mt5():
        print("Failed to connect to MT5.")
        return
        
    positions = gu_tools.fetch_positions(date_from, date_to)
    gu_tools.mt5.shutdown()
    
    if not positions:
        print("No new closed positions found in the specified window.")
        return
        
    df_new = pd.DataFrame(positions)
    
    # Filter for ONLY GU trades (Magic 282603xx)
    df_new = df_new[df_new['magic'].astype(str).str.startswith('282603')].copy()
    
    if df_new.empty:
        print("No new GU closed positions found in the specified window.")
        return
        
    # Format exactly as UTC
    df_new['open_time_utc'] = df_new['open_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_new['close_time_utc'] = df_new['close_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_new['open_hour_utc'] = df_new['open_time'].dt.hour
    
    # Add contextual columns
    states = df_new['open_time'].apply(categorize_dst)
    df_new['dst_state'] = [x[0] for x in states]
    df_new['ny_intended_setting'] = [x[1] for x in states]
    
    df_new['session'] = df_new.apply(lambda row: determine_session(row['magic'], row['open_hour_utc']), axis=1)
    
    cols = [
        'pos_id', 'magic', 'session', 'symbol', 'direction', 'volume', 
        'open_time_utc', 'open_hour_utc', 'close_time_utc', 
        'open_price', 'close_price', 'profit',
        'dst_state', 'ny_intended_setting'
    ]
    df_new = df_new[cols]
    
    if not df_old.empty:
        # Merge old and new
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        # Drop duplicates based on pos_id. Keep the last one which is usually the most updated.
        df_combined = df_combined.drop_duplicates(subset=['pos_id'], keep='last')
        
        # In case old file had non-GU trades, filter them out again just to be safe
        df_combined = df_combined[df_combined['magic'].astype(str).str.startswith('282603')]
    else:
        df_combined = df_new
        
    # Sort chronologically by open time
    df_combined.sort_values('open_time_utc', inplace=True)
    
    # Filter Invalid Trades using the shared module
    df_combined = filter_invalid_trades(df_combined)
    
    df_combined.to_csv(history_path, index=False)
    print(f"Successfully updated '{history_path}'. Total unique clean GU positions: {len(df_combined)}")

if __name__ == "__main__":
    update_utc_history()
