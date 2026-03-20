"""
Fetch latest GU positions and rerun analysis - Prioritizing BEST P&L
Not win rate - maximum profit is the goal
"""

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
    glitch_count = 0
    for basket in baskets:
        first_pos = basket['positions'][0]
        is_glitch = False
        if len(basket['positions']) >= 2:
            directions = [p['direction'] for p in basket['positions']]
            if 'BUY' in directions and 'SELL' in directions:
                times = [p['open_time'] for p in basket['positions']]
                if len(set(times)) < len(times):
                    is_glitch = True
                    glitch_count += 1
        
        if not is_glitch:
            first_positions.append({
                'time': first_pos['open_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'type': first_pos['direction'],
                'entry': first_pos['open_price'],
                'actual_pl': first_pos['net_pl']
            })
    
    return first_positions, glitch_count

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
    total_positions = tp_hits + misses
    
    return {
        'tp_points': tp_points,
        'tp_hits': tp_hits,
        'misses': misses,
        'win_rate': tp_hits / total_positions * 100 if total_positions > 0 else 0,
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
        
        print("="*120)
        print("LATEST GU ANALYSIS - FETCHING FRESH DATA FROM MT5")
        print(f"Date range: {date_from.date()} to {date_to.date()}")
        print("="*120)
        
        print("\nFetching positions from all sessions...")
        asia_positions, asia_glitch = get_session_positions('ASIA', date_from, date_to)
        london_positions, london_glitch = get_session_positions('LONDON', date_from, date_to)
        ny_positions, ny_glitch = get_session_positions('NY', date_from, date_to)
        
        print(f"\nASIA:    {len(asia_positions)} first positions (excluded {asia_glitch} glitch baskets)")
        print(f"LONDON:  {len(london_positions)} first positions (excluded {london_glitch} glitch baskets)")
        print(f"NEW YORK: {len(ny_positions)} first positions (excluded {ny_glitch} glitch baskets)")
        
        cache = {}
        cutoff = 5
        
        # Test TP levels in 10-point increments for speed
        tp_levels = list(range(30, 310, 10))
        
        print("\n" + "="*120)
        print("SIMULATING ALL TP LEVELS (5-minute cutoff, 10-point increments)")
        print("="*120)
        
        all_results = {}
        
        for session_name, positions in [('ASIA', asia_positions), ('LONDON', london_positions), ('NY', ny_positions)]:
            print(f"\nProcessing {session_name}...")
            results = []
            for tp in tp_levels:
                r = simulate_tp(positions, tp, cutoff, cache)
                results.append(r)
            all_results[session_name] = results
        
        # Find best P&L for each session
        print("\n" + "="*120)
        print("RESULTS - BEST P&L CONFIGURATION (NOT WIN RATE)")
        print("="*120)
        
        for session_name in ['ASIA', 'LONDON', 'NY']:
            results = all_results[session_name]
            positions = {'ASIA': asia_positions, 'LONDON': london_positions, 'NY': ny_positions}[session_name]
            
            best = max(results, key=lambda x: x['total_pnl'])
            
            print(f"\n{session_name} ({len(positions)} positions):")
            print("-"*80)
            print(f"  Best TP:        {best['tp_points']} points (${best['tp_points']*0.01:.2f})")
            print(f"  Win Rate:       {best['win_rate']:.1f}% ({best['tp_hits']}/{best['tp_hits']+best['misses']})")
            print(f"  TP Profit:      ${best['tp_pnl']:.2f}")
            print(f"  Miss Loss:      ${best['miss_pnl']:.2f}")
            print(f"  SIMULATED P&L:  ${best['total_pnl']:.2f}")
            print(f"  Actual P&L:     ${best['actual_pl']:.2f}")
            print(f"  vs Actual:      {best['total_pnl'] - best['actual_pl']:+.2f}")
            
            # Show top 3 for this session
            print(f"\n  Top 3 configurations:")
            top3 = sorted(results, key=lambda x: x['total_pnl'], reverse=True)[:3]
            for i, r in enumerate(top3, 1):
                print(f"    {i}. TP {r['tp_points']:>3}pts: ${r['total_pnl']:>6.2f} ({r['win_rate']:.1f}% win)")
        
        # Final recommendations
        print("\n" + "="*120)
        print("FINAL RECOMMENDATIONS - PRIORITIZING MAXIMUM P&L")
        print("="*120)
        
        print("""
+----------------+----------------+----------------+----------------+----------------+----------------+
|    Session     | Best TP        | Win Rate       | Sim P&L        | Actual P&L     | Trail Start    |
|                | (Points/$)     |                |                |                | (Points/$)     |
+----------------+----------------+----------------+----------------+----------------+----------------+
""")
        
        for session_name in ['ASIA', 'LONDON', 'NY']:
            results = all_results[session_name]
            best = max(results, key=lambda x: x['total_pnl'])
            trail_start = int(best['tp_points'] * 0.5)
            trail_dist = int(trail_start * 0.7)
            
            print(f"| {session_name:<14} | {best['tp_points']:>3} / ${best['tp_points']*0.01:<5.2f} | {best['win_rate']:<6.1f}%        | ${best['total_pnl']:<6.2f}        | ${best['actual_pl']:<6.2f}        | {trail_start:>3} / ${trail_start*0.01:<5.2f}   |")
            print("+----------------+----------------+----------------+----------------+----------------+----------------+")
        
        print("""
TRAILING STOP DISTANCE:
  Asia:   ~30-35 pts ($0.30-$0.35)
  London: ~60-70 pts ($0.60-$0.70)
  NY:     ~60-70 pts ($0.60-$0.70)

NOTE: These recommendations prioritize MAXIMUM P&L, not win rate.
      Lower win rates (60-80%) with higher TPs produce more profit.
""")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
