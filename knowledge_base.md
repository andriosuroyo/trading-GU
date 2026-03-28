# GU Strategy — EA Knowledge Base

> **Persona**: 20-year veteran in technical trading, focusing on **scalping and intraday trading**.  
> **Last Updated:** 260328  
> **Ground Truth:** This file is the single source of truth for project knowledge

---

## ⚠️ Recent Changes (Last 30 Days)

| Date | Change | Old | New |
|------|--------|-----|-----|
| 260328 | Recovery Window | 120 minutes (spec) | **12 hours** (Analysis-proven optimal) |
| 260328 | ATR Multiplier | 1.0x (spec) | **3.0x** (Analysis-proven optimal) |
| 260323 | Magic Number System | Session-based (11-13, 21-23, 31-33) | Sequential (1, 2, 3...) with strategy in CommentTag |
| 260323 | Setfile Organization | By session (Asia/London/NY) | By strategy parameters (MA, timeframe, ATR mult) |
| 260323 | Trading Hours | Session-specific (02-06, 08-12, 17-21 UTC) | Unified (02:00-23:00 market time) |

### RecoveryAnalysis Findings (March 28, 2026)

**Data Period:** March 23-27, 2026 (144 loss baskets analyzed)

**Optimal Configuration Discovered:**
- **Recovery Window:** 12 hours (was 2 hours in spec)
- **ATR Multiplier:** 3x (was 1x in spec)
- **Recovery Rate:** ~88%
- **Total Week P&L:** +335,763 points

**Magic Number Performance (Active):**
| Magic | Recovery PL | Rate | Status |
|-------|-------------|------|--------|
| 3 | +49,387 | 63.7% | ✅ Best |
| 18 | +35,812 | 84.0% | ✅ Good |
| 19 | +36,584 | 86.5% | ✅ Good |
| 5 | **-2,353** | 73.3% | ⚠️ **Underperforming** |

**Deactivated Magics:** 1, 7, 8, 9, 10, 11 (since March 24)

---

## EA Architecture

**Scalping EA** on XAUUSDp (Vantage Demo) — opens via MA crossover on M1, single position per signal (MaxLevels=1), closes via trailing stop activation or time-based cutoff. Has news filter, trading hour restrictions, daily loss stop.

> [!IMPORTANT]
> **Strategy Pivot (March 23, 2026):** Complete restructuring of setfile organization and magic number system.
> 
> **Key Changes:**
> - Magic numbers now sequential (1, 2, 3...) not session-encoded
> - Strategy parameters encoded in CommentTag (e.g., `GU_m1052005`)
> - Trading window unified to 02:00-23:00 (avoids 01:00-02:00 open volatility and 23:00-23:58 close volatility)
> - Session analysis still relevant for performance review but not for setfile organization

> [!NOTE]
> GU sets moved from BlackBull Demo to **Vantage Demo** (Mar 2026) because Vantage has significantly better ping (**8 ms vs 80 ms**). Since we're exploring scalping strategies, this latency difference is material.

> [!IMPORTANT]
> **Current Lot Size:** Trading at **0.10 lots per position** (not 0.01). All P/L analysis must be normalized to 0.01 lot equivalent by dividing by 10 for comparison with historical results.

---

## Critical: EA Uses UTC+0 for Setfile Hours

> [!IMPORTANT]
> The EA interprets `InpStartHour` / `InpEndHour` as **UTC+0 (GMT)**, NOT MT5 server time (UTC+2).
>
> **Current Trading Window:** 02:00–23:00 UTC (avoids opening volatility 01:00-02:00 and closing volatility 23:00-23:58)

---

## Current Setfile System (March 23, 2026+)

### Setfile Naming Convention

```
gu_[timeframe][MAFast][MASlow][ATRTPMult].set

Examples:
  gu_m1052005.set = M1 chart, MA 5/20, ATR TP Mult 0.5x
  gu_m1208005.set = M1 chart, MA 20/80, ATR TP Mult 0.5x
  gu_m1104005.set = M1 chart, MA 10/40, ATR TP Mult 0.5x

Where:
  - timeframe: m1 = 1-min, m6 = 6-min chart
  - MAFast: Fast MA period (2 digits)
  - MASlow: Slow MA period (2 digits)  
  - ATRTPMult: ATR multiplier for TP × 10 (05 = 0.5x, 10 = 1.0x)
```

### Magic Number System

**Current System (Sequential):**
- Magic numbers are assigned sequentially: 1, 2, 3, 4, 5...
- Strategy identification is in the CommentTag, NOT the magic number
- Example: Magic=1, Comment="GU_m1052005"

**Why This Changed:**
- Previous system (11-13, 21-23, 31-33) encoded session information
- New system allows flexible strategy testing without session constraints
- Session analysis still performed post-trade but doesn't dictate setfile organization

### Active Setfiles (20260322/)

| Setfile | Magic | CommentTag | MA | ATR TP |
|---------|-------|------------|-----|--------|
| `gu_m1052005.set` | 1 | GU_m1052005 | 5/20 | 0.5x |
| `gu_m1104005.set` | 2 | GU_m1104005 | 10/40 | 0.5x |
| `gu_m1208005.set` | 3 | GU_m1208005 | 20/80 | 0.5x |
| `gu_m1501H05.set` | 4 | GU_m1501H05 | 150/1H | 0.5x |
| `gu_m1502H05.set` | 5 | GU_m1502H05 | 150/2H | 0.5x |
| `gu_m11H2H05.set` | 6 | GU_m11H2H05 | 1H/2H | 0.5x |
| `gu_m1104003.set` | 7 | GU_m1104003 | 10/40 | 0.3x |
| `gu_m1104007.set` | 8 | GU_m1104007 | 10/40 | 0.7x |
| `gu_m5052003.set` | 9 | GU_m5052003 | 5/20 | 0.3x |
| `gu_m5052005.set` | 10 | GU_m5052005 | 5/20 | 0.5x |

---

## Core EA Parameters

### Entry Logic
All strategies use MA crossover on M1:
- **MA periods** vary by setfile (encoded in filename)
- **Position Type:** Single position per signal (`InpMaxLevels = 1`)
- **Trading Window:** 02:00-23:00 UTC (unified, avoids open/close volatility)

### Exit Logic (Fixed TP + Trailing Stop)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `InpUseATRTPTarget` | `true` | Enable ATR-based TP |
| `InpATRPeriod` | 60 | ATR(60) on M1 |
| `InpTPIATRMult` | 0.5x (default) | Set by filename (03, 05, 07) |
| `InpUseBasketTrail` | `true` | Trailing stop enabled |
| `InpTrailStartMoney` | $3.00 | Per 0.10 lot |
| `InpTrailStepMoney` | $1.00 | Per 0.10 lot |

**Time-Based Cutoff:** Controlled by **TimeCutoffManager (TCM)** utility EA.
- Partial close: 50% at 1 minute
- Final close: remainder at 2 minutes

---

## Session Analysis (For Performance Review Only)

While strategies are no longer organized by session, session-based analysis is still valuable for identifying poorly performing time periods.

### Session Definitions (UTC+0)

| Session | UTC Hours | Server Time (UTC+2) | Purpose |
|---------|-----------|---------------------|---------|
| ASIA | 02:00–06:00 | 04:00–08:00 | Legacy reference |
| LONDON | 08:00–12:00 | 10:00–14:00 | Legacy reference |
| NY | 17:00–21:00 | 19:00–23:00 | Legacy reference |

**Current Trading Window:** 02:00-23:00 UTC (overlaps all sessions)

### How to Identify Session from Position Data

Use `OpenTime` to categorize positions by session for analysis:
- Asia session positions: OpenTime between 02:00-06:00 UTC
- London session positions: OpenTime between 08:00-12:00 UTC
- NY session positions: OpenTime between 17:00-21:00 UTC

---

## User Preferences (Intraday Rules)

- **Strict Adherence to Structure:** Mathematical edges are generated by executing valid setups against proven structure. Do not "gamble" on unmanaged positions.
- **Overnight & R/R Avoidance:** Aim for day closes. Current 02:00-23:00 window helps avoid overnight risk.
- **P/L Normalization:** All profit/loss must be converted to **0.01 lot equivalent** for consistent comparison. Currently trading 0.10 lots → divide P/L by 10.

---

## SL Maestro (Utility EA)

All GU strategies are monitored and assigned SL by **SL Maestro**, a chart-attached utility EA.

| Session | SL Approach |
|---|---|
| ASIA | ATR-based: `clamp(M12_ATR7 × 1.5, 1500, 3000)` |
| LONDON | ATR-based: `clamp(M12_ATR7 × 2.5, 2000, 4000)` |
| NY | ATR-based: `clamp(M12_ATR7 × 2.0, 3000, 5500)` |

**Key Points:**
- GU has **NO INTERNAL SL** — relies entirely on SL Maestro
- If SL Maestro is not running, positions have **NO STOP LOSS** (gambling scenario)

---

## Environment

| Item | Value |
|---|---|
| Broker (GU sets) | **VantageInternational-Demo** (8 ms ping) |
| Terminal (Vantage) | `C:\Program Files\MetaTrader 5\terminal64.exe` |
| Broker (legacy) | BlackBullMarkets-Demo (80 ms ping) |
| Terminal (BB) | `C:\Program Files\MetaTrader 5_1\terminal64.exe` |
| Symbol | XAUUSDp |
| **Current Lot Size** | **0.10 lots per position** |
| **Analysis Lot Size** | **0.01 lots (normalized)** — divide live P/L by 10 |
| SL Management | **SL Maestro** (chart-attached utility) |
| MT5 Server Time | UTC+2 |
| EA Setfile Time | **UTC+0 (GMT)** |
| Data Period | Mar 23 onwards, 2026 (current system) |

---

## Data Analysis Standards

### P/L Normalization Formula
```
Normalized P/L = (Raw P/L) / (Lot Size × 100)
```
- For 0.10 lots: Divide by 10
- For 0.20 lots: Divide by 20
- This ensures consistent comparison across different lot sizes

### Invalid Trade Filtering
All analyses must filter:
1. **Glitch trades:** Simultaneous BUY/SELL at same timestamp
2. **Carry-over trades:** Positions closing outside trading window (unmanaged)
3. **Non-GU comments:** Only analyze positions with "GU_" in comment

### Time Standard
- **ALL** time analysis in **UTC+0** only
- MT5 visual timezone is toxic — use `utc_history.csv` ground truth

### Magic Number Reference
**Current (March 23+):** Sequential (1, 2, 3...), strategy in CommentTag  
**Deprecated:** Session-based (11-13, 21-23, 31-33) — do not use for current analysis

---

## RGU (Recovery GU)

See `RGU_instructions.md` for complete RGU documentation.

### Optimal Configuration (Analysis-Proven)

Based on RecoveryAnalysis (March 23-27, 2026, 144 baskets):

| Parameter | Spec Value | **Analysis Optimal** | Change |
|-----------|------------|----------------------|--------|
| **RecoveryWindow** | 120 min | **12 hours (720 min)** | +6x longer |
| **ATR_Multiplier** | 1.0x | **3.0x** | More conservative spacing |
| **MaxLayers** | 3 | 3 | No change |
| **UseLayer1Immediate** | false | false | No change |

**Results at Optimal Config:**
- Recovery Rate: **~88%**
- Total Week P&L: **+335,763 points**
- Plateau Point: 16H+ (minimal gain beyond 16 hours)

### Key Insights from Analysis

1. **Longer Window = Better**: 12H window captures 88% vs 79% at 2H
2. **Conservative Spacing Wins**: 3x ATR > 2x > 1x for profitability
3. **Fewer Better Layers**: 3x multiplier reduces over-trading, higher quality entries
4. **Magic Performance Varies**: Magic 3 best (+49k), Magic 5 losing (-2k)

### Daily RecoveryAnalysis

QA generates daily RecoveryAnalysis reports:
- **File:** `data/YYYY-MM-DD_RecoveryAnalysis.xlsx`
- **Time:** 08:00 UTC daily
- **Content:** 36 configuration sheets (2H-24H × 1x/2x/3x)
- **Includes:** Per-magic performance, optimal config tracking

See `RECOVERY_ANALYSIS_REPORT.md` for methodology.

---

## TCM (TimeCutoffManager)

See `TimeCutoffManager_Documentation_v2.md` for complete TCM documentation.

**Current Settings:**
- Filter by Comment: "GU_" (not magic numbers)
- Partial close: 50% at 1 minute
- Final close: remainder at 2 minutes
- Max spread: 500 points

---

## Knowledge Management Protocol

### Single Source of Truth
This file (`knowledge_base.md`) is the **only authoritative source** of project knowledge.

### When Knowledge Changes:
1. User notifies PM of change
2. PM updates this file immediately
3. PM marks old info as DEPRECATED with date
4. PM updates all derived documents
5. PM notifies all staff of change

### Staff Must Not:
- Create conflicting knowledge documents
- Assume other files are authoritative
- Propagate knowledge without validating against this file

### PM Must:
- Scour every interaction for new info to record
- Update this file within 24 hours of learning new information
- Cross-reference all decisions against this file
- Archive outdated info with clear deprecation markers

---

## Deprecated Information (Do Not Use)

### Magic Number System (Deprecated March 23, 2026)
**OLD:** `11=Asia, 12=London, 13=NY, 21=HR10 Asia, etc.`  
**NEW:** Sequential numbers (1, 2, 3...), strategy in CommentTag  
**Reason:** Decoupled strategy from session for more flexible testing

### Session-Based Setfiles (Deprecated March 23, 2026)
**OLD:** `gu_mh_asia.set, gu_mh_london.set, gu_mh_ny.set`  
**NEW:** `gu_m1052005.set, gu_m1208005.set, etc.`  
**Reason:** Strategy parameters now encoded in filename, not session

---

*This document is the single source of truth. All other documents must derive from and reference this file.*
