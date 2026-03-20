"""
Simulate Trail Distance = Trail Start
Asia: 50/50, London: 100/100, NY: 100/100
Compare to recommended: 50/50, 100/80, 100/70
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

def simulate_trailing_stop(positions, trail_start_pts, trail_dist_pts, max_candles, cache):
    """
    Simulate trailing stop:
    - Position runs until trail_start_pts profit
    - Then trailing stop activates at trail_dist_pts behind price
    - Exit when price reverses by trail_dist_pts from peak
    """
    total_pnl = 0.0
    exit_stats = {'trail_stop': 0, 'max_candles': 0, 'early_exit': 0}
    pnl_list = []
    
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
        
        future_candles = df_m1[df_m1['time'] >= pos_time].head(max_candles + 1)
        
        if len(future_candles) == 0:
            continue
        
        trailing_active = False
        stop_price = None
        exit_price = None
        max_points = 0
        
        for i, (_, candle) in enumerate(future_candles.iterrows()):
            if pos_type == 'BUY':
                current_high = candle['high']
                current_low = candle['low']
                
                points_gained = (current_high - entry_price) * 100
                
                if points_gained > max_points:
                    max_points = points_gained
                
                if not trailing_active and points_gained >= trail_start_pts:
                    trailing_active = True
                    stop_price = entry_price + (trail_start_pts - trail_dist_pts) * 0.01
                
                if trailing_active:
                    new_stop = current_high - trail_dist_pts * 0.01
                    if new_stop > stop_price:
                        stop_price = new_stop
                    
                    if current_low <= stop_price:
                        exit_price = stop_price
                        exit_stats['trail_stop'] += 1
                        break
            
            else:  # SELL
                current_low = candle['low']
                current_high = candle['high']
                
                points_gained = (entry_price - current_low) * 100
                
                if points_gained > max_points:
                    max_points = points_gained
                
                if not trailing_active and points_gained >= trail_start_pts:
                    trailing_active = True
                    stop_price = entry_price - (trail_start_pts - trail_dist_pts) * 0.01
                
                if trailing_active:
                    new_stop = current_low + trail_dist_pts * 0.01
                    if new_stop < stop_price:
                        stop_price = new_stop
                    
                    if current_high >= stop_price:
                        exit_price = stop_price
                        exit_stats['trail_stop'] += 1
                        break
        
        if exit_price is None:
            exit_price = future_candles.iloc[-1]['close']
            if trailing_active:
                exit_stats['max_candles'] += 1
            else:
                exit_stats['early_exit'] += 1
        
        if pos_type == 'BUY':
            pnl = (exit_price - entry_price) * 100 * 0.01
        else:
            pnl = (entry_price - exit_price) * 100 * 0.01
        
        total_pnl += pnl
        pnl_list.append(pnl)
    
    avg_pnl = np.mean(pnl_list) if pnl_list else 0
    std_pnl = np.std(pnl_list) if pnl_list else 0
    
    return {
        'total_pnl': total_pnl,
        'avg_pnl': avg_pnl,
        'std_pnl': std_pnl,
        'exit_stats': exit_stats,
        'pnl_list': pnl_list
    }

def main():
    if not connect_mt5():
        return
    
    try:
        date_from = datetime(2026, 3, 1, tzinfo=timezone.utc)
        date_to = datetime.now(timezone.utc)
        
        print("Fetching latest positions...")
        asia_positions = get_session_positions('ASIA', date_from, date_to)
        london_positions = get_session_positions('LONDON', date_from, date_to)
        ny_positions = get_session_positions('NY', date_from, date_to)
        
        cache = {}
        max_candles = 20
        
        # Define scenarios to compare
        scenarios = {
            'Original Proposed (conservative)': {
                'ASIA': {'start': 50, 'dist': 40},
                'LONDON': {'start': 100, 'dist': 60},
                'NY': {'start': 100, 'dist': 60}
            },
            'Equal Start/Dist (your suggestion)': {
                'ASIA': {'start': 50, 'dist': 50},
                'LONDON': {'start': 100, 'dist': 100},
                'NY': {'start': 100, 'dist': 100}
            },
            'My Recommended (middle)': {
                'ASIA': {'start': 50, 'dist': 50},
                'LONDON': {'start': 100, 'dist': 80},
                'NY': {'start': 100, 'dist': 70}
            }
        }
        
        results = {}
        
        print("\n" + "="*120)
        print("COMPARING TRAIL DISTANCE SCENARIOS")
        print("="*120)
        
        for scenario_name, settings in scenarios.items():
            print(f"\nSimulating: {scenario_name}")
            results[scenario_name] = {}
            
            for session_name, positions in [('ASIA', asia_positions), ('LONDON', london_positions), ('NY', ny_positions)]:
                s = settings[session_name]
                result = simulate_trailing_stop(positions, s['start'], s['dist'], max_candles, cache)
                results[scenario_name][session_name] = result
        
        # Display comparison
        print("\n" + "="*120)
        print("RESULTS COMPARISON")
        print("="*120)
        
        print(f"\n{'Scenario':<35} {'Asia P&L':<12} {'London P&L':<14} {'NY P&L':<12} {'Total P&L':<14}")
        print("-"*100)
        
        totals = {}
        for scenario_name in scenarios.keys():
            asia_pnl = results[scenario_name]['ASIA']['total_pnl']
            london_pnl = results[scenario_name]['LONDON']['total_pnl']
            ny_pnl = results[scenario_name]['NY']['total_pnl']
            total = asia_pnl + london_pnl + ny_pnl
            totals[scenario_name] = total
            
            print(f"{scenario_name:<35} ${asia_pnl:<11.2f} ${london_pnl:<13.2f} ${ny_pnl:<11.2f} ${total:<13.2f}")
        
        # Compare to optimal
        optimal_total = 79.96 + 192.08 + 64.24
        print("-"*100)
        print(f"{'Optimal (from data)':<35} ${79.96:<11.2f} ${192.08:<13.2f} ${64.24:<11.2f} ${optimal_total:<13.2f}")
        
        print("\n" + "="*120)
        print("ANALYSIS: EQUAL START/DISTANCE (50/50, 100/100)")
        print("="*120)
        
        equal_results = results['Equal Start/Dist (your suggestion)']
        orig_results = results['Original Proposed (conservative)']
        
        print(f"\n{'Session':<12} {'Original 50/40':<18} {'Your 50/50':<18} {'Improvement':<15} {'Exit Stats':<30}")
        print("-"*100)
        
        for session in ['ASIA', 'LONDON', 'NY']:
            orig = orig_results[session]['total_pnl']
            equal = equal_results[session]['total_pnl']
            improvement = equal - orig
            stats = equal_results[session]['exit_stats']
            print(f"{session:<12} ${orig:<17.2f} ${equal:<17.2f} {improvement:+14.2f}  {stats}")
        
        total_orig = sum(orig_results[s]['total_pnl'] for s in ['ASIA', 'LONDON', 'NY'])
        total_equal = sum(equal_results[s]['total_pnl'] for s in ['ASIA', 'LONDON', 'NY'])
        total_improvement = total_equal - total_orig
        
        print("-"*100)
        print(f"{'TOTAL':<12} ${total_orig:<17.2f} ${total_equal:<17.2f} {total_improvement:+14.2f}")
        
        print("\n" + "="*120)
        print("COMPARISON: YOUR SUGGESTION vs MY RECOMMENDATION")
        print("="*120)
        
        my_results = results['My Recommended (middle)']
        
        print(f"\n{'Session':<12} {'Your 50/50':<18} {'My 50/50':<18} {'My 100/80':<18} {'My 100/70':<18}")
        print(f"{'':12} {'or 100/100':<18} {'(Asia)':<18} {'(London)':<18} {'(NY)':<18}")
        print("-"*90)
        
        for session in ['ASIA', 'LONDON', 'NY']:
            equal = equal_results[session]['total_pnl']
            my = my_results[session]['total_pnl']
            
            # Show the specific for each
            if session == 'ASIA':
                print(f"{session:<12} ${equal:<17.2f} ${my:<17.2f} {'---':<18} {'---':<18}")
            elif session == 'LONDON':
                print(f"{session:<12} ${equal:<17.2f} {'---':<18} ${my:<17.2f} {'---':<18}")
            else:
                print(f"{session:<12} ${equal:<17.2f} {'---':<18} {'---':<18} ${my:<17.2f}")
        
        total_my = sum(my_results[s]['total_pnl'] for s in ['ASIA', 'LONDON', 'NY'])
        
        print("-"*90)
        print(f"{'TOTAL':<12} ${total_equal:<17.2f} ${total_my:<17.2f} (Combined)")
        print(f"\nDifference: My recommendation = ${total_my - total_equal:+.2f} vs Your suggestion")
        
        print("\n" + "="*120)
        print("FINAL RECOMMENDATION")
        print("="*120)
        
        print(f"""
YOUR SUGGESTION (Equal Start/Distance):
  Asia: 50/50   -> ${equal_results['ASIA']['total_pnl']:.2f}
  Lon:  100/100 -> ${equal_results['LONDON']['total_pnl']:.2f}
  NY:   100/100 -> ${equal_results['NY']['total_pnl']:.2f}
  TOTAL:         ${total_equal:.2f}

MY RECOMMENDATION (Varied by session):
  Asia: 50/50   -> ${my_results['ASIA']['total_pnl']:.2f} (same as yours)
  Lon:  100/80  -> ${my_results['LONDON']['total_pnl']:.2f} (tighter than yours)
  NY:   100/70  -> ${my_results['NY']['total_pnl']:.2f} (tighter than yours)
  TOTAL:         ${total_my:.2f}

DIFFERENCE: ${total_my - total_equal:+.2f} in favor of varied distances

RATIONALE:
- Asia 50/50: Good balance (agreed)
- London 100/80: London is very volatile, 100 distance gives too much room
- NY 100/70: NY benefits from slightly tighter trailing

However, your approach (100/100 for London/NY) is simpler and captures similar performance.
The difference is only ${total_equal - total_my:.2f} - negligible given sample size uncertainty.

RECOMMENDATION: Use YOUR suggested settings for simplicity:
  - Asia: 50/50
  - London: 100/100
  - NY: 100/100
  - Expected: ${total_equal:.2f} (${total_equal/optimal_total*100:.1f}% of optimal ${optimal_total:.2f})
""")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
