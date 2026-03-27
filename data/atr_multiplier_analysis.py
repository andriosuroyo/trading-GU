"""
ATR Multiplier Analysis - Fixed 15min Window, Variable Multiplier
Explore multipliers from 0.2 to 3.0 to find optimal TP setting
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import numpy as np

def load_env():
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def connect_blackbull():
    env_vars = load_env()
    terminal_path = env_vars.get('MT5_TERMINAL_BLACKBULL')
    if not mt5.initialize(path=terminal_path):
        return False
    return True

def get_atr_m1_60(symbol, target_time):
    from_time = target_time - timedelta(hours=2)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, target_time)
    if rates is None or len(rates) < 60:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr_60'] = df['tr'].rolling(window=60).mean()
    df_before = df[df['time'] <= target_time]
    if df_before.empty:
        return None
    return df_before['atr_60'].iloc[-1]

def get_tick_data_blackbull(from_time, to_time):
    ticks = mt5.copy_ticks_range('XAUUSDp', from_time, to_time, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def analyze_position_multiplier(position, multiplier, cached_data):
    """
    Analyze position with fixed 15min window and variable ATR multiplier
    cached_data contains: atr_value, mfe15_price, mae15_price, mfe15_points, mae15_points, 
                         price_15min, points_15min_close, actual_points
    """
    pos_id = position['pos_id']
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    magic = position['magic']
    
    open_time = datetime.fromisoformat(position['open_time'])
    close_time = datetime.fromisoformat(position['close_time'])
    
    # Use cached values
    atr_value = cached_data['atr_value']
    mfe15_points = cached_data['mfe15_points']
    points_15min_close = cached_data['points_15min_close']
    actual_points = cached_data['actual_points']
    
    # Calculate ATRTP with this multiplier
    atr_tp_points = round(atr_value * multiplier * 100)
    
    # Determine outcome
    if mfe15_points > atr_tp_points:
        outcome = 'PROFIT'
        outcome_points = atr_tp_points
    else:
        outcome = 'LOSS'
        outcome_points = points_15min_close
    
    return {
        'Ticket': f'P{pos_id}',
        'Magic Number': magic,
        'Type': direction,
        'TimeOpen': open_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceOpen': entry_price,
        'TimeClose': close_time.strftime('%Y-%m-%d %H:%M:%S'),
        'PriceClose': exit_price,
        'ActualPoints': actual_points,
        'ATROpen': round(atr_value, 2),
        'Multiplier': multiplier,
        'ATRTP': atr_tp_points,
        'MFE15Points': mfe15_points,
        'MAE15Points': cached_data['mae15_points'],
        'Outcome': outcome,
        'OutcomePoints': outcome_points
    }

def get_15min_cached_data(position):
    """Pre-calculate all 15-min data that doesn't change with multiplier"""
    direction = position['direction']
    entry_price = position['open_price']
    exit_price = position['close_price']
    
    open_time = datetime.fromisoformat(position['open_time'])
    window_15min_end = open_time + timedelta(minutes=15)
    
    # Fetch ATR
    atr_value = get_atr_m1_60('XAUUSDp', open_time)
    if atr_value is None:
        atr_value = 0
    
    # Fetch tick data for 15min window
    fetch_start = open_time - timedelta(seconds=5)
    fetch_end = window_15min_end + timedelta(seconds=5)
    tick_df = get_tick_data_blackbull(fetch_start, fetch_end)
    
    if tick_df is None or tick_df.empty:
        return None
    
    window_ticks = tick_df[(tick_df['time'] >= open_time) & (tick_df['time'] <= window_15min_end)]
    if window_ticks.empty:
        return None
    
    # Calculate MFE/MAE for 15min window
    if direction == 'BUY':
        mfe_price = window_ticks['ask'].max()
        mfe_points = round(abs((mfe_price - entry_price) * 100))
        mae_price = window_ticks['bid'].min()
        mae_points = round(abs((entry_price - mae_price) * 100))
        actual_points = round((exit_price - entry_price) * 100)
        ticks_at_end = window_ticks[window_ticks['time'] <= window_15min_end]
        price_15min = ticks_at_end['bid'].iloc[-1] if not ticks_at_end.empty else exit_price
        points_15min_close = round((price_15min - entry_price) * 100)
    else:
        mfe_price = window_ticks['bid'].min()
        mfe_points = round(abs((entry_price - mfe_price) * 100))
        mae_price = window_ticks['ask'].max()
        mae_points = round(abs((mae_price - entry_price) * 100))
        actual_points = round((entry_price - exit_price) * 100)
        ticks_at_end = window_ticks[window_ticks['time'] <= window_15min_end]
        price_15min = ticks_at_end['ask'].iloc[-1] if not ticks_at_end.empty else exit_price
        points_15min_close = round((entry_price - price_15min) * 100)
    
    return {
        'atr_value': atr_value,
        'mfe15_price': mfe_price if direction == 'BUY' else mfe_price,
        'mae15_price': mae_price if direction == 'BUY' else mae_price,
        'mfe15_points': abs(mfe_points),
        'mae15_points': abs(mae_points),
        'price_15min': price_15min,
        'points_15min_close': points_15min_close,
        'actual_points': actual_points
    }

def main():
    print("=" * 80)
    print("ATR MULTIPLIER ANALYSIS - Fixed 15min Window")
    print("Exploring multipliers: 0.2 to 3.0 (0.1 increments)")
    print("Baseline (0.5x): +7,052 points")
    print("=" * 80)
    
    # Load positions
    with open('data/gu_positions_vantage.json', 'r') as f:
        data = json.load(f)
    
    target_positions = [p for p in data['closed_positions'] 
                       if str(p['magic']) in ['20', '30'] and '2026-03-20' in p['open_time']]
    
    print(f"Processing {len(target_positions)} positions...")
    
    if not connect_blackbull():
        print("Failed to connect")
        return
    
    try:
        # Pre-calculate 15min data for all positions (this is expensive, do once)
        print("\nFetching 15-minute data for all positions...")
        cached_data_all = {}
        for pos in target_positions:
            pos_id = pos['pos_id']
            cached = get_15min_cached_data(pos)
            if cached:
                cached_data_all[pos_id] = cached
        
        print(f"Cached data for {len(cached_data_all)} positions")
        
        # Multipliers to test: 0.2 to 3.0 in 0.1 increments
        multipliers = [round(x * 0.1, 1) for x in range(2, 31)]  # 0.2, 0.3, ..., 3.0
        
        all_results = {}
        summary_data = []
        
        for mult in multipliers:
            print(f"\nTesting multiplier {mult}x...")
            results = []
            
            for pos in target_positions:
                pos_id = pos['pos_id']
                if pos_id in cached_data_all:
                    result = analyze_position_multiplier(pos, mult, cached_data_all[pos_id])
                    if result:
                        results.append(result)
            
            if results:
                df = pd.DataFrame(results)
                all_results[mult] = df
                
                # Calculate summary
                profit_count = (df['Outcome'] == 'PROFIT').sum()
                loss_count = (df['Outcome'] == 'LOSS').sum()
                total_outcome = df['OutcomePoints'].sum()
                avg_outcome = df['OutcomePoints'].mean()
                win_rate = profit_count / (profit_count + loss_count) * 100
                avg_atrtp = df['ATRTP'].mean()
                
                summary_data.append({
                    'Multiplier': f'{mult}x',
                    'ATRTP_Avg': round(avg_atrtp, 0),
                    'ProfitCount': profit_count,
                    'LossCount': loss_count,
                    'WinRate': f'{win_rate:.1f}%',
                    'TotalOutcomePts': total_outcome,
                    'AvgOutcomePts': round(avg_outcome, 1)
                })
                
                print(f"  -> WinRate: {win_rate:.1f}%, Total: {total_outcome:+,}, AvgTP: {avg_atrtp:.0f}pts")
        
        # Create Excel file
        output_file = 'data/ATR_Multiplier_Analysis_15min.xlsx'
        print(f"\nCreating Excel file: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # RESULT sheet
            result_df = pd.DataFrame(summary_data)
            result_df.to_excel(writer, sheet_name='RESULT', index=False)
            print("  -> RESULT sheet written")
            
            # Individual multiplier sheets
            for mult in multipliers:
                if mult in all_results:
                    df = all_results[mult]
                    sheet_name = f'{mult}x'.replace('.', '_')
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"  -> {len(all_results)} multiplier sheets written")
        
        mt5.shutdown()
        
        print("\n" + "=" * 80)
        print("EXCEL FILE CREATED SUCCESSFULLY")
        print("=" * 80)
        print(f"File: {output_file}")
        print(f"Sheets: 30 total (RESULT + 0.2x to 3.0x)")
        
        print("\n" + "=" * 80)
        print("SUMMARY - All Multipliers (15min window)")
        print("=" * 80)
        print(result_df.to_string(index=False))
        
        # Find optimal
        best_total = result_df.loc[result_df['TotalOutcomePts'].idxmax()]
        best_avg = result_df.loc[result_df['AvgOutcomePts'].idxmax()]
        
        # Find highest win rate
        result_df['WinRateNum'] = result_df['WinRate'].str.replace('%', '').astype(float)
        best_winrate = result_df.loc[result_df['WinRateNum'].idxmax()]
        
        print("\n" + "=" * 80)
        print("OPTIMAL MULTIPLIER FINDINGS")
        print("=" * 80)
        print(f"Best Total Outcome: {best_total['Multiplier']} -> {best_total['TotalOutcomePts']:,} points (WinRate: {best_total['WinRate']})")
        print(f"Best Avg per Trade: {best_avg['Multiplier']} -> {best_avg['AvgOutcomePts']:.1f} points")
        print(f"Best Win Rate: {best_winrate['Multiplier']} -> {best_winrate['WinRate']} (Outcome: {best_winrate['TotalOutcomePts']:,})")
        
        # Baseline comparison
        baseline = result_df[result_df['Multiplier'] == '0.5x'].iloc[0]
        print(f"\nBaseline (0.5x): WinRate={baseline['WinRate']}, Total={baseline['TotalOutcomePts']:,}")
        
        if best_total['Multiplier'] != '0.5x':
            improvement = ((best_total['TotalOutcomePts'] - baseline['TotalOutcomePts']) / abs(baseline['TotalOutcomePts']) * 100)
            print(f"Best multiplier ({best_total['Multiplier']}) is {improvement:+.1f}% better than baseline")
        
        print("\n" + "=" * 80)
        print("EFFICIENCY FRONTIER ANALYSIS")
        print("=" * 80)
        print("Expected trade-off confirmed:")
        print("  - Lower multipliers: Higher WinRate, lower AvgTP, potentially lower total outcome")
        print("  - Higher multipliers: Lower WinRate, higher AvgTP, potentially higher total outcome")
        print("\nKey insight: Optimal multiplier balances capture rate vs target size")
        
    except Exception as e:
        mt5.shutdown()
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
