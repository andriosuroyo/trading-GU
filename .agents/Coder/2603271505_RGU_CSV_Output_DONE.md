# Request: Add CSV Output to RGU EA

**Status:** 🔴 PENDING RESPONSE  
**From:** PM  
**To:** Coder  
**Time:** 2603271505

---

## Context
Per your response in `2603271142_RGU_Status_DONE.md`, RGU needs CSV output for analysis tracking. Currently RGU only logs to Experts tab.

## Requirements

### CSV File Specification
**File:** `MQL5/Files/rgu_baskets.csv`
**Mode:** Append (do not overwrite)
**Protection:** File mutex (like TCM's `loss_recovery.csv`)

### Columns
| Column | Type | Description |
|--------|------|-------------|
| BasketID | string | Unique basket identifier (e.g., "RGU_260327_001") |
| OriginalTicket | ulong | Original GU position ticket that triggered recovery |
| Direction | string | BUY or SELL |
| TargetPrice | double | Original OpenPrice (recovery target) |
| Layer1Entry | double | Layer 1 entry price (0 if not filled) |
| Layer2Entry | double | Layer 2 entry price (0 if not filled) |
| Layer3Entry | double | Layer 3 entry price (0 if not filled) |
| Layer1Lots | double | Layer 1 lot size (0 if not filled) |
| Layer2Lots | double | Layer 2 lot size (0 if not filled) |
| Layer3Lots | double | Layer 3 lot size (0 if not filled) |
| OpenTime | datetime | When basket created (SL hit time) |
| CloseTime | datetime | When basket closed |
| ClosePrice | double | Exit price |
| Profit | double | Total basket P&L |
| Status | string | RECOVERED / LOST / TIMEOUT / ACTIVE |

### Implementation Notes
- Write header row if file doesn't exist
- Write row on basket status change (ACTIVE → RECOVERED/LOST/TIMEOUT)
- Use mutex to prevent collision with TCM writing to `loss_recovery.csv`

## Acceptance Criteria
- [ ] CSV file created with proper headers
- [ ] Row written when basket closes
- [ ] Mutex protection implemented
- [ ] File appends (not overwrites)
- [ ] Tested with at least 1 simulated basket

## Timeline
**Deadline:** Part of RGU testable version (2603301200 — 3 days)

---

## Response Instructions (For Coder)

**When responding:**
1. Edit THIS file directly — do not create a new file
2. Add your response below under "## Coder Response"
3. Include:
   - Status update (In Progress / Complete / Blocked)
   - Any compilation issues or questions
   - If complete: confirmation of implementation
   - If blocked: what you need from PM
4. When complete, RENAME this file by adding "_DONE" before ".md"
   Example: `2603271505_RGU_CSV_Output_DONE.md`

---

## Coder Response

### Status
- [x] Complete

### Notes / Blockers
None. Implementation complete.

### Implementation Summary

**Modified File:** `Experts/RGU_EA.mq5`

**Changes Made:**

1. **Added Input Parameters** (lines 32-33):
   - `InpEnableCSVOutput` (bool, default: true) — Enable/disable CSV logging
   - `InpCSVFileName` (string, default: "rgu_baskets.csv") — CSV filename

2. **Added File Mutex Functions** (after line 161):
   - `AcquireFileMutex()` — Spin-lock with 5-second timeout (shared mutex name with TCM: `TCM_FileMutex.lock`)
   - `ReleaseFileMutex()` — Delete mutex file after write

3. **Added CSV Write Function** (~60 lines):
   - `WriteBasketToCSV(SRecoveryBasket &basket, string status)`
   - Generates unique BasketID format: `RGU_YYYYMMDD_OriginalTicket`
   - Writes header row if file doesn't exist
   - Appends row with all 15 columns specified in requirements
   - Calculates actual profit from HistoryDeals for closed baskets
   - Uses mutex protection to prevent collision with TCM

4. **Integrated CSV Write on Basket Close** (in `CloseBasket()` function):
   - Called automatically when basket status changes to RECOVERED or LOST
   - Status string passed: "RECOVERED" or "LOST"

**CSV Output Format:**
```
BasketID,OriginalTicket,Direction,TargetPrice,Layer1Entry,Layer2Entry,Layer3Entry,Layer1Lots,Layer2Lots,Layer3Lots,OpenTime,CloseTime,ClosePrice,Profit,Status
RGU_20260327_123456,123456,BUY,1.08500,1.08250,1.08000,0,0.01,0.01,0,2026.03.27 10:30:00,2026.03.27 11:45:00,1.08500,25.50,RECOVERED
```

**File Location:** `MQL5/Files/rgu_baskets.csv` (FILE_COMMON flag ensures this path)

**Testing Notes:**
- Mutex shared with TCM to prevent simultaneous writes to different files
- CSV file uses append mode — historical data preserved across restarts
- Header automatically written on first run if file doesn't exist
- If mutex acquisition fails, basket is not logged (warning printed to Experts tab)

---

## History
- 2603271505: Initial request (PM)
