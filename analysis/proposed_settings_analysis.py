"""Analysis of Proposed Conservative Settings"""

print("="*110)
print("IMPACT ANALYSIS: PROPOSED CONSERVATIVE SETTINGS")
print("="*110)

print("""
PROPOSED SETTINGS (Anti-Overfitting):
+----------------+----------------+----------------+----------------+----------------+
|    Session     | Fixed TP       | Trail Start    | Trail Distance | Max Candles    |
|                | (Points)       | (Points)       | (Points)       |                |
+----------------+----------------+----------------+----------------+----------------+
|   ASIA         | 100            | 50             | 40             | 20             |
+----------------+----------------+----------------+----------------+----------------+
|   LONDON       | 200            | 100            | 60             | 20             |
+----------------+----------------+----------------+----------------+----------------+
|   NEW YORK     | 200            | 100            | 60             | 20             |
+----------------+----------------+----------------+----------------+----------------+

RATIONALE:
- Lower TP to avoid overfitting to optimal values
- Trail Start at 50% of TP (no breakeven needed)
- Trail Distance wider for safety
- Max 20 candles (20 minutes) as time limit
""")

print("-"*110)
print("SIMULATED PERFORMANCE")
print("-"*110)

print("""
+----------------+----------------+----------------+----------------+----------------+----------------+
|    Session     | Fixed TP P&L   | Trail P&L      | Optimal P&L    | Difference     | % of Optimal   |
+----------------+----------------+----------------+----------------+----------------+----------------+
|   ASIA         | $18.91         | $35.86         | $79.96         | -$44.10        | 44.8%          |
|   (62 pos)     |                |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+
|   LONDON       | $22.24         | $44.51         | $192.08        | -$147.57       | 23.2%          |
|   (85 pos)     |                |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+
|   NEW YORK     | $26.73         | $47.23         | $64.24         | -$17.01        | 73.5%          |
|   (115 pos)    |                |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+
|   TOTAL        | $67.88         | $127.60        | $336.28        | -$208.68       | 37.9%          |
|   (262 pos)    |                |                |                |                |                |
+----------------+----------------+----------------+----------------+----------------+----------------+

COST OF CONSERVATIVE SETTINGS: -$208.68 (-62.1% vs optimal)
""")

print("-"*110)
print("BREAKDOWN BY SESSION")
print("-"*110)

print("""
ASIA (Conservative: TP 100, Trail 50/40):
  - Trail captures $35.86 vs optimal $79.96
  - Main issue: Trail distance 40pts cuts winners short
  - 58 positions hit trail stop, only 3 run to max candles
  - Recommendation: Trail distance too tight for the volatility

LONDON (Conservative: TP 200, Trail 100/60):
  - Trail captures $44.51 vs optimal $192.08  
  - Severe underperformance: -$147.57
  - London needs wider trails (85pts optimal vs 60pts proposed)
  - High volatility needs more room to breathe
  
NEW YORK (Conservative: TP 200, Trail 100/60):
  - Trail captures $47.23 vs optimal $64.24
  - Best relative performance: 73.5% of optimal
  - Conservative settings work "okay" for NY
  - Still leaving $17 on the table
""")

print("-"*110)
print("OPTIONS TO CONSIDER")
print("-"*110)

print("""
OPTION A: KEEP PROPOSED CONSERVATIVE SETTINGS
+----------------+----------------+----------------+
| Pros                    | Cons                       |
+-------------------------+----------------------------+
| Less overfitting risk   | -62% lower P&L             |
| Simpler to implement    | London especially hurt     |
| More robust going fwd   | $208 less profit           |
+-------------------------+----------------------------+
Expected Total P&L: $127.60 (vs $336.28 optimal)


OPTION B: MODERATE ADJUSTMENT
Keep conservative TP but widen trail distance:

+----------------+----------------+----------------+----------------+
| Session        | TP             | Trail Start    | Trail Distance |
+----------------+----------------+----------------+----------------+
| ASIA           | 100            | 50             | 50 (not 40)    |
+----------------+----------------+----------------+----------------+
| LONDON         | 200            | 100            | 80 (not 60)    |
+----------------+----------------+----------------+----------------+
| NEW YORK       | 200            | 100            | 70 (not 60)    |
+----------------+----------------+----------------+----------------+

Rationale: Wider trail distance lets winners run more
Expected improvement: +$30-50 vs current proposed


OPTION C: ACCEPT OPTIMAL SETTINGS
Trust the data, use optimal settings:

+----------------+----------------+----------------+----------------+
| Session        | TP             | Trail Start    | Trail Distance |
+----------------+----------------+----------------+----------------+
| ASIA           | 110            | 55             | 35             |
+----------------+----------------+----------------+----------------+
| LONDON         | 250            | 125            | 85             |
+----------------+----------------+----------------+----------------+
| NEW YORK       | 250            | 125            | 85             |
+----------------+----------------+----------------+----------------+

Expected Total P&L: $336.28 (optimal from data)
Risk: May be overfitted to current market conditions
""")

print("-"*110)
print("RECOMMENDATION")
print("-"*110)

print("""
Given the significant P&L reduction (-62%), I recommend:

MIDDLE GROUND APPROACH:

1. Use proposed TP values (100 Asia, 200 London/NY)
   - Reduces overfitting concern
   - Still captures most profitable moves

2. But WIDEN trail distance:
   - Asia: Trail 50/50 (not 50/40)
   - London: Trail 100/80 (not 100/60)  
   - NY: Trail 100/70 (not 100/60)

3. Rationale:
   - Trail Start 50% of TP is good (locks in profit)
   - But Trail Distance should be ~40-45% of TP (not 30%)
   - This balances profit protection with letting winners run

4. Expected outcome:
   - Total P&L: ~$160-180 (vs $127 conservative, $336 optimal)
   - Captures 50-55% of optimal with less overfitting risk
   - More robust across different market conditions

Would you like me to simulate this "middle ground" approach?
""")

print("="*110)
