# RGU EA Specification
**Recovery GU Expert Advisor**

## Overview
RGU monitors positions opened by GU EAs and automatically opens recovery trades when a position hits SL. Recovery trades target the original position's OpenPrice (the "magnet").

---

## Core Logic

### 1. Position Detection (Loss Detection)
- Monitor all positions with comment containing "GU_"
- Detect when a GU position closes with loss (time-based SL hit)
- Extract: Ticket, Direction, OpenPrice, ClosePrice, CloseTime, Magic
- **Create Recovery Opportunity** (do NOT enter immediately)

### 2. Entry Strategy - Confirmation-Based Layered Entries

Instead of entering immediately at SL hit, RGU **waits for confirmation** from same-direction GU positions.

#### 2.1 First Entry (Layer 1)
When a BUY loss occurs (price moved down):
- **Wait for:** GU opens a BUY position
- **Condition:** New GU BUY must be sufficiently far from InitialOpenPrice
- **Entry Distance Threshold:** Minimum distance from InitialOpenPrice (e.g., 500-1000 points)
- **Logic:** GU is confirming the direction by buying at a better price

**Example:**
- Initial BUY loss: Opened @ 4000.00, SL hit @ 3990.00 (1000 points loss)
- Wait for GU to open a BUY position
- GU opens BUY @ 3985.00 (1500 points below InitialOpen)
- **Entry triggered:** RGU opens BUY @ ~3985.00
- Target: 4000.00 (original OpenPrice)
- Potential profit: 1500 points (vs 1000 if entered at SL)

#### 2.2 Additional Layers (Layer 2, 3, ...)
If price keeps moving in favor (lower for BUY recovery):
- **Wait for:** Another GU BUY position opens
- **Condition:** Must be sufficiently far from **last RecoveryPosition** entry
- **Entry Distance Threshold:** Same minimum distance
- **Max Layers:** Configurable (default 3)

**Example continued:**
- Layer 1: Entered @ 3985.00
- Price drops further to 3970.00
- GU opens another BUY @ 3970.00
- **Layer 2 triggered:** RGU opens BUY @ ~3970.00
- Target: 4000.00 (same magnet)
- Layer 1 potential: 1500 points
- Layer 2 potential: 3000 points

#### 2.3 Entry Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| UseConfirmationEntry | bool | true | Wait for GU confirmation instead of immediate entry |
| EntryDistanceMin | int | 1000 | Min points from reference price to trigger entry |
| EntryDistanceMax | int | 5000 | Max points (prevent entry too far) |
| MaxLayers | int | 3 | Maximum layered recovery positions |
| LayerSpacing | int | 1000 | Min points between layers |

### 3. Exit Conditions
Recovery position closes when ANY of:
1. **Price hits target** (OpenPrice) → WIN
2. **Price hits SL** (10,000 points against) → LOSS
3. **Time expires** (120 minutes elapsed) → CLOSE_AT_MARKET
4. **Opposing count ≥ X** (default 10) → CLOSE_AT_MARKET (momentum against)

### 4. Invalidation Rules
Cancel recovery opportunity if:
- Opposing positions opened ≥ X (default 10)
- Time since SL hit > 120 minutes without hitting target
- Price moves beyond EntryDistanceMax without GU confirmation

### 5. Dashboard for Layered Entries
Additional columns for layered recovery:

```
+-----------------------------------------------------------------------+
|  RGU - Recovery Manager - LAYERED MODE      [Status: ACTIVE]          |
+-----------------------------------------------------------------------+
| #  | Dir | Target  | L1@    | L2@    | L3@    | TotalDist | Status   |
+-----------------------------------------------------------------------+
| 1  | BUY | 4000.00 | 3985.0 | 3970.0 | --     | 3000      | ACTIVE   |
+-----------------------------------------------------------------------+
|  Active: 1 | Total Layers: 2 | Avg Entry: 3977.5                   |
+-----------------------------------------------------------------------+
```

| Column | Description |
|--------|-------------|
| **Target** | Original OpenPrice (magnet) |
| **L1@** | Layer 1 entry price |
| **L2@** | Layer 2 entry price (or --) |
| **L3@** | Layer 3 entry price (or --) |
| **TotalDist** | Total exposure in points (sum of all layers) |

### 6. Profit Calculation for Layers
When target is hit, ALL layers close simultaneously:
```
Layer 1 Profit: (Target - L1_Entry) × 100 × Lots
Layer 2 Profit: (Target - L2_Entry) × 100 × Lots
Total Profit = Sum of all layers

Example:
  Target: 4000.00
  L1 @ 3985.00: (4000 - 3985) × 100 = 1500 points
  L2 @ 3970.00: (4000 - 3970) × 100 = 3000 points
  Total: 4500 points (vs 1000 points with single entry)
```

---

## Dashboard Display

### Layout
```
+----------------------------------------------------------+
|  RGU - Recovery Manager         [Status: ACTIVE]         |
+----------------------------------------------------------+
| #  | Dir | OpenPrice | DistTo | RemTime  | Opp | Status  |
+----------------------------------------------------------+
| 1  | BUY | 4555.98   | +52.3  | 1:47:23  | 2   | ACTIVE  |
| 2  | SELL| 4338.41   | -18.7  | 0:23:45  | 8   | WARN    |
+----------------------------------------------------------+
|  Active: 2 | Pending: 0 | Closed Today: 5               |
+----------------------------------------------------------+
```

### Column Definitions

| Column | Description | Format |
|--------|-------------|--------|
| **#** | Recovery trade sequence number | Integer |
| **Dir** | Direction (BUY/SELL) | Text (Green=Buy, Red=Sell) |
| **OpenPrice** | Target price (original OpenPrice) | Price (2 decimals) |
| **DistTo** | Distance from current price to target | Points (always positive), colored by direction |
| **RemTime** | Time remaining until 120min expiry | H:MM:SS countdown |
| **Opp** | Opposing positions count since loss | Integer (Red if ≥8, Yellow if ≥5) |
| **Status** | Current state | ACTIVE/WARN/CRITICAL/CLOSED |

### Status Determination (Most Dire Wins)
Status is determined by the **worst** condition between RemTime and Opp:

| RemTime Status | Opp Status | **Final Status** |
|----------------|------------|------------------|
| White (ok) | White (ok) | **ACTIVE** (White) |
| White (ok) | Yellow (warn) | **WARN** (Yellow) |
| Yellow (warn) | White (ok) | **WARN** (Yellow) |
| Yellow (warn) | Red (crit) | **CRITICAL** (Red) |
| Red (crit) | Yellow (warn) | **CRITICAL** (Red) |
| Red (crit) | Red (crit) | **CRITICAL** (Red) |

- **ACTIVE** (White): RemTime >30min AND Opp <5
- **WARN** (Yellow): Either RemTime <30min OR Opp 5-7
- **CRITICAL** (Red): Either RemTime <5min OR Opp ≥8
- **CLOSED** (Gray): Position closed

### Color Coding
- **DistTo:** Always positive value, colored by Direction (Green=BUY, Red=SELL)
- **RemTime:** White → Yellow (<30min) → Red (<5min)
- **Opp:** White → Yellow (5-7) → Red (≥8)

---

## Input Parameters

### Recovery Settings
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| RecoveryWindow | int | 120 | Max minutes for recovery (0=disabled) |
| OpposingThreshold | int | 10 | Max opposing positions before invalidate |
| RecoverySL | double | 10000 | Fixed SL in points for recovery trades |
| UseTrailing | bool | false | Enable trailing stop after half window |

### Detection Settings
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| CommentFilter | string | "GU_" | Filter for GU positions to monitor |
| MagicFilter | string | "" | Specific magic numbers (empty=all) |
| MinLossPoints | double | 50 | Min loss to trigger recovery |

### Risk Settings
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| RecoveryLotSize | double | 0.01 | Fixed lot size for recovery |
| UseLotMultiplier | bool | false | Multiply by original position lot |
| LotMultiplier | double | 1.0 | Multiplier if enabled |
| MaxConcurrent | int | 5 | Max recovery trades at once |
| MaxDailyRecovery | int | 10 | Max recovery trades per day |

### Dashboard Settings
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| DashboardX | int | 10 | X position on chart |
| DashboardY | int | 30 | Y position on chart |
| RowHeight | int | 18 | Row spacing |
| FontSize | int | 10 | Font size |
| ShowClosed | bool | true | Show recently closed recoveries |

---

## Technical Implementation

### Opposing Position Count
```
For each position opened since loss_time:
    If position.comment contains "GU_" AND
       position.direction != recovery_direction AND
       position.open_time > loss_close_time:
        opposing_count++
```

### DistanceTo Calculation
```
distance = round(abs(target_price - current_price) * 100)  // integer points

Example:
  BUY Recovery: Target=4000.00, Current=3990.00
  Distance = round(abs(4000.00 - 3990.00) * 100) = 1000 points
  
  BUY Recovery: Target=4559.09, Current=4564.25
  Distance = round(abs(4559.09 - 4564.25) * 100) = 516 points
```

**Note:** DistTo is always displayed as a whole number (integer points), no decimals.

### RemainderTime Countdown
```
expire_time = loss_close_time + 120 minutes
remaining = expire_time - current_time

Format: H:MM:SS
Example: 1:47:23 (1 hour, 47 min, 23 sec)
```

### File Logging
- CSV log: `RGU_Log_YYYYMMDD.csv`
- Columns: Timestamp, OriginalTicket, RecoveryTicket, Direction, EntryPrice, TargetPrice, ExitPrice, ExitReason, Profit

---

## Example Workflow

### Scenario: BUY position hits SL
1. **14:01:09** - GU BUY position opened @ 4559.09
2. **14:11:09** - SL hit @ 4564.25 (loss)
3. **14:11:10** - RGU opens BUY recovery @ ~4564.25
   - Target: 4559.09
   - SL: 4574.25 (4564.25 + 100 points = 10,000 points SL)
   - Expire: 16:11:09
4. **Dashboard shows:**
   - Dir: BUY
   - OpenPrice: 4559.09
   - DistTo: -52.3 (52 points against)
   - RemTime: 1:59:59 (counting down)
   - Opp: 0
5. **15:17:00** - 4 BUY positions opened by other GU sets
   - Dashboard: Opp = 4
6. **15:23:05** - Price hits 4559.09
   - Recovery closes with +52.3 points profit
   - Dashboard updates to CLOSED

---

## Risk Warnings

1. **Large SL:** 10,000 point SL requires significant margin
2. **Concurrent recoveries:** Multiple losses can stack up
3. **Opposing momentum:** X threshold may filter valid recoveries
4. **Time decay:** 120min may not be enough in ranging markets

---

## Version History
- **v1.0** - Initial specification
