# TimeCutoffManager - Documentation

> [!IMPORTANT]
> **Documentation Update Notice:** Examples in this file use deprecated session-based magic numbers (28260311, 28260312, 28260313).
> Current system uses sequential magics (1, 2, 3...) with strategy encoded in CommentTag.
> Filter by Comment "GU_" instead of Magic Number for current setup.
> See `knowledge_base.md` for current system details.

## Overview

TimeCutoffManager is an MQL5 utility EA that monitors positions opened by other EAs and enforces time-based cutoffs with automatic closure. It features a real-time dashboard with countdown timers and tracks losses for recovery strategies.

---

## Features

### 1. Position Monitoring
- Automatically detects newly opened positions
- Filters by Magic Number, Symbol, and Comment
- Tracks position open time and calculates cutoff time
- Updates every second (not every tick - efficient)

### 2. Time-Based Cutoff
- Default cutoff: 120 seconds (configurable)
- Automatic position closure at cutoff time
- Warning issued before close (configurable seconds)
- Optional trailing stop after cutoff trigger

### 3. Dashboard Display
- Real-time countdown timer for each position
- Shows: Ticket, Symbol, Type, Lots, P&L, Countdown, Status
- Color coding:
  - White: Normal
  - Yellow: Warning (approaching cutoff)
  - Red: Critical (< 5 seconds)
  - Green: Profitable position
  - Salmon: Losing position
- Recovery loss tracker display

### 4. Loss Tracking
- Records all losses to CSV file
- Tracks unrecovered loss total
- Supports recovery strategies (via RecoveryTactics.mqh)
- Data persists between sessions

---

## Installation

1. Copy `TimeCutoffManager.mq5` to `MQL5/Experts/`
2. Copy `RecoveryTactics.mqh` to `MQL5/Include/` (optional, for advanced recovery)
3. Compile in MetaEditor
4. Attach to any chart (recommend separate chart for monitoring)

---

## Input Parameters

### Position Filter
| Parameter | Default | Description |
|-----------|---------|-------------|
| `InpMagicNumberFilter` | 0 | Monitor only this magic (0 = all) |
| `InpCommentFilter` | "" | Filter by comment text (empty = all) |
| `InpSymbolFilter` | "" | Filter by symbol (empty = current chart) |

### Cutoff Settings
| Parameter | Default | Description |
|-----------|---------|-------------|
| `InpDefaultCutoffSeconds` | 120 | Time before auto-close (seconds) |
| `InpWarningSeconds` | 10 | Seconds before warning |
| `InpUseTrailing` | false | Enable trailing stop after cutoff |
| `InpTrailDistance` | 0 | Trail distance in points (0 = disabled) |

### Dashboard Settings
| Parameter | Default | Description |
|-----------|---------|-------------|
| `InpDashboardX` | 10 | Dashboard X position (pixels) |
| `InpDashboardY` | 30 | Dashboard Y position (pixels) |
| `InpRowHeight` | 20 | Row height for position list |
| `InpColorNormal` | White | Normal text color |
| `InpColorWarning` | Yellow | Warning color |
| `InpColorCritical` | Red | Critical (< 5s) color |
| `InpColorProfit` | Lime | Profit color |
| `InpColorLoss` | Salmon | Loss color |

### Recovery Tracking
| Parameter | Default | Description |
|-----------|---------|-------------|
| `InpTrackLosses` | true | Enable loss tracking |
| `InpRecoveryFile` | "loss_recovery.csv" | Recovery data filename |
| `InpRecoveryMultiplier` | 1.5 | Recovery lot multiplier |

---

## Usage Scenarios

### Scenario 1: Basic Time Cutoff
**Setup:**
- MagicNumberFilter: 28260311 (GU Asia)
- DefaultCutoffSeconds: 120
- WarningSeconds: 10

**Behavior:**
- All GU Asia positions get 2-minute timer
- Dashboard shows countdown
- Position closes automatically at 2 minutes
- Loss recorded if applicable

### Scenario 2: Session-Specific Cutoffs
**Setup:**
Run 3 instances on 3 charts:

**Chart 1 - ASIA:**
- MagicNumberFilter: 28260311
- DefaultCutoffSeconds: 120 (2 minutes)

**Chart 2 - LONDON:**
- MagicNumberFilter: 28260312
- DefaultCutoffSeconds: 360 (6 minutes)

**Chart 3 - NY:**
- MagicNumberFilter: 28260313
- DefaultCutoffSeconds: 900 (15 minutes)

### Scenario 3: With Trailing Stop
**Setup:**
- DefaultCutoffSeconds: 120
- UseTrailing: true
- TrailDistance: 30

**Behavior:**
- Position gets 2-minute timer
- At 2 minutes, if profitable, activates trailing stop
- Trails 30 points behind price
- Closes if price reverses 30 points from peak

### Scenario 4: Recovery Mode
**Setup:**
- TrackLosses: true
- RecoveryMultiplier: 1.5

**Behavior:**
- Records every loss with ticket, amount, time
- Displays total unrecovered loss on dashboard
- Next trade lot size = base * 1.5
- Continues until loss recovered

---

## Dashboard Layout

```
+--------------------------------------------------+
|  TIME CUTOFF MANAGER                             |
+--------------------------------------------------+
|  Ticket | Symbol | Type | Lots | P&L | Countdown |
+--------------------------------------------------+
|  12345  | XAUUSD | BUY  | 0.10 | $5  | 1m 45s    |
|  12346  | XAUUSD | SELL | 0.10 | $-2 | 45s       | ← Yellow (warning)
|  12347  | XAUUSD | BUY  | 0.10 | $8  | 3s        | ← Red (critical)
+--------------------------------------------------+
|  Recovery Loss: $45.50                           |
+--------------------------------------------------+
```

---

## Recovery Strategies (Advanced)

Include `RecoveryTactics.mqh` for advanced recovery:

```cpp
#include "RecoveryTactics.mqh"

// Create recovery calculator
CRecoveryCalculator Recovery(RECOVERY_MARTINGALE);
Recovery.SetBaseLotSize(0.10);
Recovery.SetMaxLotSize(2.0);
Recovery.SetMaxRecoveryLevels(5);

// In OnTick or trade event:
if(positionClosedWithLoss)
{
    Recovery.RecordLoss(lossAmount, lotSize);
    double nextLot = Recovery.CalculateNextTradeSize();
    double targetProfit = Recovery.GetTargetProfit();
    
    // Open next trade with nextLot size
    // Set TP to targetProfit
}
```

### Recovery Strategy Types

1. **RECOVERY_NONE** - Just track, no auto-adjustment
2. **RECOVERY_MARTINGALE** - Double lot after loss (aggressive)
3. **RECOVERY_FIBONACCI** - 1, 1, 2, 3, 5, 8... progression
4. **RECOVERY_FIXED_STEP** - Add 50% each level
5. **RECOVERY_PROFIT_TARGET** - Same lot, higher target
6. **RECOVERY_HYBRID** - Moderate lot increase (recommended)

---

## Integration with GU EA

### Recommended Configuration

**For Asia (Magic 28260311):**
```
DefaultCutoffSeconds = 120  // 2 minutes
WarningSeconds = 10
UseTrailing = false
TrackLosses = true
```

**For London (Magic 28260312):**
```
DefaultCutoffSeconds = 360  // 6 minutes
WarningSeconds = 30
UseTrailing = true
TrailDistance = 60
TrackLosses = true
```

**For NY (Magic 28260313):**
```
DefaultCutoffSeconds = 900  // 15 minutes
WarningSeconds = 60
UseTrailing = true
TrailDistance = 70
TrackLosses = true
```

---

## Data Files

### Loss Recovery File (CSV Format)
```csv
Date,Symbol,Loss,Lots,Ticket,Recovered
2026.03.16 14:30:00,XAUUSD,12.50,0.10,12345,0
2026.03.16 15:45:00,XAUUSD,8.30,0.10,12346,0
```

Location: `MQL5/Files/loss_recovery.csv`

---

## Troubleshooting

### Dashboard not showing
- Check that chart has enough space (drag to expand)
- Verify InpDashboardX/Y coordinates not off-screen
- Check Objects List (F8) for "TCM_*" objects

### Positions not being monitored
- Check MagicNumberFilter matches your EA
- Verify SymbolFilter (empty = current chart only)
- Check CommentFilter if your EA uses comments

### Positions not closing at cutoff
- Verify utility is attached and running
- Check Experts tab for error messages
- Ensure sufficient permissions for order close

### Recovery file not saving
- Check MQL5/Files directory exists
- Verify write permissions
- Check Experts tab for file errors

---

## Performance Notes

- Updates once per second (not every tick) - very efficient
- Minimal CPU usage
- No interference with trading EAs
- Can run on same chart as trading EA or separate
- Recommended: Run on separate chart for clear monitoring

---

## Future Enhancements

Possible additions for future versions:
1. Web/dashboard interface for remote monitoring
2. Telegram notifications for cutoffs/warnings
3. Multi-symbol monitoring with tabbed interface
4. Automated recovery trade execution
5. Integration with Python tick data storage

---

## Support

For issues or questions:
1. Check Experts tab for error messages
2. Verify input parameters match your setup
3. Test with TrackLosses=false first
4. Enable "Allow DLL imports" if using external libraries
