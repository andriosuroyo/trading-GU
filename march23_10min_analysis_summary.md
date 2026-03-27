# March 23rd - 10min Analysis: Discrepancy Investigation

## Key Finding: PT Multiplier Mismatch

The primary reason for discrepancies between **ActualPoints** and **OutcomePoints** is that the analysis calculated ATRTP using **0.5x for ALL magic numbers**, but:

| Magic | Code | Should Use PT | Calculated With | Issue |
|-------|------|---------------|-----------------|-------|
| 7 | m1104003 | **0.3x** | 0.5x | ATRTP too high |
| 8 | m1104007 | **0.7x** | 0.5x | ATRTP too low |

### Example Discrepancy

**Position P1036418023 (Magic 8 - m1104007)**
- ATR = 6.97
- **Should be**: ATRTP = 6.97 × 0.7 × 100 = **488 points**
- **Calculated as**: ATRTP = 6.97 × 0.5 × 100 = **348 points**
- MFE10Points = 383
- Outcome: PROFIT (because 383 >= 348 with wrong PT)
- **Should be**: LOSS (because 383 < 488 with correct PT)

This explains the large discrepancies seen in Magic 7 and 8.

---

## Spread Analysis: Why MFE ≠ Profit

**Finding**: 0 positions where MFE10Points >= ATRTP but Outcome = LOSS

This suggests:
1. **Spread is not the primary issue** in this dataset
2. **The discrepancy is mainly due to PT multiplier mismatch**
3. Positions that hit MFE >= ATRTP are correctly marked as PROFIT

---

## Magic 7 & 8 Summary (10min window)

| Metric | Magic 7 (PT=0.3x) | Magic 8 (PT=0.7x) |
|--------|-------------------|-------------------|
| Positions | 35 | 34 |
| OutcomePoints Sum | 3,814 | 4,934 |
| ActualPoints Sum | 801 | 2,874 |
| **Discrepancy** | **-3,013** | **-2,060** |
| Hit TP (MFE>=ATRTP) | 28/35 | 28/34 |

**Note**: OutcomePoints uses wrong PT (0.5x), so sums are inflated for Magic 7 and deflated for Magic 8.

---

## Recommended Fix for Future Analysis

The analysis script should calculate ATRTP per magic number using the correct PT multiplier:

```python
pt_multipliers = {
    1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0.5, 6: 0.5,
    7: 0.3, 8: 0.7, 9: 0.3, 10: 0.5, 11: 0.5, 12: 0.5,
    13: 0.5, 14: 0.5, 15: 0.5, 16: 0.5, 17: 0.5, 18: 0.5, 19: 0.5
}

atr_tp = atr_value * pt_multipliers[magic_number] * 100
```

---

## Deactivated Magic Numbers (2026.03.24)

| Magic | Reason |
|-------|--------|
| 1 | 8/28 too aggressive, bad positions |
| 6, 7, 8 | PT variations - simulate via MFE instead |
| 9, 10, 11 | 8/28 ratio not profitable per data |

---

## Active Magic Numbers (as of 2026.03.24)

| Magic | Code | TF | Fast/Slow | Note |
|-------|------|----|-----------|------|
| 2 | m1104005 | M1 | 10/40 | Core winner |
| 3 | m1208005 | M1 | 20/80 | Moderate performance |
| 4 | m1501H05 | M15 | 1/100 | Sluggish |
| 5 | m1502H05 | M15 | 2/100 | Sluggish |
| 6 | m1H2H05 | M1 | 100/200 | Too slow |
| 12 | m2104005 | M2 | 10/40 | **Best performer** |
| 13 | m3104005 | M3 | 10/40 | New - extend winner |
| 14 | m4104005 | M4 | 10/40 | New - extend winner |
| 15 | m5104005 | M5 | 10/40 | New - replace 8/28 |
| 16 | m6104005 | M6 | 10/40 | New - extend winner |
| 17 | m1103505 | M1 | 10/35 | New - tighter ratio |
| 18 | m1104505 | M1 | 10/45 | New - looser ratio |
| 19 | m1124805 | M1 | 12/48 | New - higher MAs |
