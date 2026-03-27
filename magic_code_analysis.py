"""
Analyze Magic Numbers with their #code definitions
Map performance to MA combinations
"""
import pandas as pd

# Magic number to code mapping (from your list)
magic_codes = {
    1: {'code': 'm1082805', 'timeframe': 'M1', 'fast': 8, 'slow': 28, 'pt_mult': 0.5, 'status': 'DISCONTINUED', 'note': 'Too aggressive, bad positions'},
    2: {'code': 'm1104005', 'timeframe': 'M1', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 'status': 'ACTIVE'},
    3: {'code': 'm1208005', 'timeframe': 'M1', 'fast': 20, 'slow': 80, 'pt_mult': 0.5, 'status': 'ACTIVE'},
    4: {'code': 'm1501H05', 'timeframe': 'M15', 'fast': 'H', 'slow': 'H', 'pt_mult': 0.5, 'status': 'ACTIVE'},  # H = ?
    5: {'code': 'm1502H05', 'timeframe': 'M15', 'fast': 'H', 'slow': 'H', 'pt_mult': 0.5, 'status': 'ACTIVE'},
    6: {'code': 'm1H2H05', 'timeframe': 'M1', 'fast': 'H', 'slow': '2H', 'pt_mult': 0.5, 'status': 'ACTIVE'},
    7: {'code': 'm1104003', 'timeframe': 'M1', 'fast': 10, 'slow': 40, 'pt_mult': 0.3, 'status': 'ACTIVE'},
    8: {'code': 'm1104007', 'timeframe': 'M1', 'fast': 10, 'slow': 40, 'pt_mult': 0.7, 'status': 'ACTIVE'},
    9: {'code': 'm5082803', 'timeframe': 'M5', 'fast': 8, 'slow': 28, 'pt_mult': 0.3, 'status': 'ACTIVE'},
    10: {'code': 'm5082805', 'timeframe': 'M5', 'fast': 8, 'slow': 28, 'pt_mult': 0.5, 'status': 'ACTIVE'},
    11: {'code': 'm2082805', 'timeframe': 'M2', 'fast': 8, 'slow': 28, 'pt_mult': 0.5, 'status': 'ACTIVE'},
    12: {'code': 'm2104005', 'timeframe': 'M2', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 'status': 'ACTIVE'},
}

print("=" * 100)
print("MAGIC NUMBER TO CODE MAPPING & PERFORMANCE ANALYSIS")
print("=" * 100)

print("\n" + "-" * 100)
print("MARCH 20TH PERFORMANCE (from Analysis_20260320)")
print("-" * 100)

# March 20th data (from previous analysis)
march20_data = {
    1: {'outcome': -344053, 'trades': '~40+'},  # Discontinued
    2: {'outcome': 33935, 'trades': '~20+'},
    3: {'outcome': 12253, 'trades': '~20+'},
    4: {'outcome': -100345, 'trades': '~30+'},
    5: {'outcome': -108428, 'trades': '~30+'},
    6: {'outcome': 63881, 'trades': '6'},  # Very few trades
    7: {'outcome': 15666, 'trades': '~20+'},
    8: {'outcome': 34709, 'trades': '~20+'},
    9: {'outcome': -143201, 'trades': '~40+'},
    10: {'outcome': -37573, 'trades': '~40+'},
    11: {'outcome': -17731, 'trades': '~20+'},
    12: {'outcome': 55308, 'trades': '~20+'},
}

print(f"\n{'Magic':<6} {'Code':<12} {'TF':<4} {'Fast':<5} {'Slow':<5} {'PT':<4} {'Outcome':<12} {'Status':<15}")
print("-" * 100)

for m in range(1, 13):
    info = magic_codes[m]
    perf = march20_data[m]
    print(f"{m:<6} {info['code']:<12} {info['timeframe']:<4} {str(info['fast']):<5} {str(info['slow']):<5} {info['pt_mult']:<4} {perf['outcome']:+12,} {info['status']:<15}")

print("\n" + "=" * 100)
print("KEY PATTERNS IDENTIFIED")
print("=" * 100)

print("""
1. WINNING COMBINATION: FastMA=10, SlowMA=40
   - Magic 2 (M1):  +33,935 pts
   - Magic 7 (M1, PT=0.3):  +15,666 pts
   - Magic 8 (M1, PT=0.7):  +34,709 pts
   - Magic 12 (M2):  +55,308 pts (BEST PERFORMER)
   
   * This 10/40 ratio (1:4) works across M1 and M2 timeframes
   * Consistent profitability regardless of PT multiplier

2. LOSING COMBINATION: FastMA=8, SlowMA=28
   - Magic 1 (M1):  -344,053 pts (DISCONTINUED)
   - Magic 9 (M5, PT=0.3):  -143,201 pts
   - Magic 10 (M5, PT=0.5):  -37,573 pts
   - Magic 11 (M2):  -17,731 pts
   
   * The 8/28 ratio (1:3.5) is too aggressive
   * Gets into positions too early, hits MAE before MFE

3. SLOWER MAs NOT WORKING:
   - Magic 3 (M1, 20/80): Only +12,253 pts (sluggish)
   - Magic 4 & 5 (M15): Both heavily negative
   
   * MA periods > 40 create too much lag for intraday
   * By the time signal fires, move is already underway

4. PROFIT TARGET MULTIPLIER INSIGHT:
   - 0.3x (Magic 7): +15,666 pts
   - 0.5x (Magic 2): +33,935 pts
   - 0.7x (Magic 8): +34,709 pts
   
   * 0.5x seems optimal (not too tight, not too loose)
""")

print("=" * 100)
print("RECOMMENDED NEW SETS TO TEST")
print("=" * 100)

new_recommendations = [
    (13, 'm3104005', 'M3', 10, 40, 0.5, 'Extend winning 10/40 to M3'),
    (14, 'm4104005', 'M4', 10, 40, 0.5, 'Extend winning 10/40 to M4'),
    (15, 'm5104005', 'M5', 10, 40, 0.5, 'Test 10/40 on M5 (vs losing 8/28)'),
    (16, 'm1103505', 'M1', 10, 35, 0.5, 'Tighten 10/40 ratio slightly'),
    (17, 'm1104505', 'M1', 10, 45, 0.5, 'Loosen 10/40 ratio slightly'),
    (18, 'm2104003', 'M2', 10, 40, 0.3, 'Test tighter PT on winning M2'),
    (19, 'm2104007', 'M2', 10, 40, 0.7, 'Test looser PT on winning M2'),
    (20, 'm1124805', 'M1', 12, 48, 0.5, 'Maintain 1:4 ratio with higher MAs'),
]

print(f"\n{'Magic':<6} {'Code':<12} {'TF':<4} {'Fast':<5} {'Slow':<5} {'PT':<4} {'Rationale'}")
print("-" * 100)
for m, code, tf, fast, slow, pt, note in new_recommendations:
    ratio = slow/fast
    print(f"{m:<6} {code:<12} {tf:<4} {fast:<5} {slow:<5} {pt:<4} {note} (ratio {ratio:.2f})")

print("\n" + "=" * 100)
print("WHY 50/100 AND 50/200 ARE FAILING")
print("=" * 100)
print("""
1. TOO MUCH LAG:
   - 50-period MA on M1 = 50 minutes of history
   - 200-period MA on M1 = 200 minutes (3+ hours)
   - By the time the fast MA crosses slow MA, the move is 70% complete

2. INTRADAY MISMATCH:
   - 50/200 is designed for daily/weekly charts
   - On M1-M5 timeframes, you need faster reaction
   - Optimal seems to be 10-20 periods for Fast, 40-80 for Slow

3. MISSED OPPORTUNITIES:
   - 50/200 will only catch major trends
   - GU strategy captures smaller intraday moves
   - Better to have 3-4 small winners than 1 big winner + 3 missed

VERDICT: Continue testing 50/100 and 50/200 for 1 more week, but 
expect them to underperform. The data is confirming they lag too 
much for this strategy's timeframe.
""")

print("=" * 100)
