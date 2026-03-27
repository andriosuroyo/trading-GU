"""Print extended summary"""
import pandas as pd

# Data from the analysis
data = [
    ('1min', 36, 63, '36.4%', -2111, -21.3, 241, 263),
    ('2min', 52, 47, '52.5%', 33, 0.3, 324, 383),
    ('3min', 58, 41, '58.6%', 251, 2.5, 382, 454),
    ('4min', 64, 35, '64.6%', 2825, 28.5, 460, 534),
    ('5min', 65, 34, '65.7%', 4204, 42.5, 486, 575),
    ('6min', 69, 30, '69.7%', 4176, 42.2, 521, 654),
    ('7min', 71, 28, '71.7%', 4269, 43.1, 577, 707),
    ('8min', 74, 25, '74.7%', 1772, 17.9, 637, 759),
    ('9min', 75, 24, '75.8%', 3921, 39.6, 688, 810),
    ('10min', 77, 22, '77.8%', 3856, 38.9, 754, 858),
    ('11min', 79, 20, '79.8%', 4995, 50.5, 800, 889),
    ('12min', 79, 20, '79.8%', 3755, 37.9, 830, 948),
    ('13min', 80, 19, '80.8%', 3931, 39.7, 879, 1003),
    ('14min', 80, 19, '80.8%', 3252, 32.8, 915, 1035),
    ('15min', 83, 16, '83.8%', 7052, 71.2, 952, 1064),
    ('16min', 83, 16, '83.8%', 6026, 60.9, 985, 1102),
    ('17min', 83, 16, '83.8%', 4326, 43.7, 1012, 1148),
    ('18min', 85, 14, '85.9%', 4273, 43.2, 1040, 1176),
    ('19min', 85, 14, '85.9%', 5383, 54.4, 1074, 1207),
    ('20min', 87, 12, '87.9%', 7576, 76.5, 1101, 1236),
    ('21min', 88, 11, '88.9%', 7503, 75.8, 1124, 1262),
    ('22min', 89, 10, '89.9%', 8790, 88.8, 1145, 1288),
    ('23min', 89, 10, '89.9%', 9025, 91.2, 1163, 1316),
    ('24min', 89, 10, '89.9%', 8689, 87.8, 1181, 1343),
    ('25min', 89, 10, '89.9%', 8714, 88.0, 1198, 1371),
    ('26min', 90, 9, '90.9%', 9699, 98.0, 1217, 1399),
    ('27min', 90, 9, '90.9%', 10867, 109.8, 1236, 1426),
    ('28min', 90, 9, '90.9%', 11741, 118.6, 1257, 1452),
    ('29min', 90, 9, '90.9%', 11296, 114.1, 1275, 1477),
    ('30min', 90, 9, '90.9%', 10337, 104.4, 1292, 1501),
]

columns = ['TimeWindow', 'Profit', 'Loss', 'WinRate', 'TotalOutcomePts', 'AvgOutcomePts', 'AvgMFE', 'AvgMAE']
summary_df = pd.DataFrame(data, columns=columns)

print("=" * 100)
print("EXTENDED TIME WINDOW ANALYSIS - 1min to 30min")
print("=" * 100)
print(summary_df.to_string(index=False))

# Find best
best_total_idx = summary_df['TotalOutcomePts'].idxmax()
best_total = summary_df.iloc[best_total_idx]

print()
print("=" * 100)
print("OPTIMAL CUTOFF ANALYSIS")
print("=" * 100)
print("Best Total Outcome: {} with {:,} points".format(best_total['TimeWindow'], best_total['TotalOutcomePts']))
print("Win Rate at {}: {}".format(best_total['TimeWindow'], best_total['WinRate']))
print("Avg per Trade: {} points".format(best_total['AvgOutcomePts']))

# 15min vs extended
min15_total = summary_df[summary_df['TimeWindow'] == '15min']['TotalOutcomePts'].values[0]
min28_total = summary_df[summary_df['TimeWindow'] == '28min']['TotalOutcomePts'].values[0]

print()
print("=" * 100)
print("15MIN vs EXTENDED COMPARISON")
print("=" * 100)
print("15min Total: {:,} points".format(min15_total))
print("28min Total: {:,} points".format(min28_total))
print("Difference: +{:,} points (28min is {:.1f}% better)".format(
    min28_total - min15_total, 
    ((min28_total/min15_total - 1) * 100)
))

print()
print("=" * 100)
print("KEY FINDINGS")
print("=" * 100)
print("1. The 15min result was NOT an outlier")
print("2. Performance continues to improve through 28min")
print("3. Win rate increases steadily: 83.8% (15min) -> 90.9% (26-30min)")
print("4. Peak performance at 28min with +11,741 points")
print("5. Returns plateau and decline slightly after 28min")
print()
print("RECOMMENDATION: Consider 26-28 minute FullClose for maximum outcome")
print("  - 26min: +9,699 points, 90.9% win rate")
print("  - 27min: +10,867 points, 90.9% win rate")  
print("  - 28min: +11,741 points, 90.9% win rate (PEAK)")
