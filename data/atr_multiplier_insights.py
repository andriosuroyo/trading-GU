"""
ATR Multiplier Analysis - Key Insights and Recommendations
"""
import pandas as pd

# Load the summary data
data = [
    ('0.2x', 99, 94, 5, '94.9%', 5351, 54.1),
    ('0.3x', 149, 91, 8, '91.9%', 7088, 71.6),
    ('0.4x', 198, 87, 12, '87.9%', 8181, 82.6),
    ('0.5x', 248, 83, 16, '83.8%', 7052, 71.2),
    ('0.6x', 297, 76, 23, '76.8%', -1826, -18.4),
    ('0.7x', 347, 72, 27, '72.7%', -5493, -55.5),
    ('0.8x', 396, 70, 29, '70.7%', -2486, -25.1),
    ('0.9x', 446, 68, 31, '68.7%', -874, -8.8),
    ('1.0x', 495, 64, 35, '64.6%', 142, 1.4),
    ('1.1x', 545, 63, 36, '63.6%', 2707, 27.3),
    ('1.2x', 594, 59, 40, '59.6%', 2864, 28.9),
    ('1.3x', 644, 55, 44, '55.6%', 1113, 11.2),
    ('1.4x', 693, 53, 46, '53.5%', 1634, 16.5),
    ('1.5x', 743, 51, 48, '51.5%', 2320, 23.4),
    ('1.6x', 793, 50, 49, '50.5%', 4281, 43.2),
    ('1.7x', 842, 47, 52, '47.5%', 4833, 48.8),
    ('1.8x', 892, 44, 55, '44.4%', 2888, 29.2),
    ('1.9x', 941, 41, 58, '41.4%', 2646, 26.7),
    ('2.0x', 991, 37, 62, '37.4%', 2698, 27.3),
    ('2.1x', 1040, 36, 63, '36.4%', 3625, 36.6),
    ('2.2x', 1090, 31, 68, '31.3%', 585, 5.9),
    ('2.3x', 1139, 31, 68, '31.3%', 2021, 20.4),
    ('2.4x', 1189, 30, 69, '30.3%', 1746, 17.6),
    ('2.5x', 1238, 29, 70, '29.3%', 3058, 30.9),
    ('2.6x', 1288, 27, 72, '27.3%', 2735, 27.6),
    ('2.7x', 1337, 25, 74, '25.3%', 3757, 37.9),
    ('2.8x', 1387, 22, 77, '22.2%', 3364, 34.0),
    ('2.9x', 1436, 22, 77, '22.2%', 4393, 44.4),
    ('3.0x', 1486, 20, 79, '20.2%', 5116, 51.7),
]

columns = ['Multiplier', 'ATRTP_Avg', 'ProfitCount', 'LossCount', 'WinRate', 'TotalOutcomePts', 'AvgOutcomePts']
df = pd.DataFrame(data, columns=columns)

print("=" * 90)
print("ATR MULTIPLIER ANALYSIS - KEY INSIGHTS (15min Window)")
print("=" * 90)

print("\n1. OPTIMAL MULTIPLIER IDENTIFIED:")
print("-" * 90)
print("   0.4x multiplier delivers the best performance:")
print("   - Total Outcome: +8,181 points (+16.0% vs baseline 0.5x)")
print("   - Win Rate: 87.9% (only 6% lower than baseline)")
print("   - Avg TP Target: 198 points (manageable)")
print("   - Profit/Loss: 87 wins, 12 losses")

print("\n2. THE 'DEAD ZONE' (0.6x - 0.9x):")
print("-" * 90)
print("   Multipliers in this range show NEGATIVE outcomes:")
print("   - 0.6x: -1,826 points (76.8% WinRate)")
print("   - 0.7x: -5,493 points (72.7% WinRate) <- WORST")
print("   - 0.8x: -2,486 points (70.7% WinRate)")
print("   - 0.9x: -874 points (68.7% WinRate)")
print("   \n   This suggests the targets are too ambitious for the 15-min window")
print("   but not ambitious enough to capture big moves.")

print("\n3. EFFICIENCY FRONTIER:")
print("-" * 90)
print("   Sweet spot range: 0.3x to 0.5x")
print("   +--------------------------------+----------------+----------------+")
print("   | Multiplier                     | WinRate        | Total Outcome  |")
print("   +--------------------------------+----------------+----------------+")
print("   | 0.3x (Conservative)            | 91.9%          | +7,088         |")
print("   | 0.4x (OPTIMAL)                 | 87.9%          | +8,181         |")
print("   | 0.5x (Baseline)                | 83.8%          | +7,052         |")
print("   +--------------------------------+----------------+----------------+")

print("\n4. HIGH MULTIPLIER RECOVERY (1.5x - 3.0x):")
print("-" * 90)
print("   Interestingly, performance recovers at higher multipliers:")
print("   - 1.6x: +4,281 points (50.5% WinRate)")
print("   - 1.7x: +4,833 points (47.5% WinRate)")
print("   - 2.7x: +3,757 points (25.3% WinRate)")
print("   - 3.0x: +5,116 points (20.2% WinRate)")
print("   \n   But NEVER exceeds the 0.4x optimal point.")

print("\n5. TRADE-OFF CONFIRMED:")
print("-" * 90)
print("   Lower multipliers -> Higher WinRate, Lower per-trade profit")
print("   Higher multipliers -> Lower WinRate, Higher per-trade profit (if hit)")
print("   \n   The optimal balance is at 0.4x where:")
print("   - High enough win rate (87.9%) for consistency")
print("   - Large enough target (198 pts) for meaningful returns")
print("   - Maximum total outcome (+8,181 pts)")

print("\n6. RECOMMENDATIONS:")
print("=" * 90)
print("   PRIMARY: Switch from 0.5x to 0.4x ATR multiplier")
print("            Expected gain: +1,129 points (+16.0%)")
print("   \n   CONSERVATIVE: Use 0.3x for higher win rate (91.9%)")
print("                 Trade-off: -1,093 points vs 0.4x")
print("   \n   AVOID: 0.6x - 0.9x range (the 'dead zone')")
print("   \n   AGGRESSIVE: Extended time window (26-28min) with 0.4x")
print("               Previously shown: +9,699 to +11,741 points")

print("\n" + "=" * 90)
print("CONCLUSION")
print("=" * 90)
print("The 0.5x baseline is close but not optimal.")
print("A slight reduction to 0.4x captures 16% more profit")
print("while maintaining a strong 87.9% win rate.")
print("=" * 90)
