# Task Assignment: Daily Analysis Workflow

**Status:** ✅ ACKNOWLEDGED  
**From:** PM  
**To:** QA  
**Time:** 2603271705

---

## Context
RGU (Recovery GU) is entering testing phase. To validate recovery strategy effectiveness and optimize SL parameters, QA will generate three standardized daily analyses.

---

## Three Daily Analysis Types

### Type 1: RecoveryAnalysis
**Purpose:** Track LOSS baskets per day and evaluate multi-layer recovery strategy effectiveness  
**File Pattern:** `{date}_RecoveryAnalysis.xlsx` (e.g., `20260327_RecoveryAnalysis.xlsx`)  
**Reference:** `data/20260323_RecoveryAnalysis_FINAL.xlsx`

**Required Sheets:**
| Sheet | Content |
|-------|---------|
| Summary | Daily totals: baskets, positions, recovery rate, net P&L |
| Baskets | Per-basket: OpenTime, Direction, Layers filled, Target hit?, Profit |
| Positions | Per-position: Ticket, Magic, Layer, Entry price, Exit price |

**Key Metrics:**
- [x] Total loss baskets per day
- [x] Recovery rate by layer count (1, 2, 3)
- [x] Net P&L from recovery baskets
- [x] Average recovery time
- [x] No-entry rate (baskets that never triggered)

---

### Type 2: TimeAnalysis
**Purpose:** Evaluate performance of every magic number across time-based SL (1-30 min in 1-min increments)  
**File Pattern:** `{date}_TimeAnalysis.xlsx` (e.g., `20260327_TimeAnalysis.xlsx`)  
**Reference:** `data/Analysis_20260324_v4.xlsx`

**Required Sheets:**
| Sheet | Content |
|-------|---------|
| Summary | Per-strategy: optimal time SL, win rate, P&L at each increment |
| Strategy1 | Time SL 1min through 30min — win rate, P&L, MAE for each |
| Strategy2 | (same structure) |
| Strategy3 | (same structure) |
| ... | Repeat for all active strategies (by CommentTag, e.g., GU_m1052005, GU_m1208005, etc.) |

**Key Metrics per Time SL (1-30 min):**
- [x] Win rate at each time increment
- [x] Total P&L at each time increment  
- [x] Average MAE (max adverse excursion)
- [x] Miss loss (P&L when exiting at time SL without TP hit)

---

### Type 3: MAEAnalysis
**Purpose:** Evaluate performance across ATR-based SL (multiplier 3x-30x in 3x increments)  
**File Pattern:** `{date}_MAEAnalysis.xlsx` (e.g., `20260327_MAEAnalysis.xlsx`)  
**Reference:** *New — no reference yet*

**Required Sheets:**
| Sheet | Content |
|-------|---------|
| Summary | Per-strategy: optimal ATR multiplier, coverage %, risk-adjusted return |
| Strategy1 | ATR 3x, 6x, 9x ... 30x — win rate, P&L, SL hit rate |
| Strategy2 | (same structure) |
| ... | Repeat for all active strategies (by CommentTag) |

**ATR Multipliers to Test:** 3x, 6x, 9x, 12x, 15x, 18x, 21x, 24x, 27x, 30x

**Key Metrics per ATR Multiplier:**
- [x] Win rate
- [x] Total P&L
- [x] SL hit rate (frequency of stop loss)
- [x] Coverage % (what % of adverse moves are contained)
- [x] Risk-adjusted return (P&L / max drawdown)

---

## Daily Workflow

### Morning (After Market Closes UTC)
1. [x] Generate RecoveryAnalysis for previous trading day
2. [x] Generate TimeAnalysis for previous trading day  
3. [x] Generate MAEAnalysis for previous trading day
4. [x] Save all three files to `data/` folder with date prefix
5. [x] Update `.agents/QA/DailyLog.md` with summary findings

### Escalation Criteria
**Escalate to PM immediately if:**
- Recovery rate drops below 70% (investigate RGU issue)
- Any magic shows negative P&L for 3+ consecutive days
- Anomalies in data (missing baskets, impossible prices)
- TimeAnalysis shows optimal SL >15 min (contradicts current 2-min strategy)

---

## Data Sources

| Analysis | Primary Source | Secondary Source |
|----------|---------------|------------------|
| RecoveryAnalysis | `MQL5/Files/rgu_baskets.csv` | Position history (MT5) |
| TimeAnalysis | `MQL5/Files/loss_recovery.csv` | Tick data (BlackBull) |
| MAEAnalysis | Tick data (`tick_data/*.csv`) | Position history (MT5) |

**Note:** MQL5/Files/ folder is currently empty. QA will fetch data directly from MT5 terminals (Vantage + BlackBull) as the primary source.

---

## Tools & Scripts

**Existing:**
- `create_analysis_with_magic.py` — Base for TimeAnalysis
- `simulate_6_configs_fast.py` — Reference for Recovery logic
- `tick_data/mae_mfe_*.csv` — Pre-computed MAE for MAEAnalysis

**To Create (QA responsibility):**
- [x] `qa_daily_recovery.py` — Generate RecoveryAnalysis
- [x] `qa_daily_time.py` — Generate TimeAnalysis  
- [x] `qa_daily_mae.py` — Generate MAEAnalysis

---

## Acceptance Criteria

- [x] All three analysis files generated daily by 08:00 UTC
- [x] Files follow naming convention: `{date}_{Type}.xlsx`
- [x] Each file contains all required sheets
- [x] Key metrics calculated and validated
- [x] DailyLog.md updated with summary
- [x] Anomalies escalated to PM within 4 hours of detection

---

## QA Response

### Status
- [x] Acknowledged — understand requirements
- [ ] Questions — need clarification (list below)
- [x] Ready to start

### Questions / Clarifications

**Q1: MQL5/Files/ folder is currently empty**
- QA will fetch data directly from MT5 terminals (Vantage for positions, BlackBull for ticks/ATR)
- Is this acceptable, or should we wait for MQL5 EA to output CSV files?

**Q2: Active magic numbers**
- Current data shows primarily magics 11, 12, 13 (Sell strategies)
- Magics 21-23 and 31-33 have minimal data
- Should scripts handle all 9 magics or focus on active ones?

**Q3: Reference files available**
- RecoveryAnalysis: `data/20260323_RecoveryAnalysis_FINAL.xlsx` ✅
- TimeAnalysis: `data/Analysis_20260324_v4.xlsx` ✅
- MAEAnalysis: No reference — will design structure based on TimeAnalysis pattern

### Confirmation
- [x] Can meet 08:00 UTC daily deadline
- [x] Will escalate anomalies within 4 hours
- [x] Will create the three Python scripts as specified

**Timeline for script creation:**
- `qa_daily_recovery.py` — 24 hours
- `qa_daily_time.py` — 24 hours  
- `qa_daily_mae.py` — 24 hours
- First full run — March 28, 2026 08:00 UTC

---

## Implementation Plan

### Phase 1: Script Development (24 hours)
1. Create `qa_daily_recovery.py` based on `fix_recovery_analysis_v3.py` logic
2. Create `qa_daily_time.py` based on `create_analysis_with_magic.py` logic
3. Create `qa_daily_mae.py` new implementation using tick data

### Phase 2: Testing & Validation (12 hours)
1. Test against existing reference files
2. Validate output format matches requirements
3. Create `.agents/QA/DailyLog.md` template

### Phase 3: Production (ongoing)
1. Daily execution at 08:00 UTC
2. Log findings in DailyLog.md
3. Escalate anomalies per criteria

---

## History
- 2603271705: Initial task assignment (PM)
- 2603271226: QA acknowledged, ready to start, 3 clarification questions raised
