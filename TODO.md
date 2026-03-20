# TODO - Trading GU Development

> **Last Updated:** 2026-03-20  
> **Working Environment:** macOS (Planning) ↔ Windows (MT5 Testing)

---

## 📋 PROTOCOL REFERENCE (Locked)

| Rule | Description |
|------|-------------|
| **Git Flow** | macOS → commit → push → Windows → pull → compile → test. Main branch only. |
| **Version Status** | MQ5 header indicates READY / WIP. No `_dev` filenames. |
| **Critical Fixes** | 100% safe before deployment. No "try and see." |
| **Testing Feedback** | Edit TODO.md on Windows, push results. Keep items open until resolved or **jointly** abandoned. |
| **Rollback** | Revert to last working Git version. No STABLE tags. |
| **Spec Format** | Markdown RFCs for features, inline for fixes. |
| **Knowledge Base** | I maintain `knowledge_base.md` but **must discuss changes first**. |
| **Live Environment** | Vantage Demo only. No restricted hours. |
| **Bug Reports** | Direct message. Critical = immediate priority. |
| **Versioning** | Semantic: 2.2.0 → 2.2.1 (bugfix), 2.3.0 (feature), 3.0.0 (breaking). |
| **Setfiles** | New dated folder per change. I generate from last active set + append deltas. |

---

## 🏷️ Current Version Status

| Component | Version | Status | Location |
|-----------|---------|--------|----------|
| TimeCutoffManager | 2.2.0 | **LIVE - Partial close verified** | `Experts/TimeCutoffManager.mq5` |
| GU Manager | 1.0.0 | Stable | `Experts/GUM/GUManager.mq5` |

**Header Convention for WIP:**
```
//|                        VERSION 2.3.0 - WORK IN PROGRESS            |
//|                        DO NOT DEPLOY - TESTING PHASE               |
```

**Header Convention for READY:**
```
//|                        VERSION 2.3.0 - READY FOR TESTING           |
```

---

## 🔴 PENDING TESTS (Windows/MT5 Machine Required)

> **Status:** [ ] = Not Started | [~] = In Progress | [x] = Passed | [!] = Failed

### TCM v2.2.0 Core Testing
- [ ] Compile TCM v2.2 on Windows (MetaEditor)
- [x] Test partial close with 0.03 lot position → expect 0.02/0.01 split
- [ ] Test partial close with 0.10 lot position → expect 0.05/0.05 split
- [ ] Verify 0.02 closes at 1min, 0.01 at 2min (timing accuracy)
- [ ] Test `UsePartialClose=false` (single close mode at 2min)
- [ ] Check spread filter during normal conditions (should allow close)
- [ ] Test spread filter blocking (may need to simulate or wait for news)
- [ ] Verify retry logic triggers on `TRADE_RETCODE_REJECT`

### Configuration
- [ ] Create test setfile with TCM magic numbers 11,12,13 configured
- [ ] Document optimal TCM settings for each session in Setfiles folder

---

## 🟡 OPEN QUESTIONS (Awaiting Decision)

> These block feature implementation. Discuss before proceeding.

| # | Question | Impact | Context |
|---|----------|--------|---------|
| 1 | Should trailing stop activate after partial close or only after final? | Affects TCM v2.3.0 design | Currently activates after final close only |
| 2 | Is 500-point spread filter appropriate, or should it be dynamic? | Affects close reliability during volatility | XAUUSD can hit 50-500 pts; 500 may be too loose for Asia, too tight for NFP |
| 3 | Should we add a "prefer close less" option for small lots? | Affects partial close math | 0.03 lots → 0.01/0.02 split vs current 0.02/0.01 |
| 4 | How to handle multiple TCM instances for different magic groups? | Affects deployment architecture | Currently one TCM monitors 11,12,13 |

---

## 🟠 PLANNED FEATURES (RFC Phase)

> **Status:** [RFC] = Specification needed | [IMPL] = Implementing | [TEST] = Ready to test

| Feature | Target Version | Status | Priority | Notes |
|---------|---------------|--------|----------|-------|
| **Breakeven Protection** | 2.3.0 | [TEST] | HIGH | Move SL to entry after partial close in profit — Coded, awaiting Windows testing |
| **News Blackout** | 2.3.0 or 2.4.0 | [RFC] | HIGH | Pause closes during NFP/FOMC (5 min before/after) |
| **Dynamic Spread Filter** | 2.3.0 or 2.4.0 | [RFC] | MEDIUM | Session-based spread thresholds |
| **Daily Loss Circuit Breaker** | 2.4.0 | [RFC] | MEDIUM | Stop monitoring if daily loss > threshold |
| **Slippage Monitoring** | 2.4.0 | [RFC] | LOW | Log expected vs actual close prices |
| **Telegram Notifications** | 2.4.0 | [RFC] | LOW | Send close alerts to mobile |

### Analysis Tasks (Backlog)
- [ ] Backtest 50/50 vs 70/30 partial close splits
- [ ] Analyze optimal partial close timing (45s vs 60s vs 90s)
- [ ] Compare performance with/without spread filter

---

## 🟢 DECISIONS LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-19 | Two-stage close (partial + final) | Reduce variance, lock partial profits |
| 2026-03-19 | Master switch `UsePartialClose` | Allow single-close fallback mode |
| 2026-03-19 | 50% partial close percentage | Balanced risk/reward per analysis |
| 2026-03-19 | 500-point spread filter | Configurable, prevents catastrophic fills during news |
| 2026-03-20 | Semantic versioning adopted | 2.2.0 → 2.2.1 (bugfix), 2.3.0 (feature), 3.0.0 (breaking) |

---

## 📊 TESTING RESULTS LOG

> **Updated by:** Windows/MT5 machine after testing  
> **Format:** Date | Test Name | Result | Notes

| Date | Test | Result | Notes |
|------|------|--------|-------|
| | 0.03 lot partial close | | |
| | 0.10 lot partial close | | |
| | Spread filter trigger | | |
| | Retry logic | | |

---

## 🎯 Current Focus

**Active Experiment:** TCM v2.2.0 — 2-minute total hold with 1-minute partial close at 50%

**Hypothesis:** Partial profit-taking reduces variance and improves risk-adjusted returns

**Success Criteria:**
- [ ] Partial close executes correctly (timing)
- [ ] Remainder closes at final cutoff
- [ ] No race conditions with GU EA
- [ ] Spread filter prevents bad fills

**Next Milestone:** Answer Open Questions #1-4, then proceed to RFC for v2.3.0 features.

---

*Protocol locked 2026-03-20. Changes to protocol require explicit agreement.*
