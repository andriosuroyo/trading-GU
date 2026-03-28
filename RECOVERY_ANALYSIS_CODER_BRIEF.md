# RecoveryAnalysis Script - Coder Brief

## Current Issue
The `qa_daily_recovery.py` script has a bug in layer selection logic. It's including positions from OTHER loss baskets as "layers" for the current basket.

## Problem Example (B010 on March 23, 2026)
```
Basket B010:
- CloseTime: 11:48:32
- RecoveryTime: 1.6 minutes
- LayerCount: 3
- Layer1Time: 11:59:00 (10 min AFTER basket closed!)
- Layer2Time: 12:32:00 (44 min after!)
- Layer3Time: 13:03:00 (75 min after!)
```

**These "layers" are actually positions from OTHER baskets that opened later in the day.**

## Root Cause
The current layer selection logic in `analyze_basket_for_window()`:
```python
same_direction_positions = []
for pos in all_positions:
    if pos["ticket"] == primary["ticket"]:  # Skip primary
        continue
    if pos["direction"] != direction:      # Same direction only
        continue
    if not (close_time < pos["open_time"] <= recovery_deadline):  # Within window
        continue
    same_direction_positions.append(pos)
```

This selects ALL same-direction positions opened after the basket's close time, regardless of which basket they belong to.

## What We Want to Achieve

### High-Level Goal
For each loss basket, identify "layers" - positions that would have been opened if we were adding to a losing position using an ATR-based spacing strategy.

### Correct Layer Definition
A position should be considered a "layer" for basket X IF AND ONLY IF:
1. Same direction as the basket (BUY/SELL)
2. Opens after the basket's primary position closes (`close_time < open_time`)
3. Opens before recovery OR before window deadline (`open_time <= recovery_time`)
4. **Must be part of the SAME loss sequence** (explained below)

### The "Same Loss Sequence" Challenge

This is the core problem. How do we know if a position belongs to "basket X's layer sequence" vs "a new basket Y"?

**Key Insight:**
- A "loss basket" is defined as: positions that close at roughly the same time (within 5 minutes of first position closing)
- If basket X closes at 11:48:32, and a new position opens at 11:59:00 (10+ minutes later), it likely belongs to a DIFFERENT basket
- But our current code doesn't track this relationship

### Suggested Solution Approach

**Option 1: Track Position-to-Basket Mapping (Recommended)**

1. When identifying loss baskets, create a mapping: `position_ticket -> basket_id`
2. In `analyze_basket_for_window()`, only consider positions that map to the CURRENT basket_id
3. This ensures layers are only from the same basket

**Option 2: Time-Proximity Filtering**

1. A layer must open within X minutes of the basket's close_time
2. X could be: basket_duration + buffer, or ATR-based calculation
3. This might incorrectly filter legitimate layers though

**Option 3: Magic Number + Time Window**

1. Only consider positions with the same Magic number as the basket
2. Plus time constraints (already in place)
3. Might miss layers if Magic numbers vary

## Current Data Structures

### Basket Structure
```python
basket = [
    {
        "ticket": int,
        "magic": int,
        "open_time": datetime,
        "close_time": datetime,
        "open_price": float,
        "close_price": float,
        "direction": "BUY" | "SELL",
        "profit": float,
        "volume": float
    },
    # ... more positions in same basket
]
```

### identify_loss_baskets() Logic
```python
def identify_loss_baskets(positions):
    """
    Groups positions into baskets where:
    - Positions close within 5 minutes of first position's close time
    - Same direction (BUY/SELL)
    """
    # Returns: List[basket]
```

## Required Changes

### 1. Modify identify_loss_baskets()
Return both baskets AND a position-to-basket mapping:
```python
def identify_loss_baskets(positions):
    # ... existing logic ...
    # Return: (baskets, ticket_to_basket_map)
    # where ticket_to_basket_map = {position_ticket: basket_id}
```

### 2. Modify analyze_basket_for_window()
Add parameter for ticket-to-basket mapping, use it to filter layers:
```python
def analyze_basket_for_window(basket, all_positions, basket_num, recovery_minutes, ticket_to_basket_map):
    # ...
    # When selecting layers, only include positions where:
    # ticket_to_basket_map.get(pos["ticket"]) == basket_id
```

### 3. Update generate_recovery_analysis()
Pass the mapping through to analyze_basket_for_window().

## Testing

### Test Case: B010 (March 23, 2026)
- Basket closes at 11:48:32
- Should have 0 layers (no positions opened between 11:48:32 and recovery at ~11:50)
- Currently shows 3 incorrect layers at 11:59, 12:32, 13:03

### Test Case: B001 (March 23, 2026)  
- Basket closes at 02:58:00
- Not recovered within 120min
- Should show layers from 02:58:00 to 04:58:00 only IF they belong to same basket sequence

## Files to Modify
- `qa_daily_recovery.py` (main script)

## Related Context
- ATR_MULTIPLIER = 2.0 (for layer spacing)
- MAX_LAYERS = 5
- Basket window = 5 minutes (positions closing within 5 min group together)
- Recovery windows: 60, 120, 180, 240, 300, 360, 420, 480 minutes

## Deliverable
Fix the layer selection logic so that:
1. Layers are only selected from positions belonging to the SAME basket
2. B010 (and similar baskets) show correct layer count (likely 0)
3. Existing functionality (RecoveryTime, RecoveryClose, TotalPL, LayerXPL) continues to work
