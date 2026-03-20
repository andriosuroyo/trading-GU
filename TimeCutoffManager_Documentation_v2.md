# TimeCutoffManager v2.2 Documentation

## Overview
TimeCutoffManager (TCM) is a MetaTrader 5 utility EA that monitors positions opened by other EAs and enforces time-based cutoffs with automatic closure.

---

## Input Parameters

### Position Filter Method

**Filter Method** (`InpFilterMethod`)
- **Type:** Dropdown (Enumeration)
- **Options:**
  1. **Magic Number** - Filter by position magic number(s)
  2. **Comment Contains** - Filter by text in position comment
  3. **Symbol** - Filter by trading symbol(s)

**Filter Value** (`InpFilterValue`)
- **Type:** String
- **Usage depends on Filter Method:**
  - **Magic Number:** Enter comma-separated magic numbers (e.g., "11,12,13") or "0" for all
  - **Comment Contains:** Enter text to match (e.g., "GU_ASIA") or leave empty for all
  - **Symbol:** Enter comma-separated symbols (e.g., "XAUUSDp,GOLD") or leave empty for current chart

> **Note:** Only ONE filter method is active at a time. The dropdown selection determines which filter is used.

---

### Cutoff Settings

**Duration Type** (`InpDurationType`)
- **Type:** Dropdown (Enumeration)
- **Options:**
  1. **Seconds** - Duration in seconds
  2. **Minutes** - Duration in minutes
  3. **Hours** - Duration in hours

**Close Duration** (`InpCloseDuration`)
- **Type:** Integer
- **Default:** 2
- **Example:** If Duration Type = Minutes and Close Duration = 2, positions will fully close after 2 minutes

**Use Partial Close** (`InpUsePartialClose`)
- **Type:** Boolean (true/false)
- **Default:** true
- **Function:** Master switch to enable/disable two-stage close
  - **true:** Partial close executes at Partial Close Duration, remainder at Close Duration
  - **false:** Single close at Close Duration (legacy behavior)

**Partial Close Duration** (`InpPartialCloseDuration`)
- **Type:** Integer
- **Default:** 1
- **Function:**
  - **0** = Disabled (no partial close, only final close)
  - **>0** = Close partial percentage at this time, remainder at Close Duration
- **Example:** If set to 1 and Partial Close % = 50, 50% of position closes at 1 minute, remainder at 2 minutes

**Partial Close Percentage** (`InpPartialClosePct`)
- **Type:** Double
- **Default:** 50
- **Function:** Percentage of position volume to close at Partial Close Duration
- **Example:** 50 = close 50% of lots at partial time, remainder at final time

**Two-Stage Close Example:**
```
Duration Type = Minutes
Close Duration = 2
Partial Close Duration = 1
Partial Close % = 50

T+0:00  Position opened (1.00 lot)
T+1:00  Partial close: 0.50 lot closed, 0.50 lot remains
T+2:00  Final close: remaining 0.50 lot closed
```

**Warning Before Close** (`InpWarningSeconds`)
- **Type:** Integer (seconds)
- **Default:** 10
- **Function:** 
  - X seconds BEFORE cutoff, the dashboard countdown turns **yellow** as a visual warning
  - Alert is logged to the Experts tab
  - Set to 0 to disable warning
- **Example:** If set to 10, the position row flashes yellow 10 seconds before closure

**Use Trailing Stop After Cutoff** (`InpUseTrailing`)
- **Type:** Boolean (true/false)
- **Default:** false
- **Function:**
  - When **false**: Positions close immediately at cutoff time
  - When **true** AND Trail Distance > 0: Positions enter "trailing mode" at cutoff

**Trail Distance** (`InpTrailDistance`)
- **Type:** Double (points)
- **Default:** 0 (disabled)
- **Function:**
  - Only active if `Use Trailing Stop After Cutoff` = true
  - At cutoff time, instead of closing, the EA tracks the maximum profit reached
  - If price retraces by this many points from max profit, position closes
  - Allows profitable trades to run while protecting gains

**Trailing Stop Example:**
```
Trail Distance = 50 points
Cutoff reached: Position at +$50 profit
Price continues: Max profit reaches +$150 (tracked)
Price retraces: Drops back to +$100 (50 point retrace)
→ Position closes at +$100 (protected $50 of additional gains)
```

---

### Dashboard Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| Dashboard X Position | int | 10 | X coordinate (pixels from left) |
| Dashboard Y Position | int | 30 | Y coordinate (pixels from top) |
| Row Height | int | 20 | Height of each position row |
| **Dashboard Background Color** | color | C'30,30,30' | **NEW:** Main background color (dark gray) |
| Normal Color | color | clrWhite | Standard text color |
| Warning Color | color | clrYellow | Approaching cutoff (< warning seconds) |
| Critical Color | color | clrRed | Very close to cutoff (< 5 seconds) |
| Profit Color | color | clrLime | Positive P&L |
| Loss Color | color | clrSalmon | Negative P&L |

---

### Recovery Tracking

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| Enable Loss Tracking | bool | true | Track losses for recovery analysis |
| Recovery Data File | string | "loss_recovery.csv" | CSV file for loss records |
| Recovery Lot Multiplier | double | 1.5 | Multiplier for recovery position sizing |

---

## Dashboard Display

The dashboard shows:

```
+----------------------------------------------------------+
|  TIME CUTOFF MANAGER (Gold header)                       |
+----------------------------------------------------------+
| Ticket | Symbol | Type | Lots | P&L | Countdown | Status |
+----------------------------------------------------------+
| 12345  | XAUUSD | BUY  | 0.10 | $25 | 2m 30s    | ACTIVE |
| 12346  | XAUUSD | SELL | 0.10 | $-5 | 45s       | ACTIVE | ← Yellow (warning)
| 12347  | XAUUSD | BUY  | 0.10 | $15 | TRAILING  | TRAILING | ← Aqua (trailing mode)
+----------------------------------------------------------+
| Recovery Loss: $45.50                                    |
+----------------------------------------------------------+
```

**Status Colors:**
- **White** = Normal operation
- **Yellow** = Warning (approaching cutoff)
- **Red** = Critical (< 5 seconds)
- **Aqua** = Trailing mode active
- **Lime** = Profit (P&L column)
- **Salmon** = Loss (P&L column)

---

## Usage Examples

### Example 1: Monitor All GU Asia Positions (by Magic Number)
```
Filter Method: Magic Number
Filter Value: 11,21,31
Duration Type: Minutes
Close Duration: 2
Use Partial Close: false
Warning Seconds: 10
```

### Example 2: Monitor by Comment (All Asia Session EAs)
```
Filter Method: Comment Contains
Filter Value: GU_ASIA
Duration Type: Minutes
Close Duration: 5
Use Partial Close: false
```

### Example 3: Monitor Specific Symbol
```
Filter Method: Symbol
Filter Value: XAUUSDp
Duration Type: Hours
Close Duration: 1
Use Partial Close: false
```

### Example 4: Conservative with Trailing Stop
```
Filter Method: Magic Number
Filter Value: 0 (all positions)
Duration Type: Minutes
Close Duration: 10
Use Partial Close: false
Use Trailing Stop After Cutoff: true
Trail Distance: 50 (points)
```

### Example 5: Two-Stage Close (Partial + Final)
```
Filter Method: Magic Number
Filter Value: 11,12,13
Duration Type: Minutes
Close Duration: 2
Use Partial Close: true
Partial Close Duration: 1
Partial Close %: 50
Warning Seconds: 10
```
**Behavior:** 0.10 lot position → 0.05 lot closed at 1 min, 0.05 lot closed at 2 min

---

## Important Notes

1. **Single Filter Only:** Only ONE filter method is active at a time. Use the dropdown to select your preferred method.

2. **Magic Number "0":** Entering "0" in Filter Value with Magic Number method monitors ALL positions regardless of magic number.

3. **Trailing Mode:** When trailing mode activates, the position stays open beyond the cutoff time until:
   - Price retraces by Trail Distance from max profit, OR
   - Position is closed manually or by another EA

4. **Time Calculation:** Cutoff time is calculated from position open time + duration. Changing settings does NOT affect already-tracked positions.

5. **Partial Close:** Set `Partial Close Duration` = 0 to disable. Partial close must be earlier than final close duration. If remaining volume after partial close would be below broker minimum, full close is executed instead.

5. **CPU Usage:** TCM updates once per second (not every tick) to minimize CPU usage.

---

## Changes from v1.0 to v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Magic Number Input | Integer (single) | String (comma-separated) |
| Filter Method | Multiple active (confusing) | Dropdown (single method) |
| Duration | Seconds only | Dropdown (Seconds/Minutes/Hours) |
| Dashboard Background | Hardcoded | Configurable input |
| Trailing Mode | Basic | Enhanced with visual indicator |
| Warning System | Simple | Clear documentation |

## Changes from v2.0 to v2.1 (Production Hardening)

| Feature | v2.0 | v2.1 |
|---------|------|------|
| Close Timing | Sleep(100) blocking | State machine with retry logic |
| Position Selection | Single select | Double-check verification |
| Multi-Symbol | Current only | SymbolSelect() for all monitored |
| Connection Handling | None | Validate on init and periodic checks |
| Error Codes | Hardcoded 4753 | TRADE_RETCODE constants |
| File Access | Direct | Mutex-protected for multi-instance |
| Dashboard | Recreate every second | Update existing objects |
| Memory | Unlimited growth | Periodic cleanup every 5 min |
| Spread Filter | None | Max spread threshold for closes |

## Changes from v2.1 to v2.2 (Partial Close)

| Feature | v2.1 | v2.2 |
|---------|------|------|
| Close Stages | Single | Two-stage (partial + final) with master switch |
| Duration Input | InpDurationValue | InpCloseDuration + InpPartialCloseDuration |
| Partial Close | Not available | Configurable % at mid-duration, enabled via `UsePartialClose` |
| Dashboard | Basic status | Shows "P-CLOSED" for partial state |
| Lot Display | Current only | Shows * after partial close |

---

## Installation

1. Copy `TimeCutoffManager.mq5` to `MQL5/Experts/`
2. Compile in MetaEditor (F7)
3. Attach to any chart (recommend separate chart for monitoring)
4. Configure inputs for your strategy
5. Run 3 instances for 3 sessions (each with different filter values)
