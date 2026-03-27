"""
Analyze ATR-based SL from multiplier 4 to 10 (0.5 increments)
Assuming time-based SL (10min) is still active
"""
import pandas as pd
import numpy as np

dates = ['20260320', '20260323', '20260324']

# ATR multipliers to test
multipliers = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]

print("=" * 100)
print("ATR SL MULTIPLIER ANALYSIS (with 10min time-based SL active)")
print("=" * 100)

results = []

for mult in multipliers:
    total_outcome = 0
    total_sl_hits = 0
    total_positions = 0
    total_wins = 0
    total_losses = 0
    
    for date_str in dates:
        if date_str == '20260320':
            file_path = f'data/Analysis_{date_str}.xlsx'
        else:
            file_path = f'data/Analysis_{date_str}_v4.xlsx'
        
        try:
            df = pd.read_excel(file_path, sheet_name='10min')
            
            for _, row in df.iterrows():
                atr = row['ATROpen']
                mfe = row['MFE10Points']
                mae = row['MAE10Points']
                time_outcome = row['OutcomePoints']
                sl_distance = atr * mult
                
                total_positions += 1
                
                # Check if ATR SL would be hit (MAE exceeds ATR*mult)
                if mae >= sl_distance:
                    # ATR SL hit - close at -sl_distance
                    total_sl_hits += 1
                    total_losses += 1
                    outcome = -sl_distance
                else:
                    # Time-based outcome (could be win or loss)
                    outcome = time_outcome
                    if outcome > 0:
                        total_wins += 1
                    elif outcome < 0:
                        total_losses += 1
                
                total_outcome += outcome
                
        except Exception as e:
            print(f"{date_str}: Error - {e}")
    
    results.append({
        'Multiplier': mult,
        'Total Outcome': total_outcome,
        'SL Hits': total_sl_hits,
        'Hit Rate %': (total_sl_hits / total_positions * 100) if total_positions > 0 else 0,
        'Wins': total_wins,
        'Losses': total_losses,
        'Positions': total_positions
    })
    
    print(f"ATR x{mult:4.1f}: Outcome={total_outcome:+8,.0f} | SL Hits={total_sl_hits:3}/{total_positions} ({total_sl_hits/total_positions*100:4.1f}%) | Wins={total_wins} Losses={total_losses}")

df_results = pd.DataFrame(results)

print("\n" + "=" * 100)
print("SUMMARY TABLE")
print("=" * 100)
print(df_results.to_string(index=False))

# Find best
best = df_results.loc[df_results['Total Outcome'].idxmax()]
print(f"\n" + "=" * 100)
print(f"OPTIMAL: ATR x{best['Multiplier']} with outcome {best['Total Outcome']:+,.0f} pts")
print(f"SL Hit Rate: {best['Hit Rate %']:.1f}% | Wins: {best['Wins']} | Losses: {best['Losses']}")
print("=" * 100)

# Save to CSV
df_results.to_csv('atr_sl_analysis.csv', index=False)
print("\nSaved to atr_sl_analysis.csv")
