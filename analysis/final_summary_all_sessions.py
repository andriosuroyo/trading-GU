"""Complete Summary: TP and Trailing Stop Recommendations"""

print("="*120)
print("COMPLETE SESSION-BASED TRADING CONFIGURATION")
print("="*120)

print("\n" + "="*120)
print("PART 1: SESSION CHARACTERISTICS")
print("="*120)

print("""
+----------+----------+------------+--------------+-------------+-------------+
| Session  | Time     | Positions  | Volatility   | Optimal TP  | Actual P&L  |
|          | (UTC)    | Analyzed   | Level        | (Fixed)     | (Trailing)  |
+----------+----------+------------+--------------+-------------+-------------+
| ASIA     | 02-05    | 62         | Low          | 80-110 pts  | $79.96      |
| LONDON   | 11-14    | 85         | High         | 200-250 pts | $192.08     |
| NEW YORK | 13-17    | 115        | High         | 200-250 pts | $64.24      |
+----------+----------+------------+--------------+-------------+-------------+

OBSERVATIONS:
- London is the most profitable session ($192) - highest volatility
- Asia is consistent but lower absolute returns ($80)
- NY has many positions (115) but lower per-position profitability
""")

print("="*120)
print("PART 2: FIXED TP CONFIGURATION (5-Minute Cutoff)")
print("="*120)

print("""
+----------+----------------+-----------------+----------+-------------+
| Session  | Recommended TP | Alternative TP  | Win Rate | Expected    |
|          | (Points/$)     | (Points/$)      |          | P&L         |
+----------+----------------+-----------------+----------+-------------+
| ASIA     | 80 / $0.80     | 90-110 / $0.90  | 85-79%   | $19-24      |
|          | (conservative) | (aggressive)    |          |             |
+----------+----------------+-----------------+----------+-------------+
| LONDON   | 200 / $2.00    | 250 / $2.50     | 65-59%   | $23-30      |
|          | (conservative) | (aggressive)    |          |             |
+----------+----------------+-----------------+----------+-------------+
| NEW YORK | 200 / $2.00    | 250 / $2.50     | 67-62%   | $29-39      |
|          | (conservative) | (aggressive)    |          |             |
+----------+----------------+-----------------+----------+-------------+

KEY RULE: Never use TP 80 for London/NY - leaves too much money on table!
""")

print("="*120)
print("PART 3: TRAILING STOP CONFIGURATION (RECOMMENDED)")
print("="*120)

print("""
+----------+----------------+----------------+----------------+------------------------+
| Session  | Trail Start    | Trail Distance | Time Limit     | Expected vs Fixed TP   |
|          | (Points/$)     | (Points/$)     | (Optional)     |                        |
+----------+----------------+----------------+----------------+------------------------+
| ASIA     | 40 / $0.40     | 30 / $0.30     | 10-15 min      | $80 vs $24 (+230%)     |
+----------+----------------+----------------+----------------+------------------------+
| LONDON   | 100 / $1.00    | 70 / $0.70     | 15-20 min      | $192 vs $30 (+546%)    |
+----------+----------------+----------------+----------------+------------------------+
| NEW YORK | 100 / $1.00    | 70 / $0.70     | 15-20 min      | $64 vs $39 (+67%)      |
+----------+----------------+----------------+----------------+------------------------+

TRAILING STOP LOGIC:
1. Let position run to Trail Start (40 or 100 pts)
2. Activate trailing stop at Trail Distance (30 or 70 pts)
3. Trail follows price, maintaining distance
4. Exit when price reverses by Trail Distance

WHY TRAILING WINS:
- Captures momentum beyond fixed targets
- Adapts to volatility (wins bigger in volatile sessions)
- Lets winners run while protecting profits
""")

print("="*120)
print("PART 4: PROGRESSIVE APPROACH (BEST OF BOTH WORLDS)")
print("="*120)

print("""
STAGE 1 - Capital Protection:
  ASIA:   At +30 pts profit -> Move SL to breakeven
  LON/NY: At +50 pts profit -> Move SL to breakeven
  
STAGE 2 - Profit Lock:
  ASIA:   At +40 pts profit -> Trail 30 pts
  LON/NY: At +100 pts profit -> Trail 70 pts
  
STAGE 3 - Time Exit (if not stopped):
  ASIA:   Exit at 10-15 minutes if still open
  LON/NY: Exit at 15-20 minutes if still open

This approach:
- Protects capital early (breakeven at 30-50 pts)
- Captures big moves (trailing allows 80-250+ pts)
- Prevents excessive hold time (time-based exit)
""")

print("="*120)
print("PART 5: QUICK REFERENCE TABLE")
print("="*120)

print("""
+----------------------+------------------+------------------+------------------+
| Parameter            | Asia             | London           | New York         |
+----------------------+------------------+------------------+------------------+
| SESSION TIME (UTC)   | 02:00-05:00      | 11:00-14:00      | 13:00-17:00      |
+----------------------+------------------+------------------+------------------+
| FIXED TP             | 80 pts ($0.80)   | 200 pts ($2.00)  | 200 pts ($2.00)  |
| (if using fixed)     | or 90-110 pts    | or 250 pts       | or 250 pts       |
+----------------------+------------------+------------------+------------------+
| TIME CUTOFF          | 5 minutes        | 5 minutes        | 5 minutes        |
| (for fixed TP)       |                  |                  |                  |
+----------------------+------------------+------------------+------------------+
| TRAIL START          | 40 pts ($0.40)   | 100 pts ($1.00)  | 100 pts ($1.00)  |
| (activate trailing)  |                  |                  |                  |
+----------------------+------------------+------------------+------------------+
| TRAIL DISTANCE       | 30 pts ($0.30)   | 70 pts ($0.70)   | 70 pts ($0.70)   |
| (maintain behind)    |                  |                  |                  |
+----------------------+------------------+------------------+------------------+
| BREAKEVEN TRIGGER    | 30 pts           | 50 pts           | 50 pts           |
| (move SL to entry)   |                  |                  |                  |
+----------------------+------------------+------------------+------------------+
| EXPECTED PERFORMANCE | $80 (trailing)   | $192 (trailing)  | $64 (trailing)   |
|                      | vs $24 (fixed)   | vs $30 (fixed)   | vs $39 (fixed)   |
+----------------------+------------------+------------------+------------------+
""")

print("="*120)
print("PART 6: DECISION FLOWCHART")
print("="*120)

print("""
START: Which session?
  |
  +-- ASIA (02-05 UTC) ----> Use TP 80-110 OR Trail Start 40 / Distance 30
  |
  +-- LONDON (11-14 UTC) --> Use TP 200-250 OR Trail Start 100 / Distance 70
  |
  +-- NEW YORK (13-17 UTC) -> Use TP 200-250 OR Trail Start 100 / Distance 70

Prefer trailing stop in ALL sessions (+67% to +546% better than fixed TP)

Only use fixed TP if:
  - Platform has poor trailing stop execution
  - You need predictable position sizing
  - Managing 100+ positions simultaneously
""")

print("="*120)
print("END OF SUMMARY")
print("="*120)
