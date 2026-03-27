# TODO - Trading GU Development

> Active development tasks and ideas  
> **Last Updated:** 2026-03-27 17:00  
> **Recent:** RGU compilation fixed ✅ (0 errors)

---

## 🔴 HIGH PRIORITY (Active Work)

### RGU EA — Compilation Fixed, Ready for Testing
**Status:** ✅ Compilation fixed (0 errors, 0 warnings)  
**Owner:** PM + Coder  
**ETA:** 2-3 days for testing

- [x] Position detection (loss monitoring)
- [x] ATR-based entry distance calculation
- [x] Layer tracking (up to 3 layers)
- [x] Dashboard display
- [x] CSV output for `rgu_baskets.csv` ✅
- [x] **Fix 11 compilation errors** ✅ FIXED
- [ ] Create test setfile `Setfiles/RGU/RGU_Test_v3.set` ← **NEXT**
- [ ] Strategy Tester validation (5 scenarios)
- [ ] Document any bugs found

### QA — Cleaned Data Delivery
**Status:** ✅ COMPLETE  
**Delivered:** `data/position_history_cleaned_260327.csv`

**Test Scenarios:**
1. Basic Recovery — GU loss, RGU enters, price recovers
2. Multi-Layer Recovery — 3 layers triggered sequentially
3. No Entry (Filtered) — Distance < ATR threshold
4. Timeout — 120 min without recovery
5. Emergency SL — 30,000 pt adverse move

### QA — Cleaned Data Delivery
**Status:** Assigned  
**ETA:** Within 24 hours

- [ ] Create `data/position_history_cleaned_20260327.csv`
- [ ] Include MAE/MFE calculations
- [ ] Filter glitch trades and carry-overs
- [ ] Normalize P/L to 0.01 lot
- [ ] Provide 5-row sample for PM review

### MLE — Phase 1 Feature Engineering (ON HOLD)
**Status:** ⏸️ ON HOLD — awaiting data accumulation + PM decision  
**ETA:** End of trading week (260331 or later)

- [x] Receive cleaned position history from QA ✅
- [ ] Accumulate sufficient data (300+ positions, March 23+)
- [ ] Decision: Multi-setting ML approach (see Open Questions)
- [ ] Identify 5-10 candidate features for TrailStart prediction

**Hold Reason:** Settings changed March 23; need more data for robust ML. Also need decision on whether to train separate models per setting or unified model.
- [ ] Verify all features are look-ahead safe
- [ ] Univariate analysis (correlation to target)
- [ ] Feature correlation matrix
- [ ] Recommend top 3 features with rationale

---

## 🟡 MEDIUM PRIORITY (Backlog)

### TCM Maintenance
- [ ] Test spread filter (500 points) in live conditions
- [ ] Document optimal TCM settings per session

### TCM Features to Consider
- [ ] **Breakeven Protection** — Move SL to entry after partial close in profit
- [ ] **News Blackout** — Pause closes during NFP/FOMC (5 min before/after)
- [ ] **Daily Loss Circuit Breaker** — Stop monitoring if daily loss > threshold
- [ ] **Slippage Monitoring** — Log expected vs actual close prices
- [ ] **Telegram Notifications** — Send close alerts to mobile

### RGU Enhancements (Post-Testing)
- [ ] **Dashboard Integration** — Display active recovery baskets
- [ ] **MAE Tracking** — Record maximum adverse excursion per basket
- [ ] **Recovery Analytics** — Post-recovery performance analysis

### Analysis Tasks
- [ ] Backtest 50/50 vs 70/30 partial close splits
- [ ] Analyze optimal partial close timing (45s vs 60s vs 90s)
- [ ] Compare performance with/without spread filter

---

## 🟢 LOW PRIORITY (Ideas / Future)

### GUM Development (On Hold)
**Status:** Frozen until RGU production-stable

- [ ] Architecture design for TCM + RGU merger (future decision)
- [ ] State machine for unified position tracking
- [ ] Session-aware recovery monitoring

### Documentation
- [ ] Create video walkthrough of TCM setup
- [ ] Document common errors and solutions
- [ ] Create troubleshooting flowchart

### Tools
- [ ] Python script to parse recovery CSV and generate reports
- [ ] Dashboard for visualizing session performance

---

## 📝 Discussion Points

### Open Questions
1. Should trailing stop activate after partial close or only after final?
2. Is 500-point spread filter appropriate, or should it be dynamic?
3. Should we add a "prefer close less" option for small lots (0.03→0.01/0.02 instead of 0.02/0.01)?
4. How to handle multiple TCM instances for different magic number groups?
5. RGU: Should we add Layer 4+ with tighter risk controls (spec says 0% recovery rate)?
6. ✅ **MLE: Multi-setting ML approach — DECIDED:** Option B (unified model with Magic as categorical)

### Decisions Made
- ✅ Two-stage close (partial + final) implemented
- ✅ Master switch (UsePartialClose) added
- ✅ 50% partial close percentage chosen
- ✅ Spread filter at 500 points (configurable)
- ✅ Setfile naming: `gu_[tf][MAFast][MASlow][ATRTPMult].set`
- ✅ GUM frozen; RGU priority for development
- ✅ 16 files archived per QA audit

---

## 📊 Testing Results

### TCM v2.2 Live Test
| Test | Date | Result | Notes |
|------|------|--------|-------|
| 0.03 lot partial close | | | |
| 0.10 lot partial close | | | |
| Spread filter trigger | | | |
| Retry logic | | | |

### RGU Simulation Tests
| Config | Date | Recovery Rate | Net Profit | Notes |
|--------|------|---------------|------------|-------|
| Max3+Mult1x (no Layer1) | 3/25 | 78% | +83,083 pts | Baseline |

### RGU Strategy Tester Results
| Scenario | Date | Result | Notes |
|----------|------|--------|-------|
| Basic Recovery | | | |
| Multi-Layer Recovery | | | |
| No Entry (Filtered) | | | |
| Timeout | | | |
| Emergency SL | | | |

---

## 🎯 Current Focus

**Week of March 27, 2026:**

1. **Coder:** RGU testing & CSV output implementation
2. **QA:** Cleaned position history for MLE
3. **PM:** Track progress, update documentation
4. **MLE:** Await data, then feature engineering

**Success Criteria:**
- [ ] RGU compiles without warnings
- [ ] RGU passes all 5 test scenarios
- [ ] QA delivers cleaned data within 24h
- [ ] MLE identifies 3+ predictive features

---

## 📁 Repository Status

| Metric | Count |
|--------|-------|
| Files Archived | 18 |
| Excel Lock Files Removed | 0 |
| Active Analysis Scripts | 13 |
| Active Recovery Scripts | 6 |
| Active Verification Scripts | 8 |

*Last cleanup: March 27, 2026*

---

*Add new items as they come up. Check off completed items after Windows sessions.*
