import pandas as pd

# March 24 Asia
df = pd.read_excel('data/Analysis_20260324_v4.xlsx', sheet_name='15min')
df['Hour'] = pd.to_datetime(df['TimeOpen']).dt.hour
asia = df[(df['Hour'] >= 1) & (df['Hour'] < 8)]

print('MARCH 24 ASIA LOSS BY MAGIC NUMBER')
print('Total:', len(asia), 'trades,', asia['OutcomePoints'].sum(), 'pts')
print()

for magic in sorted(asia['Magic Number'].unique()):
    subset = asia[asia['Magic Number'] == magic]
    print(f'Magic {int(magic)}: {len(subset)} trades, {subset["OutcomePoints"].sum():.0f} pts')

deact = [1, 7, 8, 9, 10, 11]
active = [2, 3, 4, 5, 6, 12]
deact_loss = asia[asia['Magic Number'].isin(deact)]['OutcomePoints'].sum()
active_loss = asia[asia['Magic Number'].isin(active)]['OutcomePoints'].sum()
print()
print('Deactivated sets (1,7,8,9,10,11):', deact_loss, 'pts')
print('Active sets (2,3,4,5,6,12):', active_loss, 'pts')

# March 23 London-NY
print()
print('='*60)
df23 = pd.read_excel('data/Analysis_20260323_v4.xlsx', sheet_name='15min')
df23['Hour'] = pd.to_datetime(df23['TimeOpen']).dt.hour
london_ny = df23[(df23['Hour'] >= 8) & (df23['Hour'] < 23)]

print('MARCH 23 LONDON-NY BY MAGIC NUMBER')
print('Total:', len(london_ny), 'trades,', london_ny['OutcomePoints'].sum(), 'pts')
print()

for magic in sorted(london_ny['Magic Number'].unique()):
    subset = london_ny[london_ny['Magic Number'] == magic]
    print(f'Magic {int(magic)}: {len(subset)} trades, {subset["OutcomePoints"].sum():.0f} pts')

deact_loss23 = london_ny[london_ny['Magic Number'].isin(deact)]['OutcomePoints'].sum()
active_loss23 = london_ny[london_ny['Magic Number'].isin(active)]['OutcomePoints'].sum()
print()
print('Deactivated sets:', deact_loss23, 'pts')
print('Active sets:', active_loss23, 'pts')
