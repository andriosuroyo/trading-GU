# Trading GU - Project Summary (Mobile View)

> **Last Updated:** 2026-03-27 17:00  
> **Communication Protocol:** See `.agents/README.md`  
> **For:** On-the-go reference without MT5 access

---

## 🎯 Project Purpose

**Primary Goal:** Automated XAUUSD (Gold) scalping system with time-based risk management.

**Core Components:**
1. **GU Manager** - Main trading EA (opens positions based on sessions)
2. **TimeCutoffManager (TCM)** - Risk manager (closes positions based on time) — **CURRENTLY ACTIVE**
3. **RGU (Recovery GU)** - *Work in progress* — Takes GU losses as signals for high-RR recovery trades
4. **GUM (GU Manager v2)** - *Future consolidation* — Will eventually merge TCM + additional features
5. **Analysis Tools** - Python scripts for backtesting and optimization

---

## 🏗️ Architecture Overview

### Current Production Setup
```
┌─────────────────────────────────────────────────────────────┐
│                    METATRADER 5                             │
│  ┌─────────────────┐      ┌─────────────────────────────┐  │
│  │  GU Manager EA  │      │   TimeCutoffManager (TCM)   │  │
│  │  (3 instances)  │◄────►│      v2.2 (ACTIVE)          │  │
│  │                 │      │                             │  │
│  │  - Strategy 1   │      │  Monitors positions from    │  │
│  │  - Strategy 2   │      │  GU instances by Comment    │  │
│  │  - Strategy 3   │      │                             │  │
│  │                 │      │  Closes at:                 │  │
│  │  Opens trades   │      │  - 1 min: 50% (partial)     │  │
│  │  based on time  │      │  - 2 min: 50% (remainder)   │  │
│  └─────────────────┘      └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  loss_recovery   │
                    │     .csv         │
                    │ (tracks losses   │
                    │  for analytics)  │
                    └──────────────────┘
```

### In Development
- **RGU EA** — Monitors `loss_recovery.csv` for GU losses, enters recovery trades
- **GUM** — Future replacement consolidating TCM + recovery monitoring + analytics

---

## ⚙️ TCM v2.2 Current Settings

### Filter (What to Monitor)
- **Method:** Magic Number
- **Value:** `0` (all GU positions) or filter by Comment "GU_"

### Timing (When to Close)
| Stage | Time | Action | % Closed |
|-------|------|--------|----------|
| Partial | 1 minute | Close 50% of position | 50% |
| Final | 2 minutes | Close remainder | 100% |

### Safety Features
- **Max Spread:** 500 points (delays close if spread too high)
- **Max Retries:** 3 attempts with exponential backoff
- **Connection Check:** Validates terminal connection every 10s

### Inputs Summary
```
Duration Type: Minutes
Close Duration: 2
Use Partial Close: true
Partial Close Duration: 1
Partial Close %: 50
Max Spread Points: 500
```

---

## 📁 Key Files Reference

### Source Code (Experts/)
| File | Purpose | Status |
|------|---------|--------|
| `TimeCutoffManager.mq5` | Risk manager EA | **ACTIVE v2.2** |
| `RGU_EA.mq5` | Recovery EA | *In development* |
| `GUM/GUManager.mq5` | Future consolidated manager | *Work in progress* |

### Configuration (Setfiles/)

#### Setfile Naming Convention (Current)
```
gu_[timeframe][MAFast][MASlow][ATRTPMult].set

Examples:
  gu_m1052005.set = M1, MA 5/20, ATR TP Mult 0.5x
  gu_m1208005.set = M1, MA 20/80, ATR TP Mult 0.5x
  gu_m1104005.set = M1, MA 10/40, ATR TP Mult 0.5x

Where:
  - timeframe: m1 = 1-min, m6 = 6-min chart
  - MAFast: Fast MA period (2 digits)
  - MASlow: Slow MA period (2 digits)
  - ATRTPMult: ATR multiplier for TP × 10 (05 = 0.5x, 10 = 1.0x)
```

#### Active Setfile Folders
| Folder | Status | Description |
|--------|--------|-------------|
| `20260317/` | Legacy | Descriptive naming (gu_mh_asia.set) |
| `20260322/` | **Current** | Coded naming per convention above |
| `RGU/` | In dev | Recovery GU configuration |

### Documentation
| File | Content |
|------|---------|
| `TimeCutoffManager_Documentation_v2.md` | Full TCM manual |
| `TCM_PreLive_Testing_Guide.md` | Testing procedures |
| `TCM_Test_Checklist.md` | Validation checklist |
| `knowledge_base.md` | Research and analysis |
| `RGU_EA_Specification_v3.md` | RGU development spec |

### Analysis (analysis/)
- Python scripts for backtesting
- Simulation results (CSV outputs - not synced)

---

## 🔄 Recent Changes (Last Session)

### March 27, 2026
- **File Cleanup:** Archived 18 superseded analysis scripts per QA audit
- **Communication Protocol:** New `.agents/` naming system (`YYMMDDHHMM_Topic.md` + `_DONE` suffix)
- **QA Delivery:** Cleaned position history delivered to MLE ✅
- **RGU Bug:** ✅ 11 compilation errors **FIXED** — ready for testing
- **MLE Task:** ON HOLD — insufficient data (need end of week); ✅ multi-setting approach decided (Option B: unified model)
- **Setfile Convention:** Standardized coded naming format
- **Team Charter:** Established operating rules for Coder, QA, MLE

### TCM v2.2 Updates (March 19)
1. ✅ **Partial Close** - Two-stage close (50% at 1min, 50% at 2min)
2. ✅ **Master Switch** - `UsePartialClose` to toggle on/off
3. ✅ **State Machine** - Replaced Sleep() with proper retry logic
4. ✅ **Race Condition Fix** - Atomic position selection
5. ✅ **Spread Filter** - Won't close into 500+ point spreads
6. ✅ **File Mutex** - Multi-instance safety for recovery CSV

---

## 🎯 Active Decisions & Questions

### Current Experiment
- **Testing:** 2-minute total hold with 1-minute partial close
- **Hypothesis:** Reduces variance by locking in partial profits
- **Risk:** Small lots (0.03) may have uneven splits (0.02/0.01)

### Open Questions
1. Should trailing stop activate after partial close or only after final?
2. Is 500-point spread filter appropriate for XAUUSD during NFP?
3. Do we need breakeven protection before final cutoff?

### Future Features (Backlog)
- [ ] Telegram/webhook notifications
- [ ] News blackout periods (NFP, FOMC)
- [ ] Daily loss circuit breaker
- [ ] Slippage monitoring
- [ ] RGU EA integration with live trading

---

## 🛠️ Development Environment

### Windows (Primary)
- MetaTrader 5 (VantageInternational-Demo)
- MetaEditor for MQ5 compilation
- Python 3.x for analysis

### macOS (Mobile)
- VS Code or similar for markdown/Python editing
- No MT5 compilation (Windows-only)
- Use for: documentation, analysis scripts, planning

---

## 📝 Quick Commands

### Git Sync
```bash
# After changes
git add .
git commit -m "Description"
git push origin main

# On other device
git pull origin main
```

### File Search (macOS)
```bash
# Find all setfiles
find . -name "*.set" -type f

# Find TCM-related files
find . -name "*TCM*" -o -name "*TimeCutoff*"
```

---

## 📊 Performance Notes

**Ping:** 8ms to VantageInternational-Demo  
**Spreads (XAUUSD):** Normal ~20-40 points, News ~100-500+ points  
**Lot Sizes:** Minimum 0.01, Step 0.01  

**Current Test:**  
- Strategy m1052005: 0.03 lots per trade  
- TCM: Closes 0.02 at 1min, 0.01 at 2min  

---

## 🔗 Important Links

- **GitHub:** https://github.com/andriosuroyo/trading-GU.git
- **MT5 Terminal Path:** `C:\Program Files\MetaTrader 5\terminal64.exe`
- **Recovery File:** `MQL5/Files/loss_recovery.csv`

---

*This document is optimized for mobile/offline reading. For full details, see individual documentation files.*
