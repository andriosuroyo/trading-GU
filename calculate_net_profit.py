"""
Calculate Net Profit Potential for Recovery Strategy
Net = Sum of LayerXPotential (Recovered=YES) - Sum of LayerXMAE (Recovered=NO)
Per day calculation
"""
import pandas as pd

print('='*100)
print('NET PROFIT POTENTIAL CALCULATION')
print('='*100)
print()
print('Formula:')
print('  Net = Sum(LayerXPotential for Recovered=YES)')
print('      - Sum(LayerXMAE for Recovered=NO)')
print()

dates = ['20260320', '20260323', '20260324', '20260325']

for date in dates:
    df = pd.read_excel(f'data/{date}_RecoveryAnalysis_FINAL.xlsx')
    
    print('='*100)
    print(f'{date}')
    print('='*100)
    
    # Recovered baskets - sum all layer potentials
    recovered_df = df[df['Recovered'] == 'YES']
    recovered_profit = 0
    
    for idx, row in recovered_df.iterrows():
        for i in range(1, int(row['NumLayers']) + 1):
            potential = row[f'Layer{i}Potential']
            if pd.notna(potential):
                recovered_profit += potential
    
    # Not recovered baskets - sum all layer MAEs (losses)
    not_recovered_df = df[df['Recovered'] == 'NO']
    not_recovered_loss = 0
    
    for idx, row in not_recovered_df.iterrows():
        for i in range(1, int(row['NumLayers']) + 1):
            mae = row[f'Layer{i}MAE']
            if pd.notna(mae):
                not_recovered_loss += mae
    
    # Net profit
    net_profit = recovered_profit - not_recovered_loss
    
    print(f'\nRecovered baskets: {len(recovered_df)}')
    print(f'  Total Potential (sum of all layer potentials): {recovered_profit:,.0f} points')
    
    print(f'\nNot Recovered baskets: {len(not_recovered_df)}')
    print(f'  Total Loss (sum of all layer MAEs): {not_recovered_loss:,.0f} points')
    
    print(f'\nNET PROFIT: {net_profit:+,.0f} points')
    print(f'  Per basket avg: {net_profit/len(df):,.0f} points')
    
    # Show breakdown by basket
    print('\nTop 5 Profitable Recovered Baskets:')
    basket_profits = []
    for idx, row in recovered_df.iterrows():
        total_potential = 0
        for i in range(1, int(row['NumLayers']) + 1):
            potential = row[f'Layer{i}Potential']
            if pd.notna(potential):
                total_potential += potential
        basket_profits.append((row['Ticket'], total_potential, row['NumLayers']))
    
    basket_profits.sort(key=lambda x: x[1], reverse=True)
    for ticket, profit, layers in basket_profits[:5]:
        print(f'  {ticket}: {profit:,.0f} points ({int(layers)} layers)')
    
    print('\nTop 5 Costly Failed Baskets:')
    basket_losses = []
    for idx, row in not_recovered_df.iterrows():
        total_mae = 0
        for i in range(1, int(row['NumLayers']) + 1):
            mae = row[f'Layer{i}MAE']
            if pd.notna(mae):
                total_mae += mae
        basket_losses.append((row['Ticket'], total_mae, row['NumLayers']))
    
    basket_losses.sort(key=lambda x: x[1], reverse=True)
    for ticket, loss, layers in basket_losses[:5]:
        print(f'  {ticket}: {loss:,.0f} points ({int(layers)} layers)')

print('\n' + '='*100)
