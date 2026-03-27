"""
Fixed ATR SL Analysis
- ATR (e.g., 3.00) -> convert to points: 3.00 * 100 = 300 points
- Then apply multiplier: 300 * 4 = 1200 points SL
- Simulate: Check if TP is hit before SL
"""
import pandas as pd
import numpy as np

dates = ['20260320', '20260323', '20260324']

# ATR multipliers to test
multipliers = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]

print("=" * 100)
print("ATR SL MULTIPLIER ANALYSIS (CORRECTED)")
print("ATR -> Points conversion: ATR * 100")
print("SL Distance = ATR_Points * Multiplier")
print("=" * 100)

results = []

for mult in multipliers:
    total_outcome = 0
    total_wins = 0
    total_losses = 0
    sl_hits = 0
    pt_hits = 0
    time_exits = 0
    total_positions = 0
    
    for date_str in dates:
        if date_str == '20260320':
            file_path = f'data/Analysis_{date_str}.xlsx'
        else:
            file_path = f'data/Analysis_{date_str}_v4.xlsx'
        
        try:
            df = pd.read_excel(file_path, sheet_name='10min')
            
            for _, row in df.iterrows():
                # ATR is in price (e.g., 3.00 = $3.00)
                # Convert to points: 3.00 * 100 = 300 points
                atr_price = row['ATROpen']
                atr_points = atr_price * 100  # Convert to points
                
                sl_distance = atr_points * mult  # ATR-based SL in points
                
                # PT is fixed at 10min based outcome if it was a win
                # Actually, we need to know what the PT target was
                # Let's calculate PT from the data - PT is typically 0.5x ATR
                pt_distance = atr_points * 0.5  # PT = 0.5x ATR (50% of ATR in points)
                
                mfe = row['MFE10Points']  # Max favorable excursion in points
                mae = row['MAE10Points']  # Max adverse excursion in points
                time_outcome = row['OutcomePoints']
                
                total_positions += 1
                
                # Determine which happens first:
                # 1. PT hit (MFE >= PT distance)
                # 2. SL hit (MAE >= SL distance)  
                # 3. Time expires (10min) -> use actual outcome
                
                pt_hit = mfe >= pt_distance
                sl_hit = mae >= sl_distance
                
                if pt_hit and not sl_hit:
                    # PT hit first (win)
                    pt_hits += 1
                    total_wins += 1
                    outcome = pt_distance
                elif sl_hit and not pt_hit:
                    # SL hit first (loss)
                    sl_hits += 1
                    total_losses += 1
                    outcome = -sl_distance
                elif pt_hit and sl_hit:
                    # Both hit - need to determine which came first
                    # For simplicity, assume 50/50 or check which is closer to target
                    # If MFE/PT_ratio > MAE/SL_ratio, PT hit first
                    pt_ratio = mfe / pt_distance
                    sl_ratio = mae / sl_distance
                    if pt_ratio >= sl_ratio:
                        pt_hits += 1
                        total_wins += 1
                        outcome = pt_distance
                    else:
                        sl_hits += 1
                        total_losses += 1
                        outcome = -sl_distance
                else:
                    # Neither hit - time-based exit
                    time_exits += 1
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
        'Wins': total_wins,
        'Losses': total_losses,
        'Win Rate %': (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0,
        'PT Hits': pt_hits,
        'SL Hits': sl_hits,
        'Time Exits': time_exits,
        'Positions': total_positions
    })
    
    print(f"ATR x{mult:4.1f}: Outcome={total_outcome:+10,.0f} | Wins={total_wins:3} Losses={total_losses:3} | WinRate={(total_wins/(total_wins+total_losses)*100 if (total_wins+total_losses)>0 else 0):5.1f}% | PT={pt_hits} SL={sl_hits} Time={time_exits}")

df_results = pd.DataFrame(results)

print("\n" + "=" * 100)
print("SUMMARY TABLE")
print("=" * 100)
print(df_results.to_string(index=False))

# Find best
best = df_results.loc[df_results['Total Outcome'].idxmax()]
print(f"\n" + "=" * 100)
print(f"OPTIMAL: ATR x{best['Multiplier']} with outcome {best['Total Outcome']:+,.0f} pts")
print(f"Win Rate: {best['Win Rate %']:.1f}% | Wins: {best['Wins']:.0f} | Losses: {best['Losses']:.0f}")
print("=" * 100)

# Save to CSV
df_results.to_csv('atr_sl_analysis_fixed.csv', index=False)
print("\nSaved to atr_sl_analysis_fixed.csv")
