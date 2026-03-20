"""Final recommendation for session-based TP settings"""

print("="*100)
print("FINAL RECOMMENDATION: SESSION-BASED TP SETTINGS (5-Minute Cutoff)")
print("="*100)

print("\n" + "-"*100)
print("TP 80 PERFORMANCE COMPARISON:")
print("-"*100)
print("""
                    Asia        NY          Difference
                    ----        --          ----------
Win Rate            87.1%       33.0%       -54.1%
TP Hits             54/62       38/115      
Misses              7/62        4/115
TP Profit           $43.20      $30.40
Miss Loss           -$23.77     -$12.86
NET P&L             $19.43      $17.54      -$1.89

INTERPRETATION:
- TP 80 works well in Asia (high win rate, good P&L)
- TP 80 is TOO LOW for NY (only 33% hit rate, missing bigger moves)
- NY positions need higher TP to capture the faster/volatile moves
""")

print("-"*100)
print("OPTIMAL TP BY SESSION:")
print("-"*100)
print("""
                    Best TP     Win Rate    Net P&L     vs TP 80
                    -------     --------    -------     --------
ASIA                110 ($1.10) 78.7%       $24.22      +$4.79
NEW YORK            250 ($2.50) 61.9%       $38.51      +$20.97

KEY INSIGHT:
- Asia optimal: TP 80-110 range (slower, more predictable moves)
- NY optimal: TP 200-250 range (faster, needs bigger targets)
""")

print("-"*100)
print("RECOMMENDED SETTINGS:")
print("-"*100)
print("""
+-----------------+------------------+------------------+
|     Session     |   Recommended TP |   Time Cutoff    |
+-----------------+------------------+------------------+
|   ASIA          |   80-90 points   |   5 minutes      |
|   ($0.80-$0.90) |   (87-85% win)   |   (conservative) |
+-----------------+------------------+------------------+
|   NEW YORK      |   200-250 points |   5 minutes      |
|   ($2.00-$2.50) |   (67-62% win)   |   (same cutoff)  |
+-----------------+------------------+------------------+

RATIONALE:
1. ASIA (02:00-05:00 UTC): Lower volatility, steady moves
   - TP 80-90 captures most of the available range
   - High win rate (85-87%) with acceptable miss losses

2. NEW YORK (13:00-17:00 UTC): Higher volatility, bigger moves
   - TP 200-250 needed to capture typical NY range
   - Lower win rate (62-67%) but bigger winners compensate
   - TP 80 would cut profits short (only 33% hit rate)

3. TIME CUTOFF: Keep 5 minutes for both
   - Shorter than 5 min = too many misses
   - Longer than 5 min = miss losses compound too much
""")

print("-"*100)
print("IMPORTANT CAVEAT:")
print("-"*100)
print("""
ACTUAL TRAILING STOP OUTPERFORMS FIXED TP:
- Asia Trailing: $79.96 vs Fixed TP 110: $24.22
- NY Trailing:   $64.24 vs Fixed TP 250: $38.51

Trailing stop captures momentum beyond fixed targets.
Only use fixed TP if trailing stop implementation is problematic.
""")

print("="*100)
