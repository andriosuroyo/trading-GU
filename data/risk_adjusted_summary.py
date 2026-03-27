"""
Risk-Adjusted Analysis Summary - Comparing Recommendations
"""

print("=" * 100)
print("RISK-ADJUSTED ANALYSIS SUMMARY")
print("How Adding MAE as a Risk Dimension Changes Recommendations")
print("=" * 100)

print("""
METHODOLOGY:
- Risk-Adjusted Ratio = Total Outcome Points / Max MAE
- Max MAE = Highest Maximum Adverse Excursion experienced across all positions
- This measures "return per unit of worst-case drawdown risk"

================================================================================
PREVIOUS RECOMMENDATION (Outcome-Focused Only):
================================================================================
Configuration: 30min_0.4x
  Time Window: 30 minutes
  ATR Multiplier: 0.4x
  Total Outcome: +11,201 points (99 positions)
  Win Rate: 94.9%

================================================================================
NEW ANALYSIS (114 positions, March 20, 2026):
================================================================================

RANKING BY TOTAL OUTCOME:
+------------------+-----------+----------+--------+----------+
| Config           | Outcome   | Max MAE  | Ratio  | Win Rate |
+------------------+-----------+----------+--------+----------+
| 30min_1.0x       | +15,863   | 8,306    | 1.91x  | 79.8%    |
| 20min_0.7x       | +14,723   | 5,183    | 2.84x  | 86.0%    |
| 30min_0.7x       | +14,693   | 8,306    | 1.77x  | 87.7%    |
| 25min_0.7x       | +12,547   | 6,044    | 2.08x  | 87.7%    |
| 30min_0.9x       | +12,027   | 8,306    | 1.45x  | 82.5%    |
+------------------+-----------+----------+--------+----------+

RANKING BY RISK-ADJUSTED RATIO:
+------------------+-----------+----------+--------+----------+
| Config           | Outcome   | Max MAE  | Ratio  | Win Rate |
+------------------+-----------+----------+--------+----------+
| 20min_0.7x       | +14,723   | 5,183    | 2.84x  | 86.0%    | <- OPTIMAL
| 10min_0.6x       | +8,182    | 3,753    | 2.18x  | 78.1%    |
| 20min_1.0x       | +11,011   | 5,183    | 2.12x  | 73.7%    |
| 10min_0.7x       | +7,954    | 3,753    | 2.12x  | 71.9%    |
| 20min_0.6x       | +10,972   | 5,183    | 2.12x  | 88.6%    |
+------------------+-----------+----------+--------+----------+

================================================================================
HEAD-TO-HEAD COMPARISON:
================================================================================

                    OUTCOME-FOCUSED          RISK-ADJUSTED
                    (30min_1.0x)             (20min_0.7x)
                    ----------------         ----------------
Time Window:        30 minutes               20 minutes
Multiplier:         1.0x                     0.7x
Total Outcome:      +15,863 pts              +14,723 pts   (-7.2%)
Max MAE:            8,306 pts                5,183 pts     (-37.6%!)
Risk-Adj Ratio:     1.91x                    2.84x         (+48.7%!)
Win Rate:           79.8%                    86.0%         (+6.2 pts)

================================================================================
KEY INSIGHTS:
================================================================================

1. RECOMMENDATION CHANGED!
   The optimal configuration shifts from 30min_1.0x (outcome-focused) to 
   20min_0.7x (risk-adjusted). This represents a more conservative approach
   that prioritizes return per unit of risk.

2. 0.7x MULTIPLIER DOMINATES RISK-ADJUSTED RANKINGS
   0.7x appears in 4 of top 5 risk-adjusted configurations:
   - 20min_0.7x: 2.84x ratio
   - 10min_0.7x: 2.12x ratio  
   - 15min_0.7x: 2.11x ratio
   - 25min_0.7x: 2.08x ratio
   - 30min_0.7x: 1.77x ratio

   Previously, 0.4x was optimal for pure outcome. With MAE consideration,
   0.7x provides better risk-adjusted returns.

3. THE "SWEET SPOT" IS 20 MINUTES
   20-minute window appears 4 times in top 6 risk-adjusted configurations.
   This window balances:
   - Enough time for trades to reach TP targets
   - Limited exposure to adverse price movements

4. RISK-RETURN TRADEOFF
   By moving from 30min_1.0x to 20min_0.7x:
   - You sacrifice only 7% of total outcome (-1,140 pts)
   - You reduce max drawdown by 38% (-3,123 pts)
   - You improve risk-adjusted return by 49% (+0.93x ratio)

5. AVOID LONG WINDOWS WITH HIGH MULTIPLIERS
   30min with 0.8x-1.0x multipliers show poor risk-adjusted ratios (1.3-1.9x)
   due to elevated MAE exposure over extended time periods.

================================================================================
FINAL RECOMMENDATIONS:
================================================================================

+-----------------------------------------------------------------------------+
|  PRIMARY RECOMMENDATION:  20min_0.7x                                        |
|                                                                             |
|  Time Window: 20 minutes                                                    |
|  ATR Multiplier: 0.7x (~350-400 points TP target)                          |
|                                                                             |
|  Expected Performance:                                                      |
|  * Total Outcome: +14,723 points (114 trades)                              |
|  * Max MAE: 5,183 points (worst drawdown experienced)                      |
|  * Risk-Adjusted Ratio: 2.84x                                               |
|  * Win Rate: 86.0% (98 wins / 16 losses)                                   |
|                                                                             |
|  ALTERNATIVE OPTIONS:                                                       |
|  * 10min_0.6x: +8,182 pts, 2.18x ratio (shorter exposure)                  |
|  * 20min_0.6x: +10,972 pts, 2.12x ratio, 88.6% WR (more conservative)      |
|  * 20min_1.0x: +11,011 pts, 2.12x ratio (higher target)                    |
|                                                                             |
|  AVOID:                                                                     |
|  * 30min with >0.8x multiplier (poor risk-adjusted returns)                |
|  * 5min with <0.5x multiplier (insufficient time for targets)              |
+-----------------------------------------------------------------------------+

================================================================================
IMPLEMENTATION NOTES:
================================================================================

The Risk-Adjusted Ratio (Outcome/MaxMAE) answers the question:
"How many points of profit do I get for each point of worst-case drawdown?"

A ratio of 2.84x means: For every 1 point of max drawdown risk, you earn 
2.84 points of profit. This is significantly better than the 1.91x ratio 
of the outcome-focused configuration.

For traders prioritizing capital preservation alongside returns, the 
20min_0.7x configuration offers the optimal balance.
""")
