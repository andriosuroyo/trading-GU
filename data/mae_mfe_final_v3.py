"""Final MAE/MFE Analysis - Exact Format"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import json

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
    terminal_path = env_vars.get('MT5_TERMINAL_BLACKBULL')
    if not mt5.initialize(path=terminal_path):
        return False
    return True

def get_atr_m1_60(symbol, target_time):
    from_time = target_time - timedelta(hours=2)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, target_time)
    if rates is None or len(rates) < 60:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr_60'] = df['tr'].rolling(window=60).mean()
    df_before = df[df['time'] <= target_time]
    if df_before.empty:
        return None
    return df_before['atr_60'].iloc[-1]

def get_tick_data_blackbull(from_time, to_time):
    ticks = mt5.copy_ticks_range('XAUUSDp', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

print("=" * 70)
print("MAE/MFE FINAL ANALYSIS - Exact Format")
print("=" * 70)

with open('data/gu_positions_vantage.json', 'r') as f:
    data = json.load(f)

target_positions = [p for p in data['closed_positions'] if str(p['magic']) in ['20', '30'] and '2026-03-20' in p['open_time']]
print(f"Found {len(target_positions)} Magic 20/30 positions on March 20")

if not connect_blackbull():
    print("Failed to connect")
    exit(1)

results = []
for i, pos in enumerate(target_positions):
    pos_id = pos['pos_id']
    direction = pos['direction']
    entry_price = pos['open_price']
    exit_price = pos['close_price']
    magic = pos['magic']
    open_time = datetime.fromisoformat(pos['open_time'])
    close_time = datetime.fromisoformat(pos['close_time'])
    window_15min_end = open_time + timedelta(minutes=15)
    
    atr_value = get_atr_m1_60('XAUUSDp', open_time)
    if atr_value is None:
        atr_value = 0
    atr_tp_points = round(atr_value * 0.5 * 100)
    
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_15min_end + timedelta(seconds=5)
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None:
        continue
    
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_15min_end)]
    if window_ticks.empty:
        continue
    
    if direction == 'BUY':
        mfe15_price = window_ticks['ask'].max()
        mfe15_points = round(abs((mfe15_price - entry_price) * 100))
        mae15_price = window_ticks['bid'].min()
        mae15_points = round(abs((entry_price - mae15_price) * 100))
        actual_points = round((exit_price - entry_price) * 100)
        ticks_at_15min = window_ticks[window_ticks['time'] <= window_15min_end]
        price_15min = ticks_at_15min['bid'].iloc[-1] if not ticks_at_15min.empty else exit_price
        points_15min_close = round((price_15min - entry_price) * 100)
    else:
        mfe15_price = window_ticks['bid'].min()
        mfe15_points = round(abs((entry_price - mfe15_price) * 100))
        mae15_price = window_ticks['ask'].max()
        mae15_points = round(abs((mae15_price - entry_price) * 100))
        actual_points = round((entry_price - exit_price) * 100)
        ticks_at_15min = window_ticks[window_ticks['time'] <= window_15min_end]
        price_15min = ticks_at_15min['ask'].iloc[-1] if not ticks_at_15min.empty else exit_price
        points_15min_close = round((entry_price - price_15min) * 100)
    
    if mfe15_points > atr_tp_points:
        outcome = 'PROFIT'
        outcome_points = atr_tp_points
    else:
        outcome = 'LOSS'
        outcome_points = points_15min_close
    
    results.append({
        'Ticket': f'P{pos_id}',
        'Magic Number': magic,
        'Type': direction,
        'TimeOpen': open_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceOpen': entry_price,
        'TimeClose': close_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceClose': exit_price,
        'ActualPoints': actual_points,
        'ATROpen': round(atr_value, 2),
        'ATRTP': atr_tp_points,
        'MFE15Price': round(mfe15_price, 2),
        'MFE15Points': mfe15_points,
        'MAE15Price': round(mae15_price, 2),
        'MAE15Points': mae15_points,
        'Outcome': outcome,
        'OutcomePoints': outcome_points
    })

mt5.shutdown()

df = pd.DataFrame(results)
output_file = 'data/mae_mfe_march20_v2.csv'
df.to_csv(output_file, index=False)

print(f"\nCSV saved: {output_file}")
print(f"Columns ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

print(f"\nTotal positions: {len(df)}")
print(f"PROFIT: {(df['Outcome']=='PROFIT').sum()}")
print(f"LOSS: {(df['Outcome']=='LOSS').sum()}")

print("\nFirst 5 rows:")
print(df.head(5).to_string(index=False))
