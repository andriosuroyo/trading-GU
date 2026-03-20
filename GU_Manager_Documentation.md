# GU Manager (GUM) v1.0 Documentation

## Overview

**GU Manager (GUM)** is a comprehensive MetaTrader 5 utility EA that replaces TimeCutoffManager (TCM). It provides advanced position tracking with a state machine for monitoring positions from entry through various outcomes, including a recovery monitoring system for positions that don't hit their TrailStart target.

## Key Capabilities

1. **Live Position Monitoring** - Tracks all positions matching filter criteria in real-time
2. **State Machine** - Manages position status transitions: OPEN → CLEAR/RECOVERY → RECOVERED/LOST
3. **Time-Based Cutoff** - Closes positions after specified duration (legacy TCM feature)
4. **Recovery Monitor** - Tracks RECOVERY positions until they recover or timeout
5. **Data Persistence** - Records all positions to CSV spreadsheet for analysis
6. **Dual Dashboard** - Shows active positions and recovery monitor separately

---

## Position Status States

### State Machine Diagram

```
                    [Position Closes]
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    Profit > 0      -$0.50 < P&L < 0    Loss ≤ -$0.50
    (TrailStart     (Slippage on         (Genuine loss,
     hit)            profitable trade)    no TrailStart)
           │               │               │
           ↓               ↓               ↓
      ┌─────────┐    ┌─────────┐     ┌─────────┐
      │  CLEAR  │    │  CLEAR  │     │ RECOVERY│
      │(success)│    │(success)│     │(monitor)│
      └─────────┘    └─────────┘     └────┬────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
            Price returns           Price returns          Time > X hours
            beyond PriceOpen        toward PriceOpen       (timeout)
            (RECOVERED)             (still monitoring)     
                    │                     │                     │
                    ↓                     ↓                     ↓
              ┌─────────┐              (continue           ┌─────────┐
              │RECOVERED│              monitoring)         │  LOST   │
              │(success)│                                    │(timeout)│
              └─────────┘                                    └─────────┘
```

### Status Definitions

| Status | Description | Dashboard Location |
|--------|-------------|-------------------|
| **OPEN** | Position is within cutoff window, has not yet hit TrailStart | Active Positions panel |
| **CLEAR** | Position closed in profit OR small loss (<$0.50/0.01) - hit TrailStart or near miss due to slippage | Active Positions panel (tinted row) |
| **RECOVERY** | Position closed by time cutoff or SL without hitting TrailStart, being monitored for price recovery | Recovery Monitor panel |
| **RECOVERED** | RECOVERY position where price returned to/beyond original PriceOpen | Not shown (moved to history) |
| **LOST** | RECOVERY position exceeded time limit (X hours) without recovering | Not shown (moved to history) |

---

## Input Parameters

### Position Filter Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Filter Method** | ENUM | Magic Number | How to filter positions: Magic Number, Comment Contains, or Symbol |
| **Filter Value** | String | "11,12,13" | Comma-separated values based on Filter Method |

**Filter Method Details:**
- **Magic Number**: Enter comma-separated magic numbers (e.g., "11,12,13") or "0" for all
- **Comment Contains**: Enter text to match (e.g., "GU_ASIA")
- **Symbol**: Enter comma-separated symbols (e.g., "XAUUSDp,GOLD")

### Time Cutoff Settings (Legacy TCM)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Duration Type** | ENUM | Minutes | Seconds, Minutes, or Hours |
| **Duration Value** | int | 5 | Numeric duration (e.g., 5 minutes) |
| **Warning Seconds** | int | 10 | Seconds before cutoff to show yellow warning |
| **Use Trailing** | bool | false | Enter trailing mode at cutoff instead of closing |
| **Trail Distance** | double | 0 | Points - close if price retraces this much from max profit |

### Recovery Monitor Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Recovery Hours - Asia** | int | 4 | Hours before RECOVERY → LOST (Asia session) |
| **Recovery Hours - London** | int | 4 | Hours before RECOVERY → LOST (London session) |
| **Recovery Hours - NY** | int | 4 | Hours before RECOVERY → LOST (NY session) |
| **Recovery Hours - Full** | int | 4 | Hours before RECOVERY → LOST (Full-time) |
| **CSV File Name** | string | "GUM_Positions.csv" | Master spreadsheet filename |
| **Normalize Lots** | bool | true | Normalize lot size to 0.01 in CSV |

### Dashboard Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| Dashboard X Position | int | 10 | X coordinate (pixels from left) |
| Dashboard Y Position | int | 30 | Y coordinate (pixels from top) |
| Row Height | int | 20 | Height of each position row |
| Background Color | color | C'30,30,30' | Main panel background |
| Normal/Warning/Critical Color | color | various | Text colors for countdown states |
| Profit/Loss Color | color | Lime/Salmon | P&L display colors |
| Recovery/Recovered/Lost Color | color | various | Status indicator colors |

---

## Dashboard Display

### Active Positions Panel

```
+-----------------------------------------------------------------------+
|  GU MANAGER (GUM)                                                     |
+-----------------------------------------------------------------------+
| Ticket | Symbol | Type | Lots |  P&L   | Time/Cutoff | Status | Session |
+-----------------------------------------------------------------------+
| 12345  | XAUUSD | BUY  | 0.10 | $25.50 | 2m 30s      | OPEN   | LONDON  |
| 12346  | XAUUSD | SELL | 0.10 | $-5.20 | 45s         | OPEN   | ASIA    | ← Yellow
| 12347  | XAUUSD | BUY  | 0.10 | $15.00 | CLEAR       | CLEAR  | NY      | ← Aqua
| 12348  | XAUUSD | SELL | 0.10 | $30.00 | TRAILING    | CLEAR  | ASIA    | ← Aqua
+-----------------------------------------------------------------------+
```

**Countdown Colors:**
- **White** = Normal (> warning seconds)
- **Yellow** = Warning (≤ warning seconds)
- **Red** = Critical (≤ 5 seconds)
- **Aqua** = "CLEAR" or "TRAILING" (successful/holding)

**Row Tint:**
- Slightly tinted background for CLEAR positions

### Recovery Monitor Panel

```
+-----------------------------------------------------------------------+
| RECOVERY MONITOR (2)                                                  |
+-----------------------------------------------------------------------+
| Ticket | Symbol | Type | OpenPrice | ClosePrice | Elapsed | Remaining | Current | Status    |
+-----------------------------------------------------------------------+
| 12340  | XAUUSD | BUY  | 2850.50   | 2848.20    | 2h 15m  | 1h 45m    | 2851.00 | MONITORING| ← Current > Open (green)
| 12341  | XAUUSD | SELL | 2860.00   | 2862.50    | 3h 30m  | 30m       | 2859.80 | MONITORING| ← Current < Open (green)
+-----------------------------------------------------------------------+
| Active: 4 | Recovery: 2                                                          |
+-----------------------------------------------------------------------+
```

**Recovery Panel Details:**
- **Elapsed**: Time since position was closed (RECOVERY status)
- **Remaining**: Time until LOST status (based on per-session setting)
- **Current**: Current market price vs original PriceOpen
  - Green = Price has recovered direction (BUY: above open, SELL: below open)
  - Red = Price not yet recovered
- When a position becomes RECOVERED or LOST, it disappears from this panel

---

## CSV Spreadsheet Format

### File Location
`MQL5/Files/GUM_Positions.csv`

### Columns

| Column | Type | Description |
|--------|------|-------------|
| Ticket | ulong | Position ticket number |
| Symbol | string | Trading symbol |
| Type | string | BUY or SELL |
| Session | string | ASIA, LONDON, NY, FULL, or UNKNOWN |
| MagicNumber | long | Position magic number |
| Comment | string | Position comment |
| TimeOpen | datetime | Position open time (Unix timestamp) |
| PriceOpen | double | Position open price |
| LotSize | double | Original lot size |
| LotSizeNormalized | double | Lot size normalized to 0.01 base |
| Status | string | OPEN, CLEAR, RECOVERY, RECOVERED, or LOST |
| TimeClose | datetime | Position close time (if closed) |
| PriceClose | double | Position close price (if closed) |
| Profit | double | Position profit/loss |
| TimeRecovered | datetime | When status changed to RECOVERED |

### Example Rows

```csv
Ticket,Symbol,Type,Session,MagicNumber,Comment,TimeOpen,PriceOpen,LotSize,LotSizeNormalized,Status,TimeClose,PriceClose,Profit,TimeRecovered
12345,XAUUSD,BUY,LONDON,12,GU_LONDON,1710734400,2850.50,0.10,10.00,CLEAR,1710734700,2852.30,18.00,0
12346,XAUUSD,SELL,ASIA,11,GU_ASIA,1710730800,2855.20,0.10,10.00,RECOVERY,1710731100,2857.40,-22.00,0
12347,XAUUSD,BUY,NY,13,GU_NEWYORK,1710738000,2848.00,0.10,10.00,RECOVERED,1710739200,2845.50,-25.00,1710741600
```

---

## Session Detection

GUM automatically detects session from either magic number or comment:

### Magic Number Format
- **Second digit** determines session:
  - `x1` = ASIA (e.g., 11, 21, 31)
  - `x2` = LONDON (e.g., 12, 22, 32)
  - `x3` = NY (e.g., 13, 23, 33)
  - `x0` = FULL (e.g., 10, 20, 30)

### Comment Detection
- Comments containing "ASIA" → ASIA session
- Comments containing "LONDON" → LONDON session
- Comments containing "NEWYORK" or "NY" → NY session
- Comments containing "FULL" → FULL session

---

## Usage Examples

### Example 1: Monitor All London Session Positions

```
Filter Method: Magic Number
Filter Value: 12,22,32
Duration Type: Minutes
Duration Value: 6
Recovery Hours - London: 4
```

### Example 2: Monitor by Comment (All Asia Session EAs)

```
Filter Method: Comment Contains
Filter Value: GU_ASIA
Duration Type: Minutes
Duration Value: 2
Recovery Hours - Asia: 4
```

### Example 3: Conservative with Long Recovery Window

```
Filter Method: Magic Number
Filter Value: 0 (all positions)
Duration Type: Hours
Duration Value: 1
Recovery Hours - All: 8
Use Trailing: true
Trail Distance: 50
```

---

## State Transition Examples

### Example 1: Successful Trade (CLEAR)

1. Position #12345 opens at 2850.50 (BUY), 0.10 lots
2. Price moves up, hits TrailStart at $0.30/0.01 ($3.00 for 0.10 lot position)
3. Trailing stop moves, position eventually closes
4. Final P&L: +$25.00 (normalized: +$2.50/0.01)
5. **Status: CLEAR** (profit > 0, recorded in CSV)

### Example 2: CLEAR with Slippage

1. Position #12346 opens at 2850.50 (SELL), 0.10 lots
2. Price moves down, hits TrailStart at $0.50/0.01 ($5.00 for 0.10 lot position)
3. Trailing stop is active, but sudden spread widening causes close
4. Final P&L: -$2.00 (normalized: -$0.20/0.01, less than $0.50 threshold)
5. **Status: CLEAR** (small loss due to slippage on profitable trade)

### Example 3: RECOVERY (Genuine Loss)

1. Position #12347 opens at 2850.50 (BUY), 0.10 lots
2. Price moves against position immediately, never approaches TrailStart
3. Time cutoff reached (5 minutes), position closed
4. Final P&L: -$8.00 (normalized: -$0.80/0.01, exceeds $0.50 threshold)
5. **Status: RECOVERY** (genuine loss, TrailStart never hit, now monitoring)

### Example 4: Recovery → Recovered

1. Position #12346 opens at 2855.00 (SELL)
2. Price moves against position, never hits TrailStart
3. Time cutoff reached → Position closed at 2857.00
4. Status: **RECOVERY** (now monitoring)
5. Price continues to 2854.00, then 2853.00
6. **Price below PriceOpen** → Status changes to **RECOVERED**
7. TimeRecovered recorded, position moves to history

### Example 5: Recovery → Lost

1. Position #12348 opens at 2860.00 (BUY), already in RECOVERY status
2. Price hovers around 2858-2859, never recovers to 2860 (PriceOpen)
3. 4 hours elapse from close time
4. Status changes to **LOST** (timeout)
5. Position moves to history

---

## File Structure

```
Experts/
└── GUM/
    ├── GUManager.mq5          (Main EA)
    ├── GUM_Structures.mqh     (Enums, structs, helpers)
    ├── GUM_CSVManager.mqh     (CSV I/O operations)
    ├── GUM_PositionManager.mqh (Position tracking & state machine)
    └── GUM_Dashboard.mqh      (Visual display)
```

---

## Installation

1. Copy entire `GUM` folder to `MQL5/Experts/`
2. Open `GUManager.mq5` in MetaEditor
3. Compile (F7)
4. Attach to any chart (recommend separate chart for monitoring)
5. Configure Filter Method and Filter Value for your strategy
6. Set Duration and Recovery Hours per your risk management

---

## Differences from TCM v2.0

| Feature | TCM v2.0 | GUM v1.0 |
|---------|----------|----------|
| Status Tracking | None (only active/closed) | Full state machine (5 states) |
| Recovery Monitoring | Basic loss tracking | Full monitoring with timeout |
| Data Persistence | Simple loss CSV | Comprehensive position database |
| Dashboard | Single panel | Dual panel (Active + Recovery) |
| Session Awareness | None | Per-session recovery settings |
| CLEAR Detection | N/A - status set after close | Based on final P&L after close |

---

## Important Notes

1. **CLEAR Detection**: CLEAR vs RECOVERY is determined **after the position closes**, not in real-time. A position is CLEAR if it closes with profit OR small loss (<$0.50 per 0.01 lot, indicating slippage on a profitable trade). RECOVERY means the loss was ≥$0.50 per 0.01 lot (genuine loss, TrailStart was never hit).

2. **Recovery Time**: "X hours" countdown starts from position close time, not open time.

3. **RECOVERED Trigger**: For BUY positions, price must go **above** PriceOpen. For SELL positions, price must go **below** PriceOpen.

4. **CSV Persistence**: All positions are automatically saved to CSV. Recovery positions are reloaded on restart.

5. **CPU Usage**: GUM updates once per second (not every tick) to minimize CPU usage.

6. **Multiple Instances**: Run separate GUM instances for different sessions with different filter values.

---

**Last Modified:** March 18, 2026
**Version:** 1.0
