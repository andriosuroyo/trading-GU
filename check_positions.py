import sys
sys.path.append('data')
from fetch_all_gu_positions import fetch_all_positions, connect_mt5
from datetime import datetime, date, timezone, timedelta
import MetaTrader5 as mt5

if connect_mt5('MT5_TERMINAL_VANTAGE'):
    date_from = datetime.combine(date(2026, 3, 23), datetime.min.time(), tzinfo=timezone.utc)
    date_to = date_from + timedelta(days=1)
    positions = fetch_all_positions(date_from, date_to)
    
    gu_positions = [p for p in positions if p.get('is_gu')]
    print(f'Total GU positions: {len(gu_positions)}')
    print('\nFirst 5 positions:')
    for p in gu_positions[:5]:
        print(f"  ID: {p['pos_id']}, Open: {p['open_time']}, Magic: {p['magic']}")
    
    mt5.shutdown()
