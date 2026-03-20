# TODO - Trading GU Development

> Active development tasks and ideas  
> **Last Updated:** 2026-03-19

---

## 🔴 HIGH PRIORITY (Next Windows Session)

### TCM Testing
- [ ] Compile TCM v2.2 on Windows
- [ ] Test partial close with 0.03 lot position
- [ ] Verify 0.02 closes at 1min, 0.01 at 2min
- [ ] Test UsePartialClose=false (single close mode)
- [ ] Check spread filter during normal conditions

### Configuration
- [ ] Create test setfile with TCM magic numbers configured
- [ ] Document optimal TCM settings for each session

---

## 🟡 MEDIUM PRIORITY (Backlog)

### TCM Features to Consider
- [ ] **Breakeven Protection** - Move SL to entry after partial close in profit
- [ ] **News Blackout** - Pause closes during NFP/FOMC (5 min before/after)
- [ ] **Daily Loss Circuit Breaker** - Stop monitoring if daily loss > threshold
- [ ] **Slippage Monitoring** - Log expected vs actual close prices
- [ ] **Telegram Notifications** - Send close alerts to mobile

### Analysis Tasks
- [ ] Backtest 50/50 vs 70/30 partial close splits
- [ ] Analyze optimal partial close timing (45s vs 60s vs 90s)
- [ ] Compare performance with/without spread filter

---

## 🟢 LOW PRIORITY (Ideas)

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

### Decisions Made
- ✅ Two-stage close (partial + final) implemented
- ✅ Master switch (UsePartialClose) added
- ✅ 50% partial close percentage chosen
- ✅ Spread filter at 500 points (configurable)

---

## 📊 Testing Results (Fill in after Windows sessions)

### TCM v2.2 Live Test
| Test | Date | Result | Notes |
|------|------|--------|-------|
| 0.03 lot partial close | | | |
| 0.10 lot partial close | | | |
| Spread filter trigger | | | |
| Retry logic | | | |

---

## 🎯 Current Focus

**Active Experiment:** 2-minute total hold with 1-minute partial close at 50%

**Hypothesis:** Partial profit-taking reduces variance and improves risk-adjusted returns

**Success Criteria:**
- Partial close executes correctly (timing)
- Remainder closes at final cutoff
- No race conditions with GU EA
- Spread filter prevents bad fills

---

*Add new items as they come up. Check off completed items after Windows sessions.*
