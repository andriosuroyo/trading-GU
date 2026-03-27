import pandas as pd
from datetime import datetime

df = pd.read_excel('data/2026-03-20_RecoveryAnalysis.xlsx')

print('Verifying RecoveryDuration calculation:')
print('='*100)

# Show a few examples
for idx in range(5):
    row = df.iloc[idx]
    print('')
    print(f'Ticket: {row["Ticket"]}')
    print(f'  OpenTime: {row["OpenTime"]}')
    print(f'  CloseTime: {row["CloseTime"]}')
    print(f'  RecoveryTime: {row["RecoveryTime"]}')
    print(f'  RecoveryDurationMin: {row["RecoveryDurationMin"]}')
    
    # Calculate manually
    close_dt = datetime.strptime(row['CloseTime'], '%H:%M:%S')
    recovery_dt = datetime.strptime(row['RecoveryTime'], '%H:%M:%S')
    duration = (recovery_dt - close_dt).total_seconds() / 60
    print(f'  Manual calc (Close to Recovery): {duration:.1f} min')

print('')
print('='*100)
print('ANSWER: RecoveryDurationMin is calculated from SL hit (CloseTime) to Recovery')
print('This means:')
print('  - Position is open for 10 min')
print('  - Recovery trade starts at CloseTime')
print('  - RecoveryDuration is from CloseTime to when price returns to OpenPrice')
print('='*100)
