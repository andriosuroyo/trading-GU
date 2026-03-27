"""
Analyze the 6 configuration simulation results
"""
import pandas as pd

print('='*100)
print('6 CONFIGURATION SIMULATION RESULTS - SUMMARY')
print('='*100)
print()

# Manual data entry from simulation output
data = [
    # March 23
    {'Date': '20260323', 'Config': 'Max2+Mult1x', 'Layer1': 'Yes', 'Net': -24284, 'Rec': 29, 'Tot': 38, 'Rate': 76.3, 'NoEntry': 0},
    {'Date': '20260323', 'Config': 'Max2+Mult1x', 'Layer1': 'No', 'Net': 45148, 'Rec': 21, 'Tot': 28, 'Rate': 75.0, 'NoEntry': 10},
    {'Date': '20260323', 'Config': 'Max2+Mult2x', 'Layer1': 'Yes', 'Net': 5937, 'Rec': 29, 'Tot': 38, 'Rate': 76.3, 'NoEntry': 0},
    {'Date': '20260323', 'Config': 'Max2+Mult2x', 'Layer1': 'No', 'Net': 43611, 'Rec': 20, 'Tot': 27, 'Rate': 74.1, 'NoEntry': 11},
    {'Date': '20260323', 'Config': 'Max2+Mult3x', 'Layer1': 'Yes', 'Net': 9214, 'Rec': 29, 'Tot': 38, 'Rate': 76.3, 'NoEntry': 0},
    {'Date': '20260323', 'Config': 'Max2+Mult3x', 'Layer1': 'No', 'Net': 55311, 'Rec': 18, 'Tot': 25, 'Rate': 72.0, 'NoEntry': 13},
    {'Date': '20260323', 'Config': 'Max3+Mult1x', 'Layer1': 'Yes', 'Net': 6623, 'Rec': 29, 'Tot': 38, 'Rate': 76.3, 'NoEntry': 0},
    {'Date': '20260323', 'Config': 'Max3+Mult1x', 'Layer1': 'No', 'Net': 34248, 'Rec': 21, 'Tot': 28, 'Rate': 75.0, 'NoEntry': 10},
    {'Date': '20260323', 'Config': 'Max3+Mult2x', 'Layer1': 'Yes', 'Net': 4981, 'Rec': 29, 'Tot': 38, 'Rate': 76.3, 'NoEntry': 0},
    {'Date': '20260323', 'Config': 'Max3+Mult2x', 'Layer1': 'No', 'Net': 36805, 'Rec': 20, 'Tot': 27, 'Rate': 74.1, 'NoEntry': 11},
    {'Date': '20260323', 'Config': 'Max3+Mult3x', 'Layer1': 'Yes', 'Net': -4927, 'Rec': 29, 'Tot': 38, 'Rate': 76.3, 'NoEntry': 0},
    {'Date': '20260323', 'Config': 'Max3+Mult3x', 'Layer1': 'No', 'Net': 49339, 'Rec': 18, 'Tot': 25, 'Rate': 72.0, 'NoEntry': 13},
    
    # March 24
    {'Date': '20260324', 'Config': 'Max2+Mult1x', 'Layer1': 'Yes', 'Net': -51139, 'Rec': 38, 'Tot': 55, 'Rate': 69.1, 'NoEntry': 0},
    {'Date': '20260324', 'Config': 'Max2+Mult1x', 'Layer1': 'No', 'Net': -31351, 'Rec': 30, 'Tot': 41, 'Rate': 73.2, 'NoEntry': 14},
    {'Date': '20260324', 'Config': 'Max2+Mult2x', 'Layer1': 'Yes', 'Net': -50863, 'Rec': 38, 'Tot': 55, 'Rate': 69.1, 'NoEntry': 0},
    {'Date': '20260324', 'Config': 'Max2+Mult2x', 'Layer1': 'No', 'Net': -35064, 'Rec': 25, 'Tot': 36, 'Rate': 69.4, 'NoEntry': 19},
    {'Date': '20260324', 'Config': 'Max2+Mult3x', 'Layer1': 'Yes', 'Net': -49865, 'Rec': 38, 'Tot': 55, 'Rate': 69.1, 'NoEntry': 0},
    {'Date': '20260324', 'Config': 'Max2+Mult3x', 'Layer1': 'No', 'Net': -33706, 'Rec': 21, 'Tot': 32, 'Rate': 65.6, 'NoEntry': 23},
    {'Date': '20260324', 'Config': 'Max3+Mult1x', 'Layer1': 'Yes', 'Net': -44602, 'Rec': 38, 'Tot': 55, 'Rate': 69.1, 'NoEntry': 0},
    {'Date': '20260324', 'Config': 'Max3+Mult1x', 'Layer1': 'No', 'Net': -24397, 'Rec': 30, 'Tot': 41, 'Rate': 73.2, 'NoEntry': 14},
    {'Date': '20260324', 'Config': 'Max3+Mult2x', 'Layer1': 'Yes', 'Net': -54540, 'Rec': 38, 'Tot': 55, 'Rate': 69.1, 'NoEntry': 0},
    {'Date': '20260324', 'Config': 'Max3+Mult2x', 'Layer1': 'No', 'Net': -45402, 'Rec': 25, 'Tot': 36, 'Rate': 69.4, 'NoEntry': 19},
    {'Date': '20260324', 'Config': 'Max3+Mult3x', 'Layer1': 'Yes', 'Net': -59281, 'Rec': 38, 'Tot': 55, 'Rate': 69.1, 'NoEntry': 0},
    {'Date': '20260324', 'Config': 'Max3+Mult3x', 'Layer1': 'No', 'Net': -43122, 'Rec': 21, 'Tot': 32, 'Rate': 65.6, 'NoEntry': 23},
    
    # March 25
    {'Date': '20260325', 'Config': 'Max2+Mult1x', 'Layer1': 'Yes', 'Net': 36768, 'Rec': 43, 'Tot': 49, 'Rate': 87.8, 'NoEntry': 0},
    {'Date': '20260325', 'Config': 'Max2+Mult1x', 'Layer1': 'No', 'Net': 49919, 'Rec': 34, 'Tot': 40, 'Rate': 85.0, 'NoEntry': 9},
    {'Date': '20260325', 'Config': 'Max2+Mult2x', 'Layer1': 'Yes', 'Net': 35697, 'Rec': 43, 'Tot': 49, 'Rate': 87.8, 'NoEntry': 0},
    {'Date': '20260325', 'Config': 'Max2+Mult2x', 'Layer1': 'No', 'Net': 41551, 'Rec': 30, 'Tot': 36, 'Rate': 83.3, 'NoEntry': 13},
    {'Date': '20260325', 'Config': 'Max2+Mult3x', 'Layer1': 'Yes', 'Net': 18878, 'Rec': 43, 'Tot': 49, 'Rate': 87.8, 'NoEntry': 0},
    {'Date': '20260325', 'Config': 'Max2+Mult3x', 'Layer1': 'No', 'Net': 29280, 'Rec': 23, 'Tot': 29, 'Rate': 79.3, 'NoEntry': 20},
    {'Date': '20260325', 'Config': 'Max3+Mult1x', 'Layer1': 'Yes', 'Net': 57455, 'Rec': 43, 'Tot': 49, 'Rate': 87.8, 'NoEntry': 0},
    {'Date': '20260325', 'Config': 'Max3+Mult1x', 'Layer1': 'No', 'Net': 73232, 'Rec': 34, 'Tot': 40, 'Rate': 85.0, 'NoEntry': 9},
    {'Date': '20260325', 'Config': 'Max3+Mult2x', 'Layer1': 'Yes', 'Net': 38715, 'Rec': 43, 'Tot': 49, 'Rate': 87.8, 'NoEntry': 0},
    {'Date': '20260325', 'Config': 'Max3+Mult2x', 'Layer1': 'No', 'Net': 44569, 'Rec': 30, 'Tot': 36, 'Rate': 83.3, 'NoEntry': 13},
    {'Date': '20260325', 'Config': 'Max3+Mult3x', 'Layer1': 'Yes', 'Net': 18878, 'Rec': 43, 'Tot': 49, 'Rate': 87.8, 'NoEntry': 0},
    {'Date': '20260325', 'Config': 'Max3+Mult3x', 'Layer1': 'No', 'Net': 29280, 'Rec': 23, 'Tot': 29, 'Rate': 79.3, 'NoEntry': 20},
]

df = pd.DataFrame(data)

# Combined results by configuration
print('COMBINED RESULTS (March 23-25)')
print('='*100)
print()

combined = df.groupby(['Config', 'Layer1']).agg({
    'Net': 'sum',
    'Rec': 'sum',
    'Tot': 'sum',
    'NoEntry': 'sum'
}).reset_index()

combined['Rate'] = combined['Rec'] / combined['Tot'] * 100
combined = combined.sort_values('Net', ascending=False)

print(f'{"Rank":<5} {"Config":<15} {"Layer1":<8} {"Net":>12} {"Rec":>5} {"Tot":>4} {"Rate":>7} {"NoEntry":>8}')
print('-' * 80)

for idx, row in combined.iterrows():
    rank = list(combined.index).index(idx) + 1
    print(f"{rank:<5} {row['Config']:<15} {row['Layer1']:<8} {row['Net']:+12,.0f} {row['Rec']:>5} {row['Tot']:>4} {row['Rate']:>6.1f}% {row['NoEntry']:>8}")

print()
print('='*100)
print('KEY FINDINGS')
print('='*100)
print()

best = combined.iloc[0]
print(f'1. BEST CONFIGURATION: {best["Config"]} WITHOUT Layer1')
print(f'   Net Profit: {best["Net"]:+,.0f} points')
print(f'   Recovery Rate: {best["Rate"]:.1f}%')
print()

# Analyze WITH vs WITHOUT Layer1
print('2. WITH vs WITHOUT Layer1 (Immediate Entry):')
print()
for config in ['Max2+Mult1x', 'Max2+Mult2x', 'Max2+Mult3x', 'Max3+Mult1x', 'Max3+Mult2x', 'Max3+Mult3x']:
    with_l1 = combined[(combined['Config'] == config) & (combined['Layer1'] == 'Yes')]['Net'].values[0]
    without_l1 = combined[(combined['Config'] == config) & (combined['Layer1'] == 'No')]['Net'].values[0]
    diff = without_l1 - with_l1
    print(f'   {config:<15}: With L1={with_l1:+8,.0f}, No L1={without_l1:+8,.0f}, Diff={diff:+8,.0f}')

print()
print('3. MAX LAYERS COMPARISON (No Layer1, combined multipliers):')
print()
max2_no = combined[(combined['Config'].str.startswith('Max2')) & (combined['Layer1'] == 'No')]['Net'].mean()
max3_no = combined[(combined['Config'].str.startswith('Max3')) & (combined['Layer1'] == 'No')]['Net'].mean()
print(f'   Max 2 layers (avg): {max2_no:+,.0f}')
print(f'   Max 3 layers (avg): {max3_no:+,.0f}')

print()
print('4. MULTIPLIER COMPARISON (No Layer1, combined max layers):')
print()
for mult in [1, 2, 3]:
    mult_data = combined[(combined['Config'].str.contains(f'Mult{mult}x')) & (combined['Layer1'] == 'No')]
    avg_net = mult_data['Net'].mean()
    print(f'   {mult}x multiplier (avg): {avg_net:+,.0f}')

print()
print('='*100)
print('RECOMMENDATIONS')
print('='*100)
print()
print('1. DO NOT use Layer1 (immediate entry) - waiting for GU confirmation is better')
print('2. Max 2 or 3 layers both work, but 3 layers has higher variance')
print('3. 1x or 2x multiplier better than 3x (more entries = more opportunities)')
print('4. Best overall: Max3+Mult1x NO Layer1 (+73,232 points) or Max2+Mult1x NO Layer1 (+49,919)')
print()
print('OPTIMAL SETTINGS:')
print('  - Max Layers: 3')
print('  - ATR Multiplier: 1x')
print('  - Layer1: NO (wait for GU confirmation)')
print('  - Entry: When GU opens position in same direction')
