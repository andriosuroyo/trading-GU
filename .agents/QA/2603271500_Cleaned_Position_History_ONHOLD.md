# Request: Cleaned Position History for MLE

**Status:** ⏸️ ON HOLD - Insufficient Data  
**From:** PM  
**To:** QA  
**Time:** 2603271500

---

## Context
MLE is ready for first task but needs cleaned position history with MAE/MFE calculations. This data will be used for feature engineering to predict TrailStart hits.

---

## Data Quality Decision

**PM Decision:** Data MUST start from March 23rd only. If insufficient data, **DO NOT FORCE IT**. Wait for more data to accumulate.

**Current Status:**
| Metric | Value |
|--------|-------|
| Date Range | March 23-27, 2026 |
| Available Positions | 109 |
| Target Positions | 200+ |
| Gap | **91 positions short** |

**Action:** ⏸️ **WAIT** for more data (end of week or next week)

---

## Requirements

**Output File:** `data/position_history_cleaned_260327.csv`

### Required Columns
| Column | Description |
|--------|-------------|
| Date | Trade date |
| Basket | Basket identifier |
| Ticket | Position ticket number |
| Magic | Magic number (11-13, 21-23, 31-33) |
| Direction | BUY or SELL |
| OpenTime | Position open timestamp (UTC+0) |
| CloseTime | Position close timestamp (UTC+0) |
| OpenPrice | Entry price |
| ClosePrice | Exit price |
| LossPoints | Points lost (if applicable) |
| ATRPoints | ATR(60) value at entry |
| Recovered | Whether position recovered (Y/N) |
| RecoveryTime | Time to recover (minutes) |
| FurthestPrice | Worst price seen (MAE) |
| LayerMAE | MAE per layer |
| TrailStartHit | Whether TrailStart was hit (Y/N) — TARGET VARIABLE |

### Filters
- [x] Date range: March 23, 2026 onwards (clean settings era)
- [x] Exclude glitch trades (simultaneous BUY/SELL at same timestamp)
- [x] Exclude carry-over trades (positions closing outside session window)
- [x] Include only GU magics: 11, 12, 13, 21, 22, 23, 31, 32, 33
- [x] Normalize P/L to 0.01 lot equivalent (divide by 10 for 0.10 lot positions)

---

## Acceptance Criteria
- [ ] At least 200 positions included (**NOT MET - Only 109 available**)
- [x] All fields populated (no nulls in critical columns: Magic, OpenTime, CloseTime, TrailStartHit)
- [x] Glitch trades filtered out
- [x] P/L normalized to 0.01 lot equivalent
- [x] Sample of 5 rows provided for PM review before full handover

---

## QA Response

### Status
- [ ] In Progress
- [ ] Complete
- [x] **ON HOLD - Insufficient Data**

### Notes / Blockers
**Data Availability Issue:**

With strict date range of March 23-27, 2026:
- Total Vantage positions: 253
- After carry-over filter (4hr buffer): ~150
- With valid BlackBull ATR/tick data: **109 positions**

**Gap Analysis:**
| Period | Positions |
|--------|-----------|
| March 12-16 | 199 positions |
| March 17-21 | 1 position (trading gap) |
| March 22 | ~40 positions |
| **March 23-27** | **253 positions (current)** |
| **After filtering** | **109 positions** |

**Options Considered:**
1. ✅ Include March 22 (adds ~40) - **REJECTED** per PM (must start March 23)
2. ✅ Remove carry-over filter entirely - **REJECTED** (compromises data quality)
3. ✅ Use March 12-16 (199 positions) - **REJECTED** (different settings)
4. ✅ Wait for more data - **ACCEPTED**

### Deliverable Summary

**Current Baseline Dataset (Preserved):**
- File: `data/position_history_cleaned_260327.csv`
- Rows: 109 positions
- Date range: March 23-26, 2026
- TrailStart hit rate: 33.0% (36 Y / 73 N)
- Recovery rate: 99.1%

**Sample Data:**
| Ticket | Magic | Direction | TrailStartHit | LayerMAE |
|--------|-------|-----------|---------------|----------|
| 1024572523 | 11 | BUY | Y | 964.0 |
| 1025864664 | 11 | BUY | Y | 33.0 |
| 1025881100 | 12 | BUY | Y | 664.0 |
| 1024205687 | 11 | SELL | N | 2080.0 |
| 1025592013 | 11 | SELL | N | 655.0 |

---

## Recommended Next Steps

1. **Re-run dataset generation on:**
   - End of this week (March 30-31)
   - Or end of next week (April 6-7)

2. **Target:** 200+ positions with March 23+ data only

3. **Process:** Re-execute `create_mle_dataset.py` when sufficient data available

---

## History
- 2603271500: Initial request (PM)
- 2603271207: QA attempted dataset generation
- 2603271215: **ON HOLD** - Insufficient data for March 23+ period only; waiting for more data accumulation as per PM instruction
- 2603271610: Final delivery with hold status confirmed (PM)
