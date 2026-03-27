# RGU EA Specification v2.0
**Recovery GU Expert Advisor - Layered Entry with ATR-Based Spacing**

## Overview
RGU monitors positions opened by GU EAs and automatically opens recovery trades when a position hits SL. Recovery trades target the original position's OpenPrice (the "magnet").

**Key Innovation:** Instead of immediate entry at SL hit, RGU waits for **GU confirmation** (same-direction GU positions opening at better prices) and uses **ATR-based dynamic entry spacing** for optimal layering.

---

## Core Logic

### 1. Position Detection (Loss Detection)
- Monitor all positions with comment containing "GU_"
- Detect when a GU position closes with loss (time-based SL hit)
- Extract: Ticket, Direction, OpenPrice, ClosePrice, CloseTime, Magic, ATR at loss
- **Create RecoveryBasket** (do NOT enter immediately)

### 2. Entry Strategy - ATR-Based Layered Entries

#### 2.1 Entry Distance Calculation
```
EntryDistance = ATR_m1_60 × ATR_Multiplier

Where:
  ATR_m1_60 = ATR in points (e.g., ATR 2.50 = 250 points)
  ATR_Multiplier = 2.0 (default)

Example:
  ATR = 2.50 ($2.50)
  ATR in points = 250
  EntryDistance = 250 × 2 = 500 points
```

#### 2.2 First Entry (Layer 1)
When a BUY loss occurs (price moved down):
- **Wait for:** GU opens a BUY position
- **Condition:** New GU BUY must be ≥ EntryDistance from InitialOpenPrice
- **Logic:** GU is confirming the direction by buying at a better price

**Example:**
- Initial BUY loss: Opened @ 4000.00, SL hit @ 3990.00
- ATR = 2.50 → EntryDistance = 500 points
- Wait for GU to open a BUY position ≥500 points below 4000.00
- GU opens BUY @ 3985.00 (1500 points below InitialOpen) ✓
- **Layer 1 triggered:** RGU opens BUY @ ~3985.00
- Target: 4000.00 (original OpenPrice)
- Layer 1 potential: 1500 points

#### 2.3 Additional Layers (Layer 2, 3, ...)
If price keeps moving in favor:
- **Wait for:** Another GU BUY position opens
- **Condition:** Must be ≥ EntryDistance from **last layer entry**
- **No MaxLayers limit** (limited only by RemTime and Opp)

**Example continued:**
- Layer 1: Entered @ 3985.00
- Price drops to 3970.00
- GU opens BUY @ 3970.00 (1500 points below Layer 1) ✓
- **Layer 2 triggered:** RGU opens BUY @ ~3970.00
- Layer 2 potential: 3000 points
- Total RecoveryBasket potential: 4500 points

#### 2.4 Entry Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| UseConfirmationEntry | bool | true | Wait for GU confirmation |
| ATR_Multiplier | double | 2.0 | Multiplier for ATR-based entry distance |
| EntryDistanceMax | int | 5000 | Max distance (prevent extreme entries) |

### 3. Exit Conditions (RecoveryBasket)
**ALL layers close simultaneously** when ANY of:
1. **Price hits target** (OpenPrice) → WIN
2. **Price hits SL** (10,000 points against) → LOSS  
3. **Time expires** (120 minutes from SL hit) → CLOSE_AT_MARKET
4. **Opposing count ≥ X** (default 10) → CLOSE_AT_MARKET (momentum against)

### 4. RecoveryBasket Concept
- All layers are tracked as a single **RecoveryBasket**
- Same Direction, Same Target (OpenPrice), Same Exit Conditions
- Profit = Sum of all layer profits when target hits
- Dashboard shows aggregated basket view

### 5. Invalidation Rules
Cancel entire RecoveryBasket if:
- Opposing positions opened ≥ X (default 10)
- Time since SL hit > 120 minutes without hitting target
- Price moves beyond EntryDistanceMax without GU confirmation

---

## Historical Simulation Results

Based on March 20, 23, 24 data (186 losses):

### Layer Distribution
| Layers | Count | Percentage | Outcome |
|--------|-------|------------|---------|
| 0 | 6 | 3.2% | No entry triggered |
| 1 | 63 | 33.9% | 46 REC / 17 LOST |
| 2 | 43 | 23.1% | 39 REC / 4 LOST |
| 3 | 13 | 7.0% | 13 REC / 0 LOST |
| 4 | 61 | 32.8% | 43 REC / 18 LOST |

**Maximum Layers Observed: 4** (both RECOVERED and LOST)

### Performance
- **Entry Rate:** 96.8% (180/186 had ≥1 layer)
- **Recovery Rate:** 78.3% (141/180 with layers recovered)
- **Average Layers:** 2.38 (recovered), 2.49 (lost)

### Profit Potential (with ATR×2 spacing)
- **Total Potential:** 3,366,576 points
- **Average per Position:** 18,703 points
- **Recovered Positions:** 2,777,452 points
- **Lost Positions:** 589,124 points

### MAE Analysis (Maximum Adverse Excursion)

| Metric | Value |
|--------|-------|
| Mean Max MAE | 12,380 points |
| Median Max MAE | 9,027 points |
| **95th Percentile** | **30,797 points** |
| **Maximum Observed** | **41,425 points** |

**MAE by Layer Count:**
- 1 layer: Mean=13,402, Max=41,425
- 2 layers: Mean=9,300, Max=18,460
- 3 layers: Mean=5,643, Max=8,363
- 4 layers: Mean=14,932, Max=34,131

**Key Finding:** 2-3 layers show lowest MAE (better averaging)

---

## Dashboard Display

### Standard Mode (Single Layer View)
```
+----------------------------------------------------------+
|  RGU - Recovery Manager         [Status: ACTIVE]         |
+----------------------------------------------------------+
| #  | Dir | Target  | DistTo | RemTime  | Opp | Status    |
+----------------------------------------------------------+
| 1  | BUY | 4000.00 | 1500   | 1:47:23  | 2   | ACTIVE    |
+----------------------------------------------------------+
|  Active: 1 | Layers: 2 | TotalPotential: 4500          |
+----------------------------------------------------------+
```

### Layered Mode (Detailed View)
```
+-----------------------------------------------------------------------+
|  RGU - Recovery Manager - LAYERED MODE      [Status: ACTIVE]          |
+-----------------------------------------------------------------------+
| #  | Dir | Target  | L1@    | L2@    | L3@    | L4@    | TotalDist   |
+-----------------------------------------------------------------------+
| 1  | BUY | 4000.00 | 3985.0 | 3970.0 | 3955.0 | --     | 6000        |
+-----------------------------------------------------------------------+
|  RemTime: 1:47:23 | Opp: 2 | Status: ACTIVE | Layers: 3              |
+-----------------------------------------------------------------------+
```

### Column Definitions
| Column | Description |
|--------|-------------|
| **#** | RecoveryBasket sequence number |
| **Dir** | Direction (Green=BUY, Red=SELL) |
| **Target** | Original OpenPrice (magnet) |
| **DistTo** | Distance from current price to target (integer points) |
| **L1@, L2@, L3@, L4@** | Layer entry prices (-- if not filled) |
| **TotalDist** | Sum of all layer distances (total potential) |
| **RemTime** | H:MM:SS countdown (120min from SL hit) |
| **Opp** | Opposing positions count |
| **Status** | ACTIVE/WARN/CRITICAL/CLOSED |

### Status Logic (Most Dire Wins)
| RemTime | OppCount | Result |
|---------|----------|--------|
| White (>30min) | White (<5) | **ACTIVE** (White) |
| White | Yellow (5-7) | **WARN** (Yellow) |
| Yellow (<30min) | White | **WARN** (Yellow) |
| Yellow | Red (≥8) | **CRITICAL** (Red) |
| Red (<5min) | Any | **CRITICAL** (Red) |

---

## Risk Management

### Recommended SL for RecoveryBasket
| SL Level | Coverage | Recommendation |
|----------|----------|----------------|
| 10,000 points | ~80% | Conservative |
| 15,000 points | ~90% | Moderate |
| **30,000 points** | **~95%** | **Recommended** |
| 42,000 points | 100% | Maximum observed |

Given 95th percentile MAE is 30,797 points, a **30,000 point SL** covers most scenarios.

### Position Sizing
- **RecoveryBasket Total Risk:** 30,000 points × TotalLots
- If using 3 layers × 0.01 lots = 0.03 total
- Risk = 30,000 × 0.03 = $9 per basket

---

## Configuration Summary

| Parameter | Default | Notes |
|-----------|---------|-------|
| ATR_Multiplier | 2.0 | Entry spacing |
| RecoveryWindow | 120 min | Max time for recovery |
| OpposingThreshold | 10 | Invalidate if exceeded |
| RecoveryBasketSL | 30000 | Based on 95th %ile MAE |
| EntryDistanceMax | 5000 | Prevent extreme entries |

---

## Files Created
- `{date}_RecoveryAnalysis.xlsx` - Per-loss recovery data
- `LayeredRecovery_Simulation.csv` - Simulation results
