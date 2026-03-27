import pandas as pd

def filter_invalid_trades(df):
    """
    Applies user-defined filters to remove 'gambling' or 'glitch' trades.
    """
    if df.empty: return df

    initial_count = len(df)
    
    # 1. Filter out parameter-change glitches: 
    # Simultaneous BUY/SELL with the exact same magic number and open time.
    # Group by magic and open_time_utc, count unique directions.
    df['open_time_sec'] = df['open_time_utc']
    
    # Find combinations of magic + open_time_sec that have Both BUY and SELL
    glitch_groups = df.groupby(['magic', 'open_time_sec'])['direction'].nunique()
    glitched = glitch_groups[glitch_groups > 1].index
    
    # Drop rows that are in the glitched index
    df = df.set_index(['magic', 'open_time_sec'])
    df = df.drop(index=glitched)
    df = df.reset_index()
    
    # 2. Filter out unmanaged carry-over trades.
    # The EA stops managing TP/Trail when the trading window closes. 
    # Any trade that closes significantly after the window ends is subject to gambling (only hard SL works).
    # Since we can't perfectly know EA internal tick processing, we will drop any trade whose close_time 
    # strictly exceeds the EndHour of its session.
    
    def is_carried_over(row):
        sess = row['session']
        if sess == 'UNKNOWN': return False # We don't know the window
        
        close_hr = pd.to_datetime(row['close_time_utc']).hour
        open_hr = row['open_hour_utc']
        
        # If ASIA (02-06), window closes at 06:00. 
        # So if close hour is >= 6, it might be carried over. 
        # Let's say if close hour > 6, it's definitely carried over.
        # Actually EA stops at EndHour. So ASIA EndHour=6 means at 06:00:00 it stops.
        
        if sess == 'ASIA':
            if close_hr >= 6: return True
        elif sess == 'LONDON':
            if close_hr >= 12: return True
        elif sess == 'NY':
            # NY end hour depends on DST state
            end_hr = 22 if row['ny_intended_setting'] == '17-22' else 21
            if close_hr >= end_hr: return True
            
        return False
        
    mask = df.apply(is_carried_over, axis=1)
    df = df[~mask]
    
    final_count = len(df)
    dropped = initial_count - final_count
    if dropped > 0:
        print(f"Filtered {dropped} invalid glitch/unmanaged trades from history.")
    
    return df.drop(columns=['open_time_sec'])
