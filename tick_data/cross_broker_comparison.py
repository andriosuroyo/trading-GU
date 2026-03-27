"""
Cross-broker tick data comparison
Compares BlackBull vs Vantage prices to assess usability for analysis
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

def load_env():
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def get_price_at_time(terminal_key, symbol, target_time, tolerance_sec=2):
    """Get price at specific time from specified broker"""
    env_vars = load_env()
    terminal_path = env_vars.get(terminal_key)
    
    if not mt5.initialize(path=terminal_path):
        return None, f"Init failed: {mt5.last_error()}"
    
    try:
        from_time = target_time - timedelta(seconds=tolerance_sec)
        to_time = target_time + timedelta(seconds=tolerance_sec)
        
        ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
        if ticks is None or len(ticks) == 0:
            return None, "No ticks"
        
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        
        # Find closest tick
        closest_idx = (df['time'] - target_time).abs().idxmin()
        closest = df.loc[closest_idx]
        
        return {
            'time': closest['time'],
            'bid': closest['bid'],
            'ask': closest['ask'],
            'diff_ms': abs((closest['time'] - target_time).total_seconds() * 1000)
        }, None
    finally:
        mt5.shutdown()

def compare_at_times(test_times):
    """Compare prices between brokers at specific times"""
    results = []
    
    for test_time in test_times:
        print(f"\nChecking {test_time}...")
        
        # Get Vantage price
        v_price, v_error = get_price_at_time("MT5_TERMINAL_VANTAGE", "XAUUSD+", test_time)
        # Get BlackBull price  
        bb_price, bb_error = get_price_at_time("MT5_TERMINAL_BLACKBULL", "XAUUSDp", test_time)
        
        result = {
            'time': test_time,
            'vantage': v_price,
            'blackbull': bb_price,
            'v_error': v_error,
            'bb_error': bb_error
        }
        
        if v_price and bb_price:
            bid_diff = abs(v_price['bid'] - bb_price['bid'])
            ask_diff = abs(v_price['ask'] - bb_price['ask'])
            result['bid_diff'] = bid_diff
            result['ask_diff'] = ask_diff
            result['usable'] = bid_diff < 50  # 50 points = $0.50 for gold
            
            print(f"  Vantage:   Bid={v_price['bid']:.2f}, Ask={v_price['ask']:.2f}")
            print(f"  BlackBull: Bid={bb_price['bid']:.2f}, Ask={bb_price['ask']:.2f}")
            print(f"  Diff:      Bid={bid_diff:.2f} pts, Ask={ask_diff:.2f} pts | Usable: {result['usable']}")
        else:
            print(f"  Vantage error: {v_error}")
            print(f"  BlackBull error: {bb_error}")
            result['usable'] = False
        
        results.append(result)
    
    return results

def check_position_entry_alignment():
    """Check alignment between Vantage positions and BlackBull tick data"""
    import json
    
    # Load March 20 positions
    pos_file = "data/gu_positions_vantage.json"
    if not os.path.exists(pos_file):
        print(f"Position file not found: {pos_file}")
        return
    
    with open(pos_file, 'r') as f:
        data = json.load(f)
    
    # Get March 20 positions
    march_20_positions = []
    for p in data.get('closed_positions', []):
        open_time = datetime.fromisoformat(p['open_time'])
        if open_time.date() == datetime(2026, 3, 20).date():
            march_20_positions.append(p)
    
    print(f"\n{'='*70}")
    print(f"POSITION-TICK ALIGNMENT CHECK ({len(march_20_positions)} positions)")
    print(f"{'='*70}")
    
    # Check first 5 positions
    check_count = min(5, len(march_20_positions))
    aligned = 0
    misaligned = 0
    
    for i, pos in enumerate(march_20_positions[:check_count]):
        open_time = datetime.fromisoformat(pos['open_time'])
        entry_price = pos['open_price']
        direction = pos['direction']
        
        # Get BlackBull price at entry time
        bb_price, error = get_price_at_time("MT5_TERMINAL_BLACKBULL", "XAUUSDp", open_time, tolerance_sec=5)
        
        if bb_price:
            # For BUY, compare with ask. For SELL, compare with bid
            if direction == "BUY":
                bb_ref = bb_price['ask']
            else:
                bb_ref = bb_price['bid']
            
            diff_points = abs(entry_price - bb_ref) * 10  # Convert to points (1 pip = 10 points for gold)
            is_aligned = diff_points < 50
            
            status = "[OK] ALIGNED" if is_aligned else "[X] MISALIGNED"
            print(f"\nPos {i+1}: {direction} @ {entry_price:.2f} ({open_time.strftime('%H:%M:%S')})")
            print(f"  BlackBull: Bid={bb_price['bid']:.2f}, Ask={bb_price['ask']:.2f}")
            print(f"  Diff: {diff_points:.1f} points | {status}")
            print(f"  Entry price: {entry_price}, BB ref: {bb_ref}")
            
            if is_aligned:
                aligned += 1
            else:
                misaligned += 1
        else:
            print(f"\nPos {i+1}: Could not fetch BlackBull tick - {error}")
            misaligned += 1
    
    print(f"\n{'='*70}")
    print(f"Alignment: {aligned}/{check_count} ({aligned/check_count*100:.0f}%)")
    print(f"{'='*70}")

def main():
    print("="*70)
    print("CROSS-BROKER TICK DATA COMPARISON")
    print("="*70)
    
    # Test at multiple times throughout March 20
    test_times = [
        datetime(2026, 3, 20, 2, 0, 0, tzinfo=timezone.utc),   # Asia session
        datetime(2026, 3, 20, 8, 0, 0, tzinfo=timezone.utc),   # London open
        datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc),  # London midday
        datetime(2026, 3, 20, 17, 0, 0, tzinfo=timezone.utc),  # NY open
        datetime(2026, 3, 20, 20, 0, 0, tzinfo=timezone.utc),  # NY afternoon
    ]
    
    results = compare_at_times(test_times)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    usable_count = sum(1 for r in results if r.get('usable'))
    total_count = len(results)
    
    print(f"Usable comparisons: {usable_count}/{total_count}")
    
    if usable_count > 0:
        diffs = [r['bid_diff'] for r in results if r.get('usable')]
        print(f"Average bid diff: {sum(diffs)/len(diffs):.2f} points")
        print(f"Max bid diff: {max(diffs):.2f} points")
        print(f"Min bid diff: {min(diffs):.2f} points")
    
    # Check position alignment
    check_position_entry_alignment()
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    if usable_count >= total_count * 0.8:
        print("[PASS] BlackBull tick data is SUITABLE for Vantage position analysis")
        print("  Price differences are within acceptable tolerance (<50 points)")
    else:
        print("[FAIL] BlackBull tick data has SIGNIFICANT divergence from Vantage")
        print("  Cross-broker analysis may introduce bias")

if __name__ == "__main__":
    main()
