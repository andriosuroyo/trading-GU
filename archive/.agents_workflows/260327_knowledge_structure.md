# Knowledge Base Structure Reference

Quick reference for where information belongs in the knowledge hierarchy.

## 1. Expert Advisors (EAs)

### 1.1 GU Strategy
| Sub-section | Content | Example |
|-------------|---------|---------|
| 1.1.0 | Overview, purpose, core concept | "Grid/DCA EA on XAUUSDp..." |
| 1.1.1 | Entry logic, MA settings, filters | "MH uses MA 20/80 on M1..." |
| 1.1.2 | Exit logic, TP/SL, trailing | "ATR-based exit with 0.2x multiplier..." |
| 1.1.3 | Session hours, DST adjustments | "ASIA: 02:00-06:00 UTC..." |
| 1.1.4 | Magic numbers, naming conventions | "11=MH Asia, 21=HR10 Asia..." |
| 1.1.5 | Setfile parameters, standards | "MaxLevels=1, CooldownMin=1..." |
| 1.1.6 | Dated analysis findings | "March 13, 2026 — MaxLevels=1..." |

### 1.2 SL Maestro
| Sub-section | Content | Example |
|-------------|---------|---------|
| 1.2.0 | What it does, how it works | "Chart-attached utility for SL..." |
| 1.2.1 | Configuration parameters | "sl_type, sl_atr_period..." |
| 1.2.2 | Session-based SL settings | "Asia: 1.5x, London: 2.5x..." |
| 1.2.3 | Known bugs, limitations | "Swing High/Low logic BANNED..." |

### 1.3 Other Utilities
| Sub-section | Content |
|-------------|---------|
| 1.3.x | DurationExitPro, future utilities |

---

## 2. Data & Analysis

### 2.1 Data Sources
| Sub-section | Content |
|-------------|---------|
| 2.1.1 | MT5 history_deals, copy_ticks |
| 2.1.2 | utc_history.csv format, fields |

### 2.2 Analysis Methods
| Sub-section | Content |
|-------------|---------|
| 2.2.1 | P/L normalization formula |
| 2.2.2 | Session filtering by hour |
| 2.2.3 | Win rate, expectancy, etc. |

### 2.3 Historical Findings
| Sub-section | Content |
|-------------|---------|
| 2.3.x | Dated analysis entries |

---

## 3. Environment & Setup

### 3.1 Broker Configuration
- VantageInternational-Demo
- Symbol: XAUUSDp
- Server time: UTC+2
- EA setfile time: UTC+0

### 3.2 MT5 Setup
- Terminal paths
- Latency/ping info
- Symbol selection

### 3.3 DST Adjustments
- Annual calendar
- Session hour changes
- Fix time adjustments

---

## 4. Workflows

### 4.1 Setfile Creation
- create_gu_sets.py
- Reference folder usage
- Naming conventions

### 4.2 Data Export
- update_utc_history.py
- export_utc_history.py

### 4.3 Reporting
- generate_daily_report.py

---

## Quick Decision Tree

```
New Information About:
│
├─► How GU EA works?
│   └─► Section 1.1.x
│
├─► SL management?
│   └─► Section 1.2.x
│
├─► Analysis results?
│   └─► Section 1.1.6 or 2.3.x
│
├─► Session hours/DST?
│   └─► Section 3.3
│
├─► Broker/MT5 setup?
│   └─► Section 3.1 or 3.2
│
└─► How to do something?
    └─► Section 4.x (workflows)
```

---

## Common Mistakes to Avoid

1. **Don't put TODO items in knowledge base**
   - Move to `todo.md` instead

2. **Don't duplicate information**
   - Cross-reference instead

3. **Don't mix strategies**
   - Keep GU, SL Maestro, other utilities separate

4. **Don't forget dates**
   - All findings must have dates

5. **Don't save without discussion**
   - Follow the 4-step process
