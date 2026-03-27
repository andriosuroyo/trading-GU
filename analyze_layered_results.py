"""Analyze Layered Recovery Simulation Results"""
import pandas as pd

df = pd.read_csv('data/LayeredRecovery_Simulation.csv')

print('='*100)
print('LAYERED RECOVERY SIMULATION - DETAILED ANALYSIS')
print('='*100)
print(f'Total losses simulated: {len(df)}')
print(f'Configuration: ATR x2.0 multiplier')
print()

# Filter out 0-layer positions (no entry triggered)
df_with_layers = df[df['NumLayers'] > 0]
print(f'Positions with at least 1 layer: {len(df_with_layers)} ({len(df_with_layers)/len(df)*100:.1f}%)')
print(f'Positions with no entry (0 layers): {len(df[df["NumLayers"] == 0])}')
print()

# Layer distribution
print('LAYER DISTRIBUTION:')
layer_dist = df['NumLayers'].value_counts().sort_index()
for layers, count in layer_dist.items():
    pct = count / len(df) * 100
    print(f'  {layers} layers: {count:3d} positions ({pct:5.1f}%)')

print(f'\nMaximum layers observed: {df["NumLayers"].max()}')

# By outcome (only positions with layers)
print('\n' + '='*100)
print('OUTCOME ANALYSIS (positions with >=1 layer)')
print('='*100)

recovered = df_with_layers[df_with_layers['Outcome'] == 'RECOVERED']
lost = df_with_layers[df_with_layers['Outcome'] == 'LOST']

print(f'\nRECOVERED: {len(recovered)} positions ({len(recovered)/len(df_with_layers)*100:.1f}%)')
print(f'  Max layers: {recovered["NumLayers"].max()}')
print(f'  Avg layers: {recovered["NumLayers"].mean():.2f}')

print(f'\nLOST: {len(lost)} positions ({len(lost)/len(df_with_layers)*100:.1f}%)')
print(f'  Max layers: {lost["NumLayers"].max()}')
print(f'  Avg layers: {lost["NumLayers"].mean():.2f}')

# Total profit potential
print('\n' + '='*100)
print('PROFIT POTENTIAL')
print('='*100)

total_potential = df_with_layers['TotalPotential'].sum()
print(f'Total potential profit (all layers): {total_potential:,.0f} points')
print(f'Average per position: {df_with_layers["TotalPotential"].mean():.0f} points')

rec_potential = recovered['TotalPotential'].sum()
lost_potential = lost['TotalPotential'].sum()
print(f'\nRecovered positions potential: {rec_potential:,.0f} points')
print(f'Lost positions potential: {lost_potential:,.0f} points')

# MAE Analysis
print('\n' + '='*100)
print('MAE ANALYSIS (Maximum Adverse Excursion)')
print('='*100)

print('\nOverall MAE statistics:')
print(f'  Mean Max MAE: {df_with_layers["MaxMAE"].mean():.0f} points')
print(f'  Median Max MAE: {df_with_layers["MaxMAE"].median():.0f} points')
print(f'  Overall Max MAE: {df_with_layers["MaxMAE"].max():.0f} points')
print(f'  95th percentile: {df_with_layers["MaxMAE"].quantile(0.95):.0f} points')

print('\nMAE by outcome:')
print(f'  RECOVERED - Mean: {recovered["MaxMAE"].mean():.0f}, Max: {recovered["MaxMAE"].max():.0f}')
print(f'  LOST - Mean: {lost["MaxMAE"].mean():.0f}, Max: {lost["MaxMAE"].max():.0f}')

print('\nMAE by layer count:')
for layers in sorted(df_with_layers['NumLayers'].unique()):
    subset = df_with_layers[df_with_layers['NumLayers'] == layers]
    print(f'  {layers} layer(s): Mean={subset["MaxMAE"].mean():.0f}, Max={subset["MaxMAE"].max():.0f}')

# Show worst MAE cases
print('\n' + '='*100)
print('WORST 5 MAE CASES:')
print('='*100)
worst = df_with_layers.nlargest(5, 'MaxMAE')[['Date', 'Ticket', 'NumLayers', 'MaxMAE', 'TotalPotential', 'Outcome']]
print(worst.to_string(index=False))
