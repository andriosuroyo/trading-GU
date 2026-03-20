"""Detailed analysis of TP 80 for Asia session"""

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

def analyze_tp80(positions, cutoff, cache):
    tp_points = 80
    
    hits = []
    misses = []
    
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
            hits.append({
                'time': pos['time'],
                'type': pos_type,
                'entry': entry_price,
                'hit_candle': hit_candle,
                'actual_pl': pos['actual_pl']
            })
        else:
            # Miss - get exit P&L at cutoff
            if len(future_candles) > cutoff:
                exit_price = future_candles.iloc[cutoff]['close']
                if pos_type == 'BUY':
                    exit_pnl = (exit_price - entry_price) * 100 * 0.01
                else:
                    exit_pnl = (entry_price - exit_price) * 100 * 0.01
                
                misses.append({
                    'time': pos['time'],
                    'type': pos_type,
                    'entry': entry_price,
                    'exit_pnl': exit_pnl,
                    'actual_pl': pos['actual_pl']
                })
    
    return hits, misses

def main():
    if not connect_mt5():
        return
    
    try:
        date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
        date_to = datetime.now(timezone.utc)
        
        asia_positions = get_session_positions('ASIA', date_from, date_to)
        ny_positions = get_session_positions('NY', date_from, date_to)
        
        cache = {}
        cutoff = 5
        
        print("="*100)
        print("TP 80 ANALYSIS - ASIA vs NY SESSION (5-Minute Cutoff)")
        print("="*100)
        
        # Asia
        asia_hits, asia_misses = analyze_tp80(asia_positions, cutoff, cache)
        asia_tp_pnl = len(asia_hits) * 0.80
        asia_miss_pnl = sum(m['exit_pnl'] for m in asia_misses)
        asia_total = asia_tp_pnl + asia_miss_pnl
        asia_actual = sum(p['actual_pl'] for p in asia_positions)
        
        print(f"\nASIA SESSION (62 positions):")
        print("-"*100)
        print(f"  TP Hits:   {len(asia_hits)}/62 ({len(asia_hits)/62*100:.1f}%)")
        print(f"  Misses:    {len(asia_misses)}/62 ({len(asia_misses)/62*100:.1f}%)")
        print(f"  TP Profit: ${asia_tp_pnl:.2f}")
        print(f"  Miss Loss: ${asia_miss_pnl:.2f}")
        print(f"  NET P&L:   ${asia_total:.2f}")
        print(f"  Actual:    ${asia_actual:.2f}")
        print(f"  vs Actual: {asia_total - asia_actual:+.2f}")
        
        # NY
        ny_hits, ny_misses = analyze_tp80(ny_positions, cutoff, cache)
        ny_tp_pnl = len(ny_hits) * 0.80
        ny_miss_pnl = sum(m['exit_pnl'] for m in ny_misses)
        ny_total = ny_tp_pnl + ny_miss_pnl
        ny_actual = sum(p['actual_pl'] for p in ny_positions)
        
        print(f"\nNY SESSION (115 positions):")
        print("-"*100)
        print(f"  TP Hits:   {len(ny_hits)}/115 ({len(ny_hits)/115*100:.1f}%)")
        print(f"  Misses:    {len(ny_misses)}/115 ({len(ny_misses)/115*100:.1f}%)")
        print(f"  TP Profit: ${ny_tp_pnl:.2f}")
        print(f"  Miss Loss: ${ny_miss_pnl:.2f}")
        print(f"  NET P&L:   ${ny_total:.2f}")
        print(f"  Actual:    ${ny_actual:.2f}")
        print(f"  vs Actual: {ny_total - ny_actual:+.2f}")
        
        print("\n" + "="*100)
        print("TP 80 SUMMARY:")
        print("="*100)
        print(f"\n  Asia: ${asia_total:.2f} (Win rate: {len(asia_hits)/62*100:.1f}%)")
        print(f"  NY:   ${ny_total:.2f} (Win rate: {len(ny_hits)/115*100:.1f}%)")
        print(f"\n  Difference: NY ${ny_total - asia_total:.2f} better than Asia")
        
        # Best TP for comparison
        print("\n" + "="*100)
        print("OPTIMAL TP BY SESSION (from earlier simulation):")
        print("="*100)
        print(f"\n  Asia Best: TP 110 ($1.10) = $24.22")
        print(f"  NY Best:   TP 250 ($2.50) = $38.51")
        print(f"\n  Recommendation:")
        print(f"    - Asia: TP 80-110 points ($0.80-$1.10) works well")
        print(f"    - NY:   TP 200-250 points ($2.00-$2.50) for faster moves")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
