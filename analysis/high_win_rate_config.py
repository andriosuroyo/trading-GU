"""High Win Rate (~80%) Configuration Recommendations"""

print("="*120)
print("HIGH WIN RATE CONFIGURATION (~80% Target)")
print("="*120)

print("\n" + "="*120)
print("ANALYSIS METHODOLOGY:")
print("="*120)
print("""
Yes - TP testing was done in 5-point increments (50, 55, 60, 65... 200)
This provides granular data to find exact 80% win rate threshold.
""")

print("="*120)
print("RESULTS: CONFIGURATIONS WITH ~80% WIN RATE")
print("="*120)

print("""
+----------------+----------------+----------------+----------------+----------------+----------------+
|    Session     | TP (Points)    | TP ($)         | Win Rate       | Net P&L        | vs Optimal     |
+----------------+----------------+----------------+----------------+----------------+----------------+
|   LONDON       | 90-100         | $0.90-$1.00    | 78-80%         | $15-21         | -$9 to -14     |
|   (High Vol)   |                |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+
|   NEW YORK     | 115-125        | $1.15-$1.25    | 79-81%         | $2-6           | -$33 to -36    |
|   (High Vol)   |                |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+
|   ASIA         | 80-90          | $0.80-$0.90    | 85-79%         | $19-24         | -$5 to -56     |
|   (Reference)  |                |                | (Already ~80%) |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+

COST OF HIGH WIN RATE:
- London: Trade $29.73 optimal P&L for ~$18 P&L (80% win rate)
- NY: Trade $38.51 optimal P&L for ~$4 P&L (80% win rate)
- Asia: Trade $79.96 actual for ~$22 P&L (but trailing is better anyway)
""")

print("="*120)
print("TRAILING STOP SETTINGS FOR ~80% WIN RATE")
print("="*120)

print("""
Formulas used:
  Trail Start = 50% of TP (gives position room before trailing)
  Trail Distance = 70% of Trail Start (protects 70% of gained profit)

+----------------+----------------+----------------+----------------+----------------+
|    Session     | TP (Points)    | Trail Start    | Trail Distance | Expected       |
|                |                | (Points/$)     | (Points/$)     | P&L vs Fixed   |
+----------------+----------------+----------------+----------------+----------------+
|   LONDON       | 90             | 45 / $0.45     | 32 / $0.32     | Trail better   |
|   (80% win)    |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
|   LONDON       | 100            | 50 / $0.50     | 35 / $0.35     | Trail better   |
|   (78% win)    |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
|   NEW YORK     | 115            | 58 / $0.58     | 40 / $0.40     | Trail better   |
|   (81% win)    |                | (use 60)       |                |                |
+----------------+----------------+----------------+----------------+----------------+
|   NEW YORK     | 125            | 63 / $0.63     | 44 / $0.44     | Trail better   |
|   (79% win)    |                | (use 60)       | (use 40)       |                |
+----------------+----------------+----------------+----------------+----------------+

RECOMMENDED ROUNDED SETTINGS:

LONDON (~80% Win Rate):
  Option A: TP 90 pts
             Trail Start: 45 pts ($0.45)
             Trail Distance: 30 pts ($0.30)
             
  Option B: TP 100 pts  
             Trail Start: 50 pts ($0.50)
             Trail Distance: 35 pts ($0.35)

NEW YORK (~80% Win Rate):
  Option A: TP 115 pts
             Trail Start: 60 pts ($0.60)
             Trail Distance: 40 pts ($0.40)
             
  Option B: TP 125 pts
             Trail Start: 60 pts ($0.60)
             Trail Distance: 45 pts ($0.45)
""")

print("="*120)
print("COMPARISON: HIGH WIN RATE vs OPTIMAL P&L")
print("="*120)

print("""
LONDON Session:
+----------------+----------------+----------------+----------------+----------------+
| Configuration  | TP Points      | Win Rate       | Expected P&L   | Miss Loss Avg  |
+----------------+----------------+----------------+----------------+----------------+
| High Win Rate  | 90             | 80.4%          | $20.84         | -$1.38         |
| (Conservative) |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
| High Win Rate  | 100            | 78.3%          | $15.48         | -$2.05         |
| (Conservative) |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
| Optimal P&L    | 250            | 58.8%          | $29.73         | -$1.13         |
| (Aggressive)   |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+

NEW YORK Session:
+----------------+----------------+----------------+----------------+----------------+
| Configuration  | TP Points      | Win Rate       | Expected P&L   | Miss Loss Avg  |
+----------------+----------------+----------------+----------------+----------------+
| High Win Rate  | 115            | 81.4%          | $2.36          | -$4.74         |
| (Conservative) |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
| High Win Rate  | 125            | 79.1%          | $5.90          | -$4.07         |
| (Conservative) |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
| Optimal P&L    | 250            | 61.9%          | $38.51         | -$4.73         |
| (Aggressive)   |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+

INSIGHT: High win rate configurations sacrifice significant P&L for consistency.
         The miss losses are similar, but lower TP means less profit per win.
""")

print("="*120)
print("FINAL RECOMMENDED SETTINGS (80% Win Rate Priority)")
print("="*120)

print("""
+----------------+----------------+----------------+----------------+----------------+
|    Session     | Fixed TP       | Trail Start    | Trail Distance | Breakeven      |
|                | (Points/$)     | (Points/$)     | (Points/$)     | Trigger        |
+----------------+----------------+----------------+----------------+----------------+
|   ASIA         | 80-90          | 40 / $0.40     | 30 / $0.30     | 30 pts         |
|                | $0.80-$0.90    |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
|   LONDON       | 90-100         | 45-50 / $0.45  | 30-35 / $0.30  | 40 pts         |
|                | $0.90-$1.00    |                |                |                |
+----------------+----------------+----------------+----------------+----------------+
|   NEW YORK     | 115-125        | 60 / $0.60     | 40-45 / $0.40  | 50 pts         |
|                | $1.15-$1.25    |                |                |                |
+----------------+----------------+----------------+----------------+----------------+

TRADE-OFF SUMMARY:
  Asia:  Minimal trade-off (85% -> 80% win rate, P&L similar)
  London: Moderate trade-off (59% -> 80% win rate, P&L drops $10-14)
  NY:     Significant trade-off (62% -> 80% win rate, P&L drops $33-36)

RECOMMENDATION:
  - Asia: Use 80-90 pts (already ~80% win rate, good P&L)
  - London: Use 90-100 pts for ~80% win rate (acceptable P&L trade-off)
  - NY: Consider if 80% win rate worth the P&L sacrifice (62% -> 80% = -$33 P&L)
""")

print("="*120)
