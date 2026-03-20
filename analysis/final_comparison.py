"""Final comparison: Simulated Fixed TP vs Actual Trailing Stop"""

print("="*90)
print("COMPARISON: SIMULATED FIXED TP vs ACTUAL TRAILING STOP")
print("="*90)
print()

# Actual performance from Asia session
actual_total_pl = 14.86  # From previous analysis
actual_positions = 62

print("ACTUAL TRAILING STOP PERFORMANCE:")
print("-" * 90)
print(f"  Total P&L:        ${actual_total_pl:.2f}")
print(f"  Positions:        {actual_positions}")
print(f"  Avg per position: ${actual_total_pl/actual_positions:.2f}")
print()

print("SIMULATED FIXED TP PERFORMANCE (Best Configurations):")
print("-" * 90)

configs = [
    {"tp": 110, "tp_dollars": 1.10, "cutoff": 2, "pnl": 28.26, "win_rate": 59.0, "hits": 36, "misses": 25},
    {"tp": 90, "tp_dollars": 0.90, "cutoff": 2, "pnl": 28.07, "win_rate": 63.9, "hits": 39, "misses": 22},
    {"tp": 90, "tp_dollars": 0.90, "cutoff": 3, "pnl": 22.05, "win_rate": 75.4, "hits": 46, "misses": 15},
    {"tp": 110, "tp_dollars": 1.10, "cutoff": 5, "pnl": 24.22, "win_rate": 78.7, "hits": 48, "misses": 13},
    {"tp": 30, "tp_dollars": 0.30, "cutoff": 15, "pnl": 5.03, "win_rate": 98.4, "hits": 60, "misses": 1},
]

print(f"{'TP ($)':<10} {'Cutoff':<10} {'Win%':<10} {'Hits/Miss':<15} {'Net P&L':<15} {'vs Actual':<15}")
print("-" * 90)
for c in configs:
    diff = c['pnl'] - actual_total_pl
    diff_pct = (diff / actual_total_pl) * 100
    print(f"${c['tp_dollars']:<9.2f} {c['cutoff']:<10} {c['win_rate']:<10.1f} {c['hits']}/{c['misses']:<13} ${c['pnl']:<14.2f} {'+' if diff > 0 else ''}${diff:.2f} ({diff_pct:+.0f}%)")

print()
print("="*90)
print("KEY INSIGHTS:")
print("="*90)
print()
print("1. FIXED TP CAN OUTPERFORM TRAILING STOP:")
print("   - Best config (TP $1.10, 2-min): $28.26 vs $14.86 actual = +90% better")
print()
print("2. OPTIMAL CONFIGURATION:")
print("   - TP: $0.90-$1.10 (90-110 points)")
print("   - Cutoff: 2-5 minutes")
print("   - Accept ~60-79% win rate with controlled miss losses")
print()
print("3. WHY SHORTER CUTOFFS WIN:")
print("   - Miss losses grow dramatically with time (-$0.45 at 2min -> -$15.32 at 30min)")
print("   - Better to exit quickly if TP not hit")
print()
print("4. HIGH WIN RATE != PROFITABLE:")
print("   - TP $0.30 with 98% win rate only makes $5.03 (vs $28.26 best)")
print("   - Single miss at $0.30 costs -$13, wiping out 43 winning trades")
print()
print("="*90)
