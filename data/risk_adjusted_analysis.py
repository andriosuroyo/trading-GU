# New file

                    'profit_count': profit_count,
                    'loss_count': loss_count,
                    'win_rate': win_rate,
                    'avg_outcome': total_outcome / total_trades if total_trades > 0 else 0
                })
    
    df_results = pd.DataFrame(results)
    
    if df_results.empty:
        print("No results generated")
        mt5.shutdown()
        return
    
    print()
    print("=" * 100)
    print("RISK-ADJUSTED RANKINGS (by Risk-Adjusted Ratio)")
    print("=" * 100)
    df_sorted = df_results.sort_values("risk_adjusted_ratio", ascending=False)
    print(df_sorted[["config", "total_outcome", "max_mae", "risk_adjusted_ratio", "win_rate"]].head(15).to_string(index=False))
    
    print()
    print("=" * 100)
    print("HEAT MAP: Risk-Adjusted Ratio")
    print("=" * 100)
    pivot_ratio = df_results.pivot_table(values="risk_adjusted_ratio", index="multiplier", columns="time_window", aggfunc="first")
    print()
    print("Multiplier | 5min | 10min | 15min | 20min | 25min | 30min")
    print("-" * 70)
    for mult in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        row = pivot_ratio.loc[mult]
        print(f"   {mult}x    | {row[5]:4.1f} | {row[10]:4.1f}  | {row[15]:4.1f}  | {row[20]:4.1f}  | {row[25]:4.1f}  | {row[30]:4.1f}")
    
    print()
    print("=" * 100)
    print("COMPARISON: Top by Outcome vs Top by Risk-Adjusted Ratio")
    print("=" * 100)
    print()
    print("Top 10 by TOTAL OUTCOME:")
    df_by_outcome = df_results.sort_values("total_outcome", ascending=False).head(10)
    for i, (_, row) in enumerate(df_by_outcome.iterrows(), 1):
        print(f"  {i}. {row['config']:12s} | Outcome: {row['total_outcome']:6,d} pts | Max MAE: {row['max_mae']:4d} pts | Ratio: {row['risk_adjusted_ratio']:4.1f}x")
    
    print()
    print("Top 10 by RISK-ADJUSTED RATIO:")
    df_by_ratio = df_results.sort_values("risk_adjusted_ratio", ascending=False).head(10)
    for i, (_, row) in enumerate(df_by_ratio.iterrows(), 1):
        print(f"  {i}. {row['config']:12s} | Outcome: {row['total_outcome']:6,d} pts | Max MAE: {row['max_mae']:4d} pts | Ratio: {row['risk_adjusted_ratio']:4.1f}x")
    
    print()
    print("=" * 100)
    print("KEY INSIGHTS")
    print("=" * 100)
    best_outcome = df_results.loc[df_results["total_outcome"].idxmax()]
    best_ratio = df_results.loc[df_results["risk_adjusted_ratio"].idxmax()]
    print(f"BEST BY OUTCOME: {best_outcome['config']} | {best_outcome['total_outcome']:,} pts | {best_outcome['win_rate']:.1f}% WR")
    print(f"BEST BY RATIO:   {best_ratio['config']} | {best_ratio['total_outcome']:,} pts | {best_ratio['risk_adjusted_ratio']:.2f}x ratio")
    
    mt5.shutdown()
    print()
    print("Done!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026-03-20", help="Date to analyze (YYYY-MM-DD)")
    args = parser.parse_args()
    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    main(target_date)
