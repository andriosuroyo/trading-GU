"""Final Recommendations - Prioritizing Best P&L (Latest Data)"""

print("="*110)
print("FINAL RECOMMENDATIONS - PRIORITIZING MAXIMUM P&L (NOT WIN RATE)")
print("Data: Latest GU positions from MT5 (March 2026)")
print("="*110)

print("\n" + "-"*110)
print("SESSION SUMMARY (Latest Data)")
print("-"*110)

print("""
+----------------+----------+----------------+----------------+----------------+
|    Session     | Positions| Actual P&L     | Best Fixed TP  | Best Sim P&L   |
|                |          | (Trailing)     | P&L            | vs Actual      |
+----------------+----------+----------------+----------------+----------------+
| ASIA           | 62       | $79.96         | $24.22         | -55.74         |
| (02-05 UTC)    |          |                | (TP 110)       |                |
+----------------+----------+----------------+----------------+----------------+
| LONDON         | 85       | $192.08        | $29.73         | -162.35        |
| (11-14 UTC)    |          |                | (TP 250)       |                |
+----------------+----------+----------------+----------------+----------------+
| NEW YORK       | 115      | $64.24         | $38.51         | -25.73         |
| (13-17 UTC)    |          |                | (TP 250)       |                |
+----------------+----------+----------------+----------------+----------------+

KEY FINDING: Trailing stop significantly outperforms fixed TP in ALL sessions.
             Fixed TP is only recommended if trailing cannot be implemented.
""")

print("-"*110)
print("OPTION 1: FIXED TP CONFIGURATION (If trailing stop not available)")
print("-"*110)

print("""
+----------------+----------------+----------------+----------------+----------------+----------------+
|    Session     | TP Points      | TP ($)         | Win Rate       | Exp P&L        | Time Cutoff    |
+----------------+----------------+----------------+----------------+----------------+----------------+
| ASIA           | 110            | $1.10          | 78.7%          | $24.22         | 5 minutes      |
+----------------+----------------+----------------+----------------+----------------+----------------+
| LONDON         | 250            | $2.50          | 58.8%          | $29.73         | 5 minutes      |
+----------------+----------------+----------------+----------------+----------------+----------------+
| NEW YORK       | 250            | $2.50          | 61.9%          | $38.51         | 5 minutes      |
+----------------+----------------+----------------+----------------+----------------+----------------+

RATIONALE:
  - Asia: Lower TP (110) works due to moderate volatility
  - London/NY: Higher TP (250) needed for volatile sessions
  - 5-minute cutoff balances capture rate vs miss losses
""")

print("-"*110)
print("OPTION 2: TRAILING STOP CONFIGURATION (RECOMMENDED)")
print("-"*110)

print("""
+----------------+----------------+----------------+----------------+----------------+----------------+
|    Session     | Trail Start    | Trail Distance | Breakeven      | Exp P&L        | vs Fixed TP    |
|                | (Points/$)     | (Points/$)     | Trigger        |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+
| ASIA           | 55 / $0.55     | 35 / $0.35     | 40 pts         | $79.96         | +230%          |
+----------------+----------------+----------------+----------------+----------------+----------------+
| LONDON         | 125 / $1.25    | 85 / $0.85     | 80 pts         | $192.08        | +546%          |
+----------------+----------------+----------------+----------------+----------------+----------------+
| NEW YORK       | 125 / $1.25    | 85 / $0.85     | 80 pts         | $64.24         | +67%           |
+----------------+----------------+----------------+----------------+----------------+----------------+

TRAILING STOP LOGIC:
  1. Trail Start = 50% of equivalent optimal TP
  2. Trail Distance = ~70% of trail start (protects profit)
  3. Breakeven = Move SL to entry at 40-80 pts profit
  4. Let winners run, trail locks in gains
""")

print("-"*110)
print("QUICK REFERENCE TABLE")
print("-"*110)

print("""
+----------------+----------------+----------------+----------------+----------------+
|    Session     | Fixed TP       | Trail Start    | Trail Distance | Priority       |
|                | (Points/$)     | (Points/$)     | (Points/$)     |                |
+----------------+----------------+----------------+----------------+----------------+
| ASIA           | 110 / $1.10    | 55 / $0.55     | 35 / $0.35     | Trailing       |
| (02-05 UTC)    |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
| LONDON         | 250 / $2.50    | 125 / $1.25    | 85 / $0.85     | Trailing       |
| (11-14 UTC)    |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
| NEW YORK       | 250 / $2.50    | 125 / $1.25    | 85 / $0.85     | Trailing       |
| (13-17 UTC)    |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+

DECISION RULE:
  1. Can you implement trailing stop well? -> Use trailing (67-546% better)
  2. Need simple fixed exits? -> Use fixed TP with 5-min cutoff
  3. Always prioritize P&L over win rate
""")

print("-"*110)
print("IMPORTANT NOTES")
print("-"*110)

print("""
1. WIN RATE vs P&L TRADE-OFF:
   - High win rate (80%+) = Lower P&L (sacrificing profit for consistency)
   - Optimal P&L (60-70% win) = Maximum profit (accepting some losses)
   - Recommendation: Prioritize P&L, accept 60-80% win rates

2. LONDON IS THE STAR:
   - Highest actual P&L ($192)
   - Most volatile = biggest moves when right
   - Trailing stop captures this volatility best

3. IMPLEMENTATION CHECKLIST:
   [ ] Can your platform execute trailing stops accurately?
   [ ] Can you monitor/manage positions during session hours?
   [ ] Do you have slippage control on exits?
   
   If YES to all -> Use trailing stop
   If NO -> Use fixed TP with 5-minute cutoff
""")

print("="*110)
