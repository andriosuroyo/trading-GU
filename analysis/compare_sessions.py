"""Compare Asia vs New York session for TP optimization"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timezone

def load_env():
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
    env_vars = load_env()
    terminal_path = env_vars.get("MT5_TERMINAL_VANTAGE")
    if not mt5.initialize(path=terminal_path):
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    return True

def get_m1_bars(from_time, to_time):
    rates = mt5.copy_rates_range('XAUUSD+', mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def fetch_positions(date_from, date_to):
    """Fetch positions from MT5"""
    import gu_tools
    positions = gu_tools.fetch_positions(date_from, date_to)
    return positions

def parse_magic(magic):
    m = str(int(magic))
    if not m.startswith('282603'): 
        return 'UNKNOWN', 'UNKNOWN'
    strat_id = m[6] if len(m) > 6 else '0'
    session_id = m[7] if len(m) > 7 else '0'
    
    strategies = {'0': 'TESTS', '1': 'MH', '2': 'HR05', '3': 'HR10'}
    sessions = {'1': 'ASIA', '2': 'LONDON', '3': 'NY', '0': 'FULL'}
    
    return strategies.get(strat_id, f'STRAT_{strat_id}'), sessions.get(session_id, f'SESS_{session_id}')

def get_session_positions(session_name, date_from, date_to):
    """Get first positions for a specific session"""
    import gu_tools
    positions = gu_tools.fetch_positions(date_from, date_to)
    
    # Filter for GU magics
    gu_positions = [p for p in positions if str(p['magic']).startswith('282603')]
    
    # Parse and filter by session
    session_positions = []
    for p in gu_positions:
        strat, sess = parse_magic(p['magic'])
        if sess == session_name:
            p['strategy'] = strat
            p['session'] = sess
            session_positions.append(p)
    
    # Group into baskets (within 60 seconds)
    sorted_pos = sorted(session_positions, key=lambda x: (x['magic'], x['open_time']))
    
    baskets = []
    current_basket = None
    
    for p in sorted_pos:
        if current_basket is None or p['magic'] != current_basket['magic']:
            current_basket = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
            baskets.append(current_basket)
        else:
            first_time = current_basket['positions'][0]['open_time']
            if (p['open_time'] - first_time).total_seconds() <= 60:
                current_basket['positions'].append(p)
            else:
                current_basket = {'magic': p['magic'], 'strategy': p['strategy'], 'positions': [p]}
                baskets.append(current_basket)
    
    # Get first positions only, exclude glitch baskets (simultaneous BUY/SELL)
    first_positions = []
    for basket in baskets:
        first_pos = basket['positions'][0]
        
        # Check for glitch (simultaneous BUY/SELL)
        is_glitch = False
        if len(basket['positions']) >= 2:
            directions = [p['direction'] for p in basket['positions']]
            if 'BUY' in directions and 'SELL' in directions:
                times = [p['open_time'] for p in basket['positions']]
                if len(set(times)) < len(times):
                    is_glitch = True
        
        if not is_glitch:
            first_positions.append({
                'time': first_pos['open_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'type': first_pos['direction'],
                'entry': first_pos['open_price'],
                'actual_pl': first_pos['net_pl']
            })
    
    return first_positions

def find_tp_hit(position, df_m1, tp_points):
    entry_time = pd.to_datetime(position['time'])
    entry_price = position['entry']
    pos_type = position['type']
    
    if pos_type == 'BUY':
        tp_price = entry_price + tp_points * 0.01
    else:
        tp_price = entry_price - tp_points * 0.01
    
    future_candles = df_m1[df_m1['time'] >= entry_time].head(30)
    
    for i, (_, candle) in enumerate(future_candles.iterrows()):
        if pos_type == 'BUY':
            if candle['high'] >= tp_price:
                return i
        else:
            if candle['low'] <= tp_price:
                return i
    return None

def get_exit_pnl(position, df_m1, cutoff_candles):
    entry_time = pd.to_datetime(position['time'])
    entry_price = position['entry']
    pos_type = position['type']
    
    future_candles = df_m1[df_m1['time'] >= entry_time].head(cutoff_candles + 1)
    
    if len(future_candles) < cutoff_candles + 1:
        return None
    
    exit_price = future_candles.iloc[cutoff_candles]['close']
    
    if pos_type == 'BUY':
        return (exit_price - entry_price) * 100 * 0.01
    else:
        return (entry_price - exit_price) * 100 * 0.01

def simulate_session(positions, tp_points, cutoff_candles, cache):
    tp_hits = 0
    misses = 0
    total_pnl = 0.0
    sum_miss_pnl = 0.0
    
    for pos in positions:
        pos_time = pd.to_datetime(pos['time'])
        cache_key = pos['time'][:10]
        
        if cache_key not in cache:
            start_time = pos_time - pd.Timedelta(hours=2)
            end_time = pos_time + pd.Timedelta(hours=6)
            cache[cache_key] = get_m1_bars(start_time, end_time)
        
        df_m1 = cache[cache_key]
        if df_m1 is None or df_m1.empty:
            continue
        
        hit_candle = find_tp_hit(pos, df_m1, tp_points)
        
        if hit_candle is not None and hit_candle < cutoff_candles:
            tp_hits += 1
            total_pnl += tp_points * 0.01
        else:
            exit_pnl = get_exit_pnl(pos, df_m1, cutoff_candles)
            if exit_pnl is not None:
                misses += 1
                sum_miss_pnl += exit_pnl
                total_pnl += exit_pnl
    
    actual_pl = sum(p['actual_pl'] for p in positions)
    
    return {
        'tp_points': tp_points,
        'tp_hits': tp_hits,
        'misses': misses,
        'win_rate': tp_hits / (tp_hits + misses) * 100 if (tp_hits + misses) > 0 else 0,
        'tp_pnl': tp_hits * tp_points * 0.01,
        'miss_pnl': sum_miss_pnl,
        'total_pnl': total_pnl,
        'avg_miss_pnl': sum_miss_pnl / misses if misses > 0 else 0,
        'actual_pl': actual_pl
    }

def main():
    import gu_tools
    if not connect_mt5():
        return
    
    try:
        date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
        date_to = datetime.now(timezone.utc)
        
        print("Fetching Asia session positions...")
        asia_positions = get_session_positions('ASIA', date_from, date_to)
        
        print("Fetching NY session positions...")
        ny_positions = get_session_positions('NY', date_from, date_to)
        
        print(f"\nAsia positions: {len(asia_positions)}")
        print(f"NY positions: {len(ny_positions)}")
        
        # Simulate for both sessions
        cache = {}
        cutoff = 5
        tp_levels = [70, 80, 90, 100, 110, 120, 150, 200]
        
        print("\n" + "="*110)
        print(f"COMPARISON: ASIA vs NY SESSION (5-Minute Cutoff)")
        print("="*110)
        
        print(f"\n{'TP':<8} {'Asia Hits':<10} {'Asia Miss':<10} {'Asia Win%':<10} {'Asia P&L':<12} {'NY Hits':<10} {'NY Miss':<10} {'NY Win%':<10} {'NY P&L':<12} {'Diff':<10}")
        print("-"*110)
        
        for tp in tp_levels:
            asia_result = simulate_session(asia_positions, tp, cutoff, cache)
            ny_result = simulate_session(ny_positions, tp, cutoff, cache)
            
            diff = ny_result['total_pnl'] - asia_result['total_pnl']
            
            print(f"{tp:<8} {asia_result['tp_hits']:<10} {asia_result['misses']:<10} {asia_result['win_rate']:<10.1f} ${asia_result['total_pnl']:<11.2f} {ny_result['tp_hits']:<10} {ny_result['misses']:<10} {ny_result['win_rate']:<10.1f} ${ny_result['total_pnl']:<11.2f} {'+' if diff >= 0 else ''}{diff:.2f}")
        
        # Best for each session
        asia_results = [simulate_session(asia_positions, tp, cutoff, cache) for tp in range(30, 310, 10)]
        ny_results = [simulate_session(ny_positions, tp, cutoff, cache) for tp in range(30, 310, 10)]
        
        asia_best = max(asia_results, key=lambda x: x['total_pnl'])
        ny_best = max(ny_results, key=lambda x: x['total_pnl'])
        
        print("\n" + "="*110)
        print("BEST CONFIGURATION BY SESSION:")
        print("="*110)
        
        print(f"\nASIA SESSION:")
        print(f"  Best TP: {asia_best['tp_points']} points (${asia_best['tp_points']*0.01:.2f})")
        print(f"  Win Rate: {asia_best['win_rate']:.1f}% ({asia_best['tp_hits']}/{asia_best['tp_hits']+asia_best['misses']})")
        print(f"  Simulated P&L: ${asia_best['total_pnl']:.2f}")
        print(f"  Actual P&L: ${asia_best['actual_pl']:.2f}")
        print(f"  Improvement: +{asia_best['total_pnl'] - asia_best['actual_pl']:.2f}")
        
        print(f"\nNEW YORK SESSION:")
        print(f"  Best TP: {ny_best['tp_points']} points (${ny_best['tp_points']*0.01:.2f})")
        print(f"  Win Rate: {ny_best['win_rate']:.1f}% ({ny_best['tp_hits']}/{ny_best['tp_hits']+ny_best['misses']})")
        print(f"  Simulated P&L: ${ny_best['total_pnl']:.2f}")
        print(f"  Actual P&L: ${ny_best['actual_pl']:.2f}")
        print(f"  Improvement: +{ny_best['total_pnl'] - ny_best['actual_pl']:.2f}")
        
        print("\n" + "="*110)
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
