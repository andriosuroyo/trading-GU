# Timed Exit Pro - Duration Cap Profitability Analysis

## Complete Results Table: Net P/L by Strategy

| Strategy | Baseline | 15 min Cap | 30 min Cap | 45 min Cap | 60 min Cap |
|----------|----------|------------|------------|------------|------------|
| **MH** | -$87.24 | **-$25.30** | **-$25.30** | **-$25.30** | **-$25.30** |
| **HR05** | +$118.39 | +$118.39 | +$118.39 | +$118.39 | +$118.39 |
| **HR10** | +$39.27 | **+$46.43** | **+$46.43** | +$45.63 | +$43.07 |
| **TESTS** | -$25.48 | -$25.48 | -$25.48 | -$25.48 | -$25.48 |
| **TOTAL** | +$44.94 | **+$114.04** | **+$114.04** | +$113.23 | +$110.68 |

---

## Improvement vs Baseline ($)

| Strategy | 15 min Cap | 30 min Cap | 45 min Cap | 60 min Cap |
|----------|------------|------------|------------|------------|
| **MH** | **+$61.94** | **+$61.94** | **+$61.94** | **+$61.94** |
| **HR05** | $0.00 | $0.00 | $0.00 | $0.00 |
| **HR10** | **+$7.16** | **+$7.16** | +$6.35 | +$3.80 |
| **TESTS** | $0.00 | $0.00 | $0.00 | $0.00 |
| **TOTAL** | **+$69.10** | **+$69.10** | +$68.30 | +$65.74 |

---

## Improvement vs Baseline (%)

| Strategy | 15 min Cap | 30 min Cap | 45 min Cap | 60 min Cap |
|----------|------------|------------|------------|------------|
| **MH** | **+71.0%** | **+71.0%** | **+71.0%** | **+71.0%** |
| **HR05** | 0.0% | 0.0% | 0.0% | 0.0% |
| **HR10** | **+18.2%** | **+18.2%** | +16.2% | +9.7% |
| **TESTS** | 0.0% | 0.0% | 0.0% | 0.0% |

---

## Trades Affected by Duration Cap

| Strategy | Baseline | 15 min | 30 min | 45 min | 60 min |
|----------|----------|--------|--------|--------|--------|
| **MH** | 71 | 2 (2.8%) | 2 (2.8%) | 2 (2.8%) | 2 (2.8%) |
| **HR05** | 101 | 2 (2.0%) | 2 (2.0%) | 2 (2.0%) | 2 (2.0%) |
| **HR10** | 67 | 4 (6.0%) | 4 (6.0%) | 2 (3.0%) | 1 (1.5%) |
| **TESTS** | 379 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| **TOTAL** | 618 | 8 (1.3%) | 8 (1.3%) | 6 (1.0%) | 5 (0.8%) |

---

## Win Rate by Duration Cap

| Strategy | Baseline | 15 min | 30 min | 45 min | 60 min |
|----------|----------|--------|--------|--------|--------|
| **MH** | 90.1% | 90.1% | 90.1% | 90.1% | 90.1% |
| **HR05** | 87.1% | 87.1% | 87.1% | 87.1% | 87.1% |
| **HR10** | 85.1% | 85.1% | 85.1% | 85.1% | 85.1% |
| **TESTS** | 73.9% | 73.9% | 73.9% | 73.9% | 73.9% |

*Note: Win rate doesn't change because we're simulating early exit of losers, not filtering entries.*

---

## Key Findings

### 1. The "15-Minute Sweet Spot"
- **15-minute cap delivers maximum improvement: +$69.10 (+154%)**
- Only affects 1.3% of trades (8 out of 618)
- Catches all long-duration losers while preserving winners

### 2. Strategy-Specific Impact
- **MH**: Massive +71% improvement from cutting just 2 trades (the overnight carries)
- **HR10**: +18% improvement from cutting 4 extended-duration trades
- **HR05**: No improvement needed — already optimal
- **TESTS**: No trades exceed 15 minutes (all scalps)

### 3. Diminishing Returns
| Cap | Total P/L | Improvement | Trades Cut |
|-----|-----------|-------------|------------|
| 15 min | $114.04 | +$69.10 | 8 (1.3%) |
| 30 min | $114.04 | +$69.10 | 8 (1.3%) |
| 45 min | $113.23 | +$68.30 | 6 (1.0%) |
| 60 min | $110.68 | +$65.74 | 5 (0.8%) |

**The 15-30 minute window captures almost all the benefit.**

---

## Recommended Configuration

### Option A: Universal 30-Minute Cap (Simple)
```
All Strategies: 30 minutes max
Expected P/L: $114.04 (+154% vs baseline)
Trades affected: 8 (1.3%)
```

### Option B: Strategy-Specific (Optimal)
```
MH: 15 minutes (prevents overnight disasters)
HR05: No cap (already optimal)
HR10: 15 minutes (captures HR10 degradation)
TESTS: No cap (all trades < 5 min anyway)

Expected P/L: $114.04 (+154% vs baseline)
```

### Option C: Conservative 60-Minute Cap (Safe)
```
All Strategies: 60 minutes max
Expected P/L: $110.68 (+146% vs baseline)
Trades affected: 5 (0.8%)
```

---

## Clock-Time Exit Alternative

If using Timed Exit Pro's clock-time feature instead of duration:

| Session | Exit Time | Prevents |
|---------|-----------|----------|
| ASIA | 05:55 UTC | Late-session losers |
| LONDON | 11:55 UTC | Overlapping session risk |
| NY | 20:55 UTC | **The $123 MH disaster** |

**Recommendation:** Combine clock-time exits (session ends) + 30-minute max duration as safety net.

---

## Bottom Line

**A simple 30-minute max duration cap would have:**
- Prevented the two MH overnight carries (-$123.89)
- Cut 4 HR10 extended losers (+$7.16)
- Improved total P/L from **$44.94** to **$114.04** (+154%)
- Affected only **1.3%** of trades

**This is the single highest-impact optimization available.**
