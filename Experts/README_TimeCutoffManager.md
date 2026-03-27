# TimeCutoffManager - Quick Start

## What is this?

A MetaTrader 5 utility that:
1. **Monitors positions** opened by your trading EA
2. **Shows countdown timers** for each position
3. **Closes positions** automatically at time limit
4. **Tracks losses** for recovery strategies

---

## Files

| File | Purpose |
|------|---------|
| `TimeCutoffManager.mq5` | Main utility EA |
| `RecoveryTactics.mqh` | Advanced recovery strategies (optional) |
| `TimeCutoffManager_Documentation.md` | Full documentation |
| `README_TimeCutoffManager.md` | This file |

---

## Quick Setup (5 minutes)

### 1. Install
```
1. Open MetaEditor (F4 from MT5)
2. Copy TimeCutoffManager.mq5 to MQL5/Experts/
3. Press F7 to compile
4. Drag to chart from Navigator
```

### 2. Configure
```
Input Settings:
- Filter Method: Comment Contains
- Filter Value: GU_          [Current system — filters all GU positions]
- DefaultCutoffSeconds: 120  (2 minutes)
- WarningSeconds: 10
- TrackLosses: true
```

> [!NOTE]
> Old system used MagicNumberFilter with session-based magics (28260311, etc.).
> Current system uses Comment filter for all GU positions.
> See knowledge_base.md for current magic number system.

### 3. Run
```
- Dashboard appears on chart
- New positions get countdown timer
- Auto-closed at cutoff
- Losses tracked in CSV
```

---

## Example: Monitor GU Asia with 2-Minute Cutoff

```cpp
// Inputs:
InpMagicNumberFilter = 28260311    // GU Asia magic
InpDefaultCutoffSeconds = 120      // 2 minutes
InpWarningSeconds = 10             // Warn at 10 seconds
InpTrackLosses = true              // Track losses
```

**What happens:**
1. GU EA opens position
2. TimeCutoffManager detects it
3. Countdown starts: 2:00 → 0:00
4. At 10 seconds: Warning (yellow)
5. At 0 seconds: Position closed
6. If loss: Recorded to CSV

---

## Dashboard Screenshot (Text)

```
+--------------------------------------------------+
|  TIME CUTOFF MANAGER                             |
+--------------------------------------------------+
|  Ticket  Symbol  Type  Lots  P&L   Countdown     |
|  12345   XAUUSD  BUY   0.10  $2.30  1m 23s       |
|  12346   XAUUSD  SELL  0.10  $-1.20  8s    [WARN]|
+--------------------------------------------------+
|  Recovery Loss: $45.50                           |
+--------------------------------------------------+
```

---

## Recovery Loss File

Location: `MQL5/Files/loss_recovery.csv`

```csv
Date,Symbol,Loss,Lots,Ticket,Recovered
2026.03.16 14:30,XAUUSD,12.50,0.10,12345,0
2026.03.16 15:45,XAUUSD,8.30,0.10,12346,0
```

---

## Need Help?

See `TimeCutoffManager_Documentation.md` for:
- All input parameters
- Recovery strategies
- Troubleshooting
- Advanced usage

---

## Integration with Your Python Tick Data

The utility records losses to CSV. Your Python tick storage can:
1. Read `loss_recovery.csv`
2. Correlate with stored tick data
3. Analyze what happened during losing trades
4. Optimize cutoff times

See `tick_storage_manager.py` for tick data storage system.
