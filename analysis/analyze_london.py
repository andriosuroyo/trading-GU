"""Analyze London session and compare all three sessions"""

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
        return False
    return True

def get_m1_bars(from_time, to_time):
    rates = mt5.copy_rates_range('XAUUSD+', mt5.TIMEFRAME_M1, from_time, to_time)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

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
    import gu_tools
    positions = gu_tools.fetch_positions(date_from, date_to)
    gu_positions = [p for p in positions if str(p['magic']).startswith('282603')]
    
    session_positions = []
    for p in gu_positions:
        strat, sess = parse_magic(p['magic'])
        if sess == session_name:
            p['strategy'] = strat
            p['session'] = sess
            session_positions.append(p)
    
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
    
    first_positions = []
    for basket in baskets:
        first_pos = basket['positions'][0]
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

def simulate_tp(positions, tp_points, cutoff, cache):
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
        
        entry_price = pos['entry']
        pos_type = pos['type']
        
        if pos_type == 'BUY':
            tp_price = entry_price + tp_points * 0.01
        else:
            tp_price = entry_price - tp_points * 0.01
        
        future_candles = df_m1[df_m1['time'] >= pos_time].head(cutoff + 1)
        
        tp_hit = False
        hit_candle = None
        
        for i, (_, candle) in enumerate(future_candles.iterrows()):
            if pos_type == 'BUY':
                if candle['high'] >= tp_price:
                    tp_hit = True
                    hit_candle = i
                    break
            else:
                if candle['low'] <= tp_price:
                    tp_hit = True
                    hit_candle = i
                    break
        
        if tp_hit and hit_candle < cutoff:
            tp_hits += 1
            total_pnl += tp_points * 0.01
        else:
            if len(future_candles) > cutoff:
                exit_price = future_candles.iloc[cutoff]['close']
                if pos_type == 'BUY':
                    exit_pnl = (exit_price - entry_price) * 100 * 0.01
                else:
                    exit_pnl = (entry_price - exit_price) * 100 * 0.01
                
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
        'actual_pl': actual_pl
    }

def main():
    if not connect_mt5():
        return
    
    try:
        date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
        date_to = datetime.now(timezone.utc)
        
        print("Fetching positions...")
        asia_positions = get_session_positions('ASIA', date_from, date_to)
        london_positions = get_session_positions('LONDON', date_from, date_to)
        ny_positions = get_session_positions('NY', date_from, date_to)
        
        print(f"\nAsia positions: {len(asia_positions)}")
        print(f"London positions: {len(london_positions)}")
        print(f"NY positions: {len(ny_positions)}")
        
        cache = {}
        cutoff = 5
        
        # Test various TPs
        tp_levels = [50, 60, 70, 80, 90, 100, 110, 120, 150, 200, 250, 300]
        
        print("\n" + "="*120)
        print(f"ALL SESSIONS COMPARISON (5-Minute Cutoff)")
        print("="*120)
        
        print(f"\n{'TP':<8} {'Asia Win%':<12} {'Asia P&L':<12} {'London Win%':<14} {'London P&L':<14} {'NY Win%':<12} {'NY P&L':<12}")
        print("-"*120)
        
        results = {'asia': [], 'london': [], 'ny': []}
        
        for tp in tp_levels:
            asia_r = simulate_tp(asia_positions, tp, cutoff, cache)
            london_r = simulate_tp(london_positions, tp, cutoff, cache)
            ny_r = simulate_tp(ny_positions, tp, cutoff, cache)
            
            results['asia'].append(asia_r)
            results['london'].append(london_r)
            results['ny'].append(ny_r)
            
            print(f"{tp:<8} {asia_r['win_rate']:<12.1f} ${asia_r['total_pnl']:<11.2f} {london_r['win_rate']:<14.1f} ${london_r['total_pnl']:<13.2f} {ny_r['win_rate']:<12.1f} ${ny_r['total_pnl']:<11.2f}")
        
        # Find best for each
        asia_best = max(results['asia'], key=lambda x: x['total_pnl'])
        london_best = max(results['london'], key=lambda x: x['total_pnl'])
        ny_best = max(results['ny'], key=lambda x: x['total_pnl'])
        
        print("\n" + "="*120)
        print("OPTIMAL TP BY SESSION:")
        print("="*120)
        
        print(f"\n{'Session':<12} {'Best TP':<10} {'Win Rate':<12} {'Sim P&L':<12} {'Actual P&L':<14} {'Positions':<12}")
        print("-"*120)
        print(f"{'Asia':<12} {asia_best['tp_points']:<10} {asia_best['win_rate']:<12.1f} ${asia_best['total_pnl']:<11.2f} ${asia_best['actual_pl']:<13.2f} {len(asia_positions):<12}")
        print(f"{'London':<12} {london_best['tp_points']:<10} {london_best['win_rate']:<12.1f} ${london_best['total_pnl']:<11.2f} ${london_best['actual_pl']:<13.2f} {len(london_positions):<12}")
        print(f"{'New York':<12} {ny_best['tp_points']:<10} {ny_best['win_rate']:<12.1f} ${ny_best['total_pnl']:<11.2f} ${ny_best['actual_pl']:<13.2f} {len(ny_positions):<12}")
        
        # Get TP 80 data for London specifically
        london_tp80 = [r for r in results['london'] if r['tp_points'] == 80][0]
        
        print("\n" + "="*120)
        print("TP 80 PERFORMANCE (For Comparison):")
        print("="*120)
        print(f"\n{'Session':<12} {'Win Rate':<12} {'Net P&L':<12}")
        print("-"*50)
        asia_tp80 = [r for r in results['asia'] if r['tp_points'] == 80][0]
        ny_tp80 = [r for r in results['ny'] if r['tp_points'] == 80][0]
        print(f"{'Asia':<12} {asia_tp80['win_rate']:<12.1f} ${asia_tp80['total_pnl']:<11.2f}")
        print(f"{'London':<12} {london_tp80['win_rate']:<12.1f} ${london_tp80['total_pnl']:<11.2f}")
        print(f"{'New York':<12} {ny_tp80['win_rate']:<12.1f} ${ny_tp80['total_pnl']:<11.2f}")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
