"""
Simulate proposed conservative settings:
- TP: Asia 100, London 200, NY 200
- Trail: Asia Start 50/Dist 40, London/NY Start 100/Dist 60
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

def simulate_fixed_tp(positions, tp_points, cutoff, cache):
    """Simulate fixed TP with time cutoff"""
    tp_hits = 0
    misses = 0
    total_pnl = 0.0
    
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
        
        for i, (_, candle) in enumerate(future_candles.iterrows()):
            if pos_type == 'BUY':
                if candle['high'] >= tp_price:
                    tp_hit = True
                    break
            else:
                if candle['low'] <= tp_price:
                    tp_hit = True
                    break
        
        if tp_hit:
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
                total_pnl += exit_pnl
    
    return {
        'tp_hits': tp_hits,
        'misses': misses,
        'total_pnl': total_pnl
    }

def simulate_trailing_stop(positions, trail_start_pts, trail_dist_pts, max_candles, cache):
    """
    Simulate trailing stop:
    - Position runs until trail_start_pts profit
    - Then trailing stop activates at trail_dist_pts behind price
    - Exit when price reverses by trail_dist_pts from peak
    - Or at max_candles if not stopped
    """
    total_pnl = 0.0
    exit_reasons = {'trail_stop': 0, 'max_candles': 0}
    
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
        
        # Track high/low water mark
        trailing_active = False
        stop_price = None
        exit_price = None
        
        for i, (_, candle) in enumerate(future_candles.iterrows()):
            if pos_type == 'BUY':
                # Check if we've reached trail start level
                current_high = candle['high']
                current_low = candle['low']
                current_close = candle['close']
                
                points_gained = (current_high - entry_price) * 100
                
                if not trailing_active and points_gained >= trail_start_pts:
                    trailing_active = True
                    stop_price = entry_price + (trail_start_pts - trail_dist_pts) * 0.01
                
                if trailing_active:
                    # Update stop price if we made new highs
                    new_stop = current_high - trail_dist_pts * 0.01
                    if new_stop > stop_price:
                        stop_price = new_stop
                    
                    # Check if we hit the trailing stop
                    if current_low <= stop_price:
                        exit_price = stop_price
                        exit_reasons['trail_stop'] += 1
                        break
            
            else:  # SELL
                current_low = candle['low']
                current_high = candle['high']
                current_close = candle['close']
                
                points_gained = (entry_price - current_low) * 100
                
                if not trailing_active and points_gained >= trail_start_pts:
                    trailing_active = True
                    stop_price = entry_price - (trail_start_pts - trail_dist_pts) * 0.01
                
                if trailing_active:
                    new_stop = current_low + trail_dist_pts * 0.01
                    if new_stop < stop_price:
                        stop_price = new_stop
                    
                    if current_high >= stop_price:
                        exit_price = stop_price
                        exit_reasons['trail_stop'] += 1
                        break
        
        # If we didn't exit via trail stop, exit at last candle close
        if exit_price is None:
            exit_price = future_candles.iloc[-1]['close']
            exit_reasons['max_candles'] += 1
        
        # Calculate P&L
        if pos_type == 'BUY':
            pnl = (exit_price - entry_price) * 100 * 0.01
        else:
            pnl = (entry_price - exit_price) * 100 * 0.01
        
        total_pnl += pnl
    
    return {
        'total_pnl': total_pnl,
        'exit_reasons': exit_reasons
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
        
        print("\n" + "="*120)
        print("SIMULATING PROPOSED CONSERVATIVE SETTINGS")
        print("="*120)
        
        # Proposed settings
        proposed = {
            'ASIA': {'tp': 100, 'trail_start': 50, 'trail_dist': 40, 'max_candles': 20},
            'LONDON': {'tp': 200, 'trail_start': 100, 'trail_dist': 60, 'max_candles': 20},
            'NY': {'tp': 200, 'trail_start': 100, 'trail_dist': 60, 'max_candles': 20}
        }
        
        # Optimal settings from earlier analysis
        optimal = {
            'ASIA': {'tp': 110, 'trail_start': 55, 'trail_dist': 35, 'actual_pl': 79.96},
            'LONDON': {'tp': 250, 'trail_start': 125, 'trail_dist': 85, 'actual_pl': 192.08},
            'NY': {'tp': 250, 'trail_start': 125, 'trail_dist': 85, 'actual_pl': 64.24}
        }
        
        results = {}
        
        for session_name, positions in [('ASIA', asia_positions), ('LONDON', london_positions), ('NY', ny_positions)]:
            settings = proposed[session_name]
            
            # Simulate fixed TP
            fixed_result = simulate_fixed_tp(positions, settings['tp'], 5, cache)
            
            # Simulate trailing stop
            trail_result = simulate_trailing_stop(positions, settings['trail_start'], settings['trail_dist'], 
                                                   settings['max_candles'], cache)
            
            results[session_name] = {
                'positions': len(positions),
                'fixed': fixed_result,
                'trail': trail_result,
                'optimal_actual': optimal[session_name]['actual_pl']
            }
        
        # Display results
        print("\n" + "-"*120)
        print("PROPOSED SETTINGS:")
        print("-"*120)
        print(f"{'Session':<12} {'TP (pts)':<10} {'Trail Start':<12} {'Trail Dist':<12} {'Max Candles':<12}")
        print("-"*120)
        for session_name in ['ASIA', 'LONDON', 'NY']:
            s = proposed[session_name]
            print(f"{session_name:<12} {s['tp']:<10} {s['trail_start']:<12} {s['trail_dist']:<12} {s['max_candles']:<12}")
        
        print("\n" + "-"*120)
        print("SIMULATION RESULTS:")
        print("-"*120)
        
        print(f"\n{'Session':<10} {'Positions':<10} {'Fixed TP P&L':<15} {'Trail P&L':<15} {'Optimal*':<15} {'vs Optimal':<15}")
        print("-"*100)
        
        total_proposed_fixed = 0
        total_proposed_trail = 0
        total_optimal = 0
        
        for session_name in ['ASIA', 'LONDON', 'NY']:
            r = results[session_name]
            fixed_pnl = r['fixed']['total_pnl']
            trail_pnl = r['trail']['total_pnl']
            optimal_pnl = r['optimal_actual']
            
            total_proposed_fixed += fixed_pnl
            total_proposed_trail += trail_pnl
            total_optimal += optimal_pnl
            
            diff = trail_pnl - optimal_pnl
            
            print(f"{session_name:<10} {r['positions']:<10} ${fixed_pnl:<14.2f} ${trail_pnl:<14.2f} ${optimal_pnl:<14.2f} {diff:+15.2f}")
        
        print("-"*100)
        print(f"{'TOTAL':<10} {sum(r['positions'] for r in results.values()):<10} ${total_proposed_fixed:<14.2f} ${total_proposed_trail:<14.2f} ${total_optimal:<14.2f} {total_proposed_trail - total_optimal:+15.2f}")
        
        print("\n* Optimal = Actual trailing stop performance from data")
        
        # Detailed breakdown
        print("\n" + "="*120)
        print("DETAILED BREAKDOWN BY SESSION")
        print("="*120)
        
        for session_name in ['ASIA', 'LONDON', 'NY']:
            r = results[session_name]
            s = proposed[session_name]
            
            print(f"\n{session_name} ({r['positions']} positions):")
            print("-"*80)
            print(f"  Settings: TP {s['tp']}pts, Trail Start {s['trail_start']}pts, Trail Dist {s['trail_dist']}pts")
            print(f"  Fixed TP P&L:      ${r['fixed']['total_pnl']:.2f} ({r['fixed']['tp_hits']} hits, {r['fixed']['misses']} misses)")
            print(f"  Trailing Stop P&L: ${r['trail']['total_pnl']:.2f}")
            print(f"  Optimal Actual:    ${r['optimal_actual']:.2f}")
            print(f"  Difference:        ${r['trail']['total_pnl'] - r['optimal_actual']:+.2f}")
            print(f"  Exit reasons: {r['trail']['exit_reasons']}")
        
        # Comparison table
        print("\n" + "="*120)
        print("COMPARISON: PROPOSED vs OPTIMAL SETTINGS")
        print("="*120)
        
        print("""
+----------------+----------------+----------------+----------------+----------------+----------------+
|                | PROPOSED       | PROPOSED       | OPTIMAL        | OPTIMAL        | P&L Impact     |
| Session        | TP/Trail       | Exp P&L        | TP/Trail       | Exp P&L        | of Conservative|
+----------------+----------------+----------------+----------------+----------------+----------------+
""")
        
        comparisons = [
            ('ASIA', 100, '50/40', 'ASIA', 110, '55/35'),
            ('LONDON', 200, '100/60', 'LONDON', 250, '125/85'),
            ('NY', 200, '100/60', 'NY', 250, '125/85')
        ]
        
        for session, prop_tp, prop_trail, opt_key, opt_tp, opt_trail in comparisons:
            r = results[session]
            prop_pnl = r['trail']['total_pnl']
            opt_pnl = r['optimal_actual']
            impact = prop_pnl - opt_pnl
            
            print(f"| {session:<14} | {prop_tp}/{prop_trail:<9} | ${prop_pnl:<14.2f} | {opt_tp}/{opt_trail:<9} | ${opt_pnl:<14.2f} | {impact:>+7.2f}        |")
            print("+----------------+----------------+----------------+----------------+----------------+----------------+")
        
        total_prop = sum(results[s]['trail']['total_pnl'] for s in ['ASIA', 'LONDON', 'NY'])
        total_opt = sum(results[s]['optimal_actual'] for s in ['ASIA', 'LONDON', 'NY'])
        total_impact = total_prop - total_opt
        
        print(f"| {'TOTAL':<14} |                | ${total_prop:<14.2f} |                | ${total_opt:<14.2f} | {total_impact:>+7.2f}        |")
        print("+----------------+----------------+----------------+----------------+----------------+----------------+")
        
        print(f"\nTotal P&L Impact: ${total_impact:+.2f}")
        if total_impact < 0:
            pct = (total_impact / total_opt) * 100
            print(f"This is {abs(pct):.1f}% less than optimal settings")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
