# Trading GU - Project Summary (Mobile View)

> **Last Updated:** 2026-03-19  
> **For:** On-the-go reference without MT5 access

---

## 🎯 Project Purpose

**Primary Goal:** Automated XAUUSD (Gold) scalping system with time-based risk management.

**Core Components:**
1. **GU Manager** - Main trading EA (opens positions based on sessions)
2. **TimeCutoffManager (TCM)** - Risk manager (closes positions based on time)
3. **Analysis Tools** - Python scripts for backtesting and optimization

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    METATRADER 5                             │
│  ┌─────────────────┐      ┌─────────────────────────────┐  │
│  │  GU Manager EA  │      │   TimeCutoffManager (TCM)   │  │
│  │  (3 instances)  │◄────►│        (1 instance)         │  │
│  │                 │      │                             │  │
│  │  - Asia (11)    │      │  Monitors positions from    │  │
│  │  - London (12)  │      │  GU instances by Magic #    │  │
│  │  - NY (13)      │      │                             │  │
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

---

## ⚙️ TCM v2.2 Current Settings

### Filter (What to Monitor)
- **Method:** Magic Number
- **Values:** `11,12,13` (GU Asia, London, NY instances)

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
| File | Purpose | Last Modified |
|------|---------|---------------|
| `TimeCutoffManager.mq5` | Risk manager EA | v2.2 - Partial close added |
| `GUM/GUManager.mq5` | Main trading EA | v1.00 |

### Configuration (Setfiles/)
| Session | Magic | File Pattern |
|---------|-------|--------------|
| Asia | 11 | `gu_*_asia.set` |
| London | 12 | `gu_*_london.set` |
| New York | 13 | `gu_*_ny.set` |

### Documentation
| File | Content |
|------|---------|
| `TimeCutoffManager_Documentation_v2.md` | Full TCM manual |
| `TCM_PreLive_Testing_Guide.md` | Testing procedures |
| `TCM_Test_Checklist.md` | Validation checklist |
| `GU_Manager_Documentation.md` | GU EA manual |
| `knowledge_base.md` | Research and analysis |

### Analysis (analysis/)
- Python scripts for backtesting
- Simulation results (CSV outputs - not synced)

---

## 🔄 Recent Changes (Last Session)

### TCM v2.2 Updates
1. ✅ **Partial Close** - Two-stage close (50% at 1min, 50% at 2min)
2. ✅ **Master Switch** - `UsePartialClose` to toggle on/off
3. ✅ **State Machine** - Replaced Sleep() with proper retry logic
4. ✅ **Race Condition Fix** - Atomic position selection
5. ✅ **Spread Filter** - Won't close into 500+ point spreads
6. ✅ **File Mutex** - Multi-instance safety for recovery CSV

### Git Repository
- ✅ Initialized and synced to GitHub
- ✅ Excluded large files (*.parquet, *.csv) for mobile sync
- ✅ 245 files tracked, ~47K lines

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
- GU Asia: 0.03 lots per trade  
- TCM: Closes 0.02 at 1min, 0.01 at 2min  

---

## 🔗 Important Links

- **GitHub:** https://github.com/andriosuroyo/trading-GU.git
- **MT5 Terminal Path:** `C:\Program Files\MetaTrader 5\terminal64.exe`
- **Recovery File:** `MQL5/Files/loss_recovery.csv`

---

*This document is optimized for mobile/offline reading. For full details, see individual documentation files.*
