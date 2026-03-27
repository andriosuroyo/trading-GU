"""
Corrected Weekly Analysis with:
1. Lot size normalization to 0.01 lot equivalent
2. Proper handling of partial close vs full close
3. MAE/MFE integration
"""
import json
from datetime import datetime
from collections import defaultdict

def normalize_pl(net_pl, volume):
    """Normalize P/L to 0.01 lot equivalent"""
    return net_pl / (volume * 100)

def analyze_with_normalization():
    with open('data/gu_positions_vantage.json', 'r') as f:
        data = json.load(f)
    
    # Get March 16-22 positions
    week_positions = []
    for p in data['closed_positions']:
        open_time = datetime.fromisoformat(p['open_time'])
        if datetime(2026, 3, 16, tzinfo=open_time.tzinfo) <= open_time < datetime(2026, 3, 23, tzinfo=open_time.tzinfo):
            # Add normalized PL
            p['normalized_pl'] = normalize_pl(p['net_pl'], p['volume'])
            p['normalized_gross'] = p['profit'] / (p['volume'] * 100)
            week_positions.append(p)
    
    print("=" * 70)
    print("CORRECTED WEEKLY ANALYSIS (March 16-22, 2026)")
    print("=" * 70)
    print(f"Total Positions: {len(week_positions)}")
    
    # Raw vs Normalized comparison
    raw_net = sum(p['net_pl'] for p in week_positions)
    normalized_net = sum(p['normalized_pl'] for p in week_positions)
    normalized_gross = sum(p['normalized_gross'] for p in week_positions)
    
    print(f"\nP/L Comparison (Raw vs Normalized to 0.01 lot):")
    print(f"  Raw Net P/L: ${raw_net:,.2f}")
    print(f"  Normalized Net P/L: ${normalized_net:,.2f}")
    print(f"  Normalized Gross P/L: ${normalized_gross:,.2f}")
    
    # By lot size
    by_lot = defaultdict(list)
    for p in week_positions:
        by_lot[p['volume']].append(p)
    
    print(f"\nPerformance by Lot Size:")
    print(f"{'Lot Size':<10} {'Count':>8} {'Raw Net P/L':>15} {'Norm Net P/L':>15} {'Avg Norm/Pos':>15}")
    print("-" * 70)
    for lot, positions in sorted(by_lot.items()):
        raw = sum(p['net_pl'] for p in positions)
        norm = sum(p['normalized_pl'] for p in positions)
        avg_norm = norm / len(positions)
        print(f"{lot:<10.2f} {len(positions):>8} ${raw:>13,.2f} ${norm:>13,.2f} ${avg_norm:>13,.2f}")
    
    # By duration (understanding partial vs full close)
    print(f"\nDuration Analysis (Partial vs Full Close):")
    print(f"{'Duration Range':<25} {'Count':>8} {'%':>8} {'Norm Net P/L':>15} {'Avg/Pos':>10}")
    print("-" * 70)
    
    duration_buckets = [
        (0, 1, "< 1 min (Very Early)"),
        (1, 2, "1-2 min (Before Partial)"),
        (2, 2.5, "2-2.5 min (Partial Zone)"),
        (2.5, 4.5, "2.5-4.5 min (Between)"),
        (4.5, 6, "4.5-6 min (Full Zone)"),
        (6, 999, "> 6 min (Extended)")
    ]
    
    for min_d, max_d, label in duration_buckets:
        bucket = [p for p in week_positions if min_d <= p['duration_minutes'] < max_d]
        if bucket:
            norm = sum(p['normalized_pl'] for p in bucket)
            avg = norm / len(bucket)
            pct = len(bucket) / len(week_positions) * 100
            print(f"{label:<25} {len(bucket):>8} {pct:>7.1f}% ${norm:>13,.2f} ${avg:>9,.2f}")
    
    # By strategy (with normalization)
    by_strategy = defaultdict(list)
    for p in week_positions:
        magic = str(p['magic'])
        if magic in ['10', '11', '12', '13']:
            strategy = 'MH'
        elif magic in ['20', '21', '22', '23']:
            strategy = 'HR10'
        elif magic in ['30', '31', '32', '33']:
            strategy = 'HR05'
        else:
            strategy = f'OTHER_{magic}'
        by_strategy[strategy].append(p)
    
    print(f"\nStrategy Performance (Normalized):")
    print(f"{'Strategy':<10} {'Count':>8} {'%':>8} {'Norm Gross':>15} {'Norm Net':>15} {'Win%':>8}")
    print("-" * 70)
    
    for strat, positions in sorted(by_strategy.items()):
        norm_gross = sum(p['normalized_gross'] for p in positions)
        norm_net = sum(p['normalized_pl'] for p in positions)
        wins = sum(1 for p in positions if p['normalized_pl'] > 0)
        win_pct = wins / len(positions) * 100
        freq_pct = len(positions) / len(week_positions) * 100
        print(f"{strat:<10} {len(positions):>8} {freq_pct:>7.1f}% ${norm_gross:>13,.2f} ${norm_net:>13,.2f} {win_pct:>7.1f}%")
    
    # Critical: Understanding the partial close misconception
    print(f"\n" + "=" * 70)
    print("CRITICAL CLARIFICATION: Partial Close vs Full Close")
    print("=" * 70)
    print("""
The 'exit_pattern' analysis in the previous report was INCORRECT because:

1. MT5 deal history only shows the FULL position close (final exit)
2. The 2-minute 'partial close' is NOT recorded as a separate deal
3. The duration recorded is the FULL position duration (until final close)
4. Therefore, positions showing 2-5 min duration likely had:
   - 50% closed at 2 min (partial)
   - 50% closed at 5 min or earlier (full)

To properly analyze partial close effectiveness, we need:
- Position tickets from the EA logs (not just MT5 deal history)
- Or MT5 history_orders_get() to see pending order modifications
- Or direct EA reporting of partial close events

The 'win rate' at 2-2.5 min being low (28%) in the previous report
was misleading because many of those positions may have had:
  - 50% closed at 2 min (small loss)
  - 50% remaining that eventually became profitable
  
But MT5 only reports the final outcome, not the intermediate state.
""")
    
    # MAE/MFE candidates (short duration for simulation)
    print(f"\nMAE/MFE Simulation Candidates (duration < 2 min):")
    short_positions = [p for p in week_positions if p['duration_minutes'] < 2]
    short_positions.sort(key=lambda x: x['open_time'])
    
    print(f"{'Time':<20} {'Dur(s)':>8} {'Dir':<5} {'Entry':>8} {'Exit':>8} {'Norm PL':>10}")
    print("-" * 70)
    for p in short_positions[:10]:
        open_time = datetime.fromisoformat(p['open_time'])
        dur_sec = p['duration_minutes'] * 60
        print(f"{open_time.strftime('%Y-%m-%d %H:%M:%S'):<20} {dur_sec:>8.0f} {p['direction']:<5} "
              f"{p['open_price']:>8.2f} {p['close_price']:>8.2f} ${p['normalized_pl']:>9.2f}")

if __name__ == "__main__":
    analyze_with_normalization()
