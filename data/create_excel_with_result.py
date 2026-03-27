"""Create Excel with RESULT sheet at front and all minute sheets"""
import pandas as pd

# Summary data
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

# Add findings section as additional rows
findings_data = [
    ('', '', '', '', '', '', '', ''),
    ('KEY FINDINGS', '', '', '', '', '', '', ''),
    ('', '', '', '', '', '', '', ''),
    ('1. Peak Performance:', '28min', '', '', '+11,741 pts', '118.6 avg', '90.9% WR', ''),
    ('2. 15min was NOT outlier', 'Continues improving', '', '', '', '', '', ''),
    ('3. Win rate progression:', '83.8% (15min)', '-> 90.9% (26-30min)', '', '', '', '', ''),
    ('4. Recommendation:', '26-28 min FullClose', '', '', '', '', '', ''),
    ('', '', '', '', '', '', '', ''),
    ('OPTIMAL TIME WINDOWS:', '', '', '', '', '', '', ''),
    ('Conservative:', '5min', '', '', '+4,204 pts', '42.5 avg', '65.7% WR', ''),
    ('Balanced:', '11min', '', '', '+4,995 pts', '50.5 avg', '79.8% WR', ''),
    ('Aggressive:', '15min', '', '', '+7,052 pts', '71.2 avg', '83.8% WR', ''),
    ('Maximum:', '28min', '', '', '+11,741 pts', '118.6 avg', '90.9% WR', ''),
]

findings_df = pd.DataFrame(findings_data, columns=columns)

# Combine
result_sheet = pd.concat([summary_df, findings_df], ignore_index=True)

# Read existing data from individual sheets if available
try:
    old_xl = pd.ExcelFile('data/Analysis_20260320.xlsx')
    old_sheets = {sheet: pd.read_excel(old_xl, sheet_name=sheet) for sheet in old_xl.sheet_names}
except:
    old_sheets = {}

# Write new Excel
output_file = 'data/Analysis_20260320_Final.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Write RESULT sheet first
    result_sheet.to_excel(writer, sheet_name='RESULT', index=False)
    
    # Write individual minute sheets (1-15 from old file if available)
    for minutes in range(1, 31):
        sheet_name = f'{minutes}min'
        if sheet_name in old_sheets:
            old_sheets[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)

print("Excel file created: {}".format(output_file))
print("Contains:")
print("  - RESULT sheet (at front) with summary of all 30 time windows")
print("  - Individual sheets: 1min through 30min")
print()
print("RESULT Sheet Preview:")
print(summary_df.head(15).to_string(index=False))
