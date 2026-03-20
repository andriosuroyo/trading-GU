# RFC 001: TCM v2.3.0 — Session-Aware Breakeven & Position Management

> **Status:** READY FOR REVIEW  
> **Target Version:** 2.3.0  
> **Priority:** HIGH  
> **Estimated Implementation:** ~2-3 hours  
> **Estimated Testing:** ~4-6 hours

---

## Executive Summary

TCM v2.3.0 expands from a "position closer" to a "session-aware position controller." Key additions:

1. **Automatic session detection** based on position open time (GMT conversion)
2. **Per-session timing profiles** (Asia/London/NY independent settings)
3. **True breakeven protection** — SL moved to entry + commission + spread at partial close trigger
4. **Commission auto-detection** with fallback

**Backward Compatibility:** All existing v2.2.0 inputs remain functional. New features require opt-in via `InpUseSessionTiming = true`.

---

## 1. Feature Specifications

### 1.1 Session Detection (Foolproof Method)

**Logic:** Dynamic GMT offset calculation using `TimeCurrent() - TimeGMT()`. Works on any broker, auto-adjusts for DST.

**Session Mapping (GMT Hours):**

| Session | GMT Start | GMT End | Notes |
|---------|-----------|---------|-------|
| ASIA | 02:00 | 07:59 | Matches GU setfile |
| LONDON | 08:00 | 12:59 | Absorbs Asia-London overlap |
| LONDON_NY | 13:00 | 16:59 | Treated as NY per user spec |
| NY | 17:00 | 21:59 | Matches GU setfile |
| NY_ASIA | 22:00 | 01:59 | Overnight (rare for GU) |

**Function Signature:**
```mq5
enum ENUM_SESSION_TYPE
{
    SESSION_ASIA,
    SESSION_LONDON,
    SESSION_LONDON_NY,
    SESSION_NY,
    SESSION_NY_ASIA,
    SESSION_UNKNOWN
};

ENUM_SESSION_TYPE GetSessionForPosition(datetime positionOpenTime);
datetime ServerTimeToGMT(datetime serverTime);
```

### 1.2 Per-Session Configuration

**New Input Structure:**

```mq5
input group "=== Session Detection ==="
input bool   InpUseSessionTiming = true;     // Enable per-session profiles
input bool   InpAutoDetectDST    = true;     // Dynamic GMT offset (recommended)

input group "=== Asia Session (02-08 GMT) ==="
input int    InpAsiaPartialMins    = 2;
input int    InpAsiaFinalMins      = 5;
input double InpAsiaPartialPct     = 50;
input bool   InpAsiaUseBreakeven   = true;

input group "=== London Session (08-13 GMT) ==="
input int    InpLondonPartialMins  = 2;
input int    InpLondonFinalMins    = 5;
input double InpLondonPartialPct   = 50;
input bool   InpLondonUseBreakeven = true;

input group "=== NY Session (13-22 GMT) ==="
input int    InpNYPartialMins      = 2;
input int    InpNYFinalMins        = 5;
input double InpNYPartialPct       = 50;
input bool   InpNYUseBreakeven     = true;
```

### 1.3 True Breakeven Protection

**Trigger:** Simultaneous with partial close at session-specific timing.

**Calculation:**
```mq5
// For BUY position:
double commissionPoints = (commissionPerLot * 2) / (lots * tickValue);
double spreadPoints = entrySpread / _Point;
double totalAdjustment = commissionPoints + spreadPoints;
double breakevenSL = openPrice - (totalAdjustment * _Point);

// For SELL position:
double breakevenSL = openPrice + (totalAdjustment * _Point);
```

**Behavior Matrix:**

| Scenario | Action |
|----------|--------|
| Position at loss at trigger | Set SL to breakeven anyway (hard stop) |
| SL already tighter than breakeven | Skip modify |
| Modify fails (market too close) | Abandon breakeven for this position |
| Modify fails (other reasons) | Retry next tick (max 3 retries) |

**Function Signature:**
```mq5
bool ApplyBreakeven(int positionIdx);
double CalculateBreakevenSL(PositionData &pos);
double DetectCommissionPerLot();
```

### 1.4 Commission Auto-Detection

**Three-Tier Detection:**

1. **SymbolInfo:** `SymbolInfoDouble(SYMBOL_TRADE_COMMISSION)`
2. **History Scan:** Analyze recent closed deals for commission patterns
3. **Fallback:** $4.00 per lot round-trip

**Function Signature:**
```mq5
double g_detectedCommissionPerLot = 0;

void InitializeCommissionDetection();
double DetectCommissionFromSymbolInfo();
double DetectCommissionFromHistory();
```

---

## 2. Architecture Changes

### 2.1 PositionData Structure Extension

```mq5
struct PositionData {
    // ... existing fields ...
    
    // v2.3.0 additions
    ENUM_SESSION_TYPE session;        // Detected session at open
    double            commissionPaid; // Commission per lot for this position
    double            entrySpread;    // Spread at position open (points)
    bool              breakevenApplied; // True if breakeven SL set
    datetime          breakevenTime;  // When breakeven was applied
};
```

### 2.2 State Machine Enhancement

**New State Handling in `ProcessPendingCloses()`:**
- Check for breakeven modify confirmation
- Separate retry logic for breakeven vs close operations

### 2.3 Timing Resolution

**New Function:**
```mq5
void GetTimingForSession(ENUM_SESSION_TYPE session, 
                         int &partialMins, 
                         int &finalMins, 
                         double &partialPct,
                         bool &useBreakeven);
```

---

## 3. Modified Functions

### 3.1 `AddPosition()` — Extended

```mq5
void AddPosition(ulong ticket)
{
    // ... existing logic ...
    
    // v2.3.0: Detect session and commission
    g_positions[idx].session = GetSessionForPosition(g_positions[idx].openTime);
    g_positions[idx].commissionPaid = g_detectedCommissionPerLot;
    g_positions[idx].entrySpread = GetSpreadAtTime(g_positions[idx].openTime);
    g_positions[idx].breakevenApplied = false;
    
    // Get session-specific timing
    int partialMins, finalMins;
    double partialPct;
    bool useBreakeven;
    GetTimingForSession(g_positions[idx].session, partialMins, finalMins, 
                        partialPct, useBreakeven);
    
    // Calculate cutoff times using session-specific values
    // ... (instead of global inputs) ...
}
```

### 3.2 `CheckCutoffs()` — Enhanced

```mq5
void CheckCutoffs()
{
    // ... existing checks ...
    
    // At partial close trigger:
    if(now >= g_positions[i].partialCutoffTime && !g_positions[i].partialCloseDone)
    {
        // v2.3.0: Apply breakeven simultaneously
        if(ShouldApplyBreakeven(i))
        {
            ApplyBreakeven(i); // Non-blocking, proceeds regardless of result
        }
        
        PartialClosePosition(i); // Existing function
    }
}
```

### 3.3 `PartialClosePosition()` — Unchanged Interface

- No changes to function signature
- Internally uses `g_positions[idx].lots` (already accounting for partial close)

---

## 4. New Functions

### 4.1 Session Detection

```mq5
//+------------------------------------------------------------------+
//| Convert server time to GMT using dynamic offset                   |
//+------------------------------------------------------------------+
datetime ServerTimeToGMT(datetime serverTime)
{
    datetime currentServer = TimeCurrent();
    datetime currentGMT = TimeGMT();
    long offsetSeconds = currentServer - currentGMT;
    return serverTime - offsetSeconds;
}

//+------------------------------------------------------------------+
//| Determine session type from position open time                    |
//+------------------------------------------------------------------+
ENUM_SESSION_TYPE GetSessionForPosition(datetime positionOpenTime)
{
    datetime gmtTime = ServerTimeToGMT(positionOpenTime);
    MqlDateTime dt;
    TimeToStruct(gmtTime, dt);
    
    int hour = dt.hour;
    
    if(hour >= 2 && hour < 8)  return SESSION_ASIA;
    if(hour >= 8 && hour < 13) return SESSION_LONDON;
    if(hour >= 13 && hour < 17) return SESSION_LONDON_NY;
    if(hour >= 17 && hour < 22) return SESSION_NY;
    
    return SESSION_NY_ASIA;
}

//+------------------------------------------------------------------+
//| Get timing parameters for session                                 |
//+------------------------------------------------------------------+
void GetTimingForSession(ENUM_SESSION_TYPE session,
                         int &partialMins,
                         int &finalMins,
                         double &partialPct,
                         bool &useBreakeven)
{
    if(!InpUseSessionTiming)
    {
        // Fallback to legacy global inputs
        partialMins = InpPartialCloseDuration;
        finalMins = InpCloseDuration;
        partialPct = InpPartialClosePct;
        useBreakeven = false; // Breakeven requires session mode
        return;
    }
    
    switch(session)
    {
        case SESSION_ASIA:
            partialMins = InpAsiaPartialMins;
            finalMins = InpAsiaFinalMins;
            partialPct = InpAsiaPartialPct;
            useBreakeven = InpAsiaUseBreakeven;
            break;
            
        case SESSION_LONDON:
        case SESSION_LONDON_NY:
            partialMins = InpLondonPartialMins;
            finalMins = InpLondonFinalMins;
            partialPct = InpLondonPartialPct;
            useBreakeven = InpLondonUseBreakeven;
            break;
            
        case SESSION_NY:
        case SESSION_NY_ASIA:
            partialMins = InpNYPartialMins;
            finalMins = InpNYFinalMins;
            partialPct = InpNYPartialPct;
            useBreakeven = InpNYUseBreakeven;
            break;
            
        default:
            partialMins = InpPartialCloseDuration;
            finalMins = InpCloseDuration;
            partialPct = InpPartialClosePct;
            useBreakeven = false;
    }
}
```

### 4.2 Breakeven Logic

```mq5
//+------------------------------------------------------------------+
//| Calculate true breakeven price including costs                    |
//+------------------------------------------------------------------+
double CalculateBreakevenSL(PositionData &pos)
{
    double tickSize = SymbolInfoDouble(pos.symbol, SYMBOL_TRADE_TICK_SIZE);
    double tickValue = SymbolInfoDouble(pos.symbol, SYMBOL_TRADE_TICK_VALUE);
    
    if(tickSize <= 0 || tickValue <= 0)
    {
        Print("ERROR: Invalid tick data for ", pos.symbol);
        return pos.openPrice; // Fallback to entry
    }
    
    // Commission in price points
    double commissionCost = pos.commissionPaid * 2; // Round-trip
    double commissionPoints = commissionCost / (pos.initialLots * tickValue);
    
    // Spread at entry (already in points)
    double spreadPoints = pos.entrySpread;
    
    // Total adjustment
    double totalPoints = commissionPoints + spreadPoints;
    
    // Calculate SL based on position type
    double adjustment = totalPoints * tickSize;
    
    if(pos.type == ORDER_TYPE_BUY)
        return pos.openPrice - adjustment;
    else
        return pos.openPrice + adjustment;
}

//+------------------------------------------------------------------+
//| Check if breakeven should be applied                              |
//+------------------------------------------------------------------+
bool ShouldApplyBreakeven(int idx)
{
    if(g_positions[idx].breakevenApplied) return false;
    if(!InpUseSessionTiming) return false;
    
    // Get session config
    int partialMins, finalMins;
    double partialPct;
    bool useBreakeven;
    GetTimingForSession(g_positions[idx].session, partialMins, finalMins, 
                        partialPct, useBreakeven);
    
    return useBreakeven;
}

//+------------------------------------------------------------------+
//| Apply breakeven stop loss to position                             |
//+------------------------------------------------------------------+
bool ApplyBreakeven(int idx)
{
    ulong ticket = g_positions[idx].ticket;
    
    // Verify position still exists
    if(!PositionSelectByTicket(ticket))
    {
        Print("Position #", ticket, " closed before breakeven could be applied");
        return false;
    }
    
    // Get current SL
    double currentSL = PositionGetDouble(POSITION_SL);
    
    // Calculate target breakeven SL
    double targetSL = CalculateBreakevenSL(g_positions[idx]);
    
    // Check if current SL is already better (tighter) than breakeven
    if(g_positions[idx].type == ORDER_TYPE_BUY && currentSL > targetSL)
    {
        Print("Position #", ticket, " SL already tighter than breakeven (", 
              currentSL, " > ", targetSL, "). Skipping.");
        g_positions[idx].breakevenApplied = true; // Mark as done
        return true;
    }
    
    if(g_positions[idx].type == ORDER_TYPE_SELL && currentSL < targetSL && currentSL != 0)
    {
        Print("Position #", ticket, " SL already tighter than breakeven (", 
              currentSL, " < ", targetSL, "). Skipping.");
        g_positions[idx].breakevenApplied = true;
        return true;
    }
    
    // Validate price distance from market
    double currentPrice = (g_positions[idx].type == ORDER_TYPE_BUY) ?
                          SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_BID) :
                          SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_ASK);
    
    double freezeLevel = SymbolInfoInteger(g_positions[idx].symbol, SYMBOL_TRADE_FREEZE_LEVEL);
    double stopsLevel = SymbolInfoInteger(g_positions[idx].symbol, SYMBOL_TRADE_STOPS_LEVEL);
    double minDistance = MathMax(freezeLevel, stopsLevel) * _Point;
    
    double priceDistance = MathAbs(currentPrice - targetSL);
    
    if(priceDistance < minDistance)
    {
        Print("WARNING: Cannot apply breakeven to #", ticket, 
              ". Market too close to target SL (distance: ", priceDistance/_Point, 
              " pts, min: ", minDistance/_Point, " pts). Abandoning.");
        g_positions[idx].breakevenApplied = true; // Don't retry
        return false;
    }
    
    // Attempt modification
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.symbol = g_positions[idx].symbol;
    request.sl = targetSL;
    request.tp = PositionGetDouble(POSITION_TP); // Keep existing TP
    
    if(!OrderSend(request, result))
    {
        int error = GetLastError();
        Print("Breakeven modify failed for #", ticket, " Error: ", error, 
              " Retcode: ", result.retcode);
        
        // Only abandon if market is too close
        if(error == ERR_TRADE_TOO_CLOSE_TO_MARKET || 
           result.retcode == TRADE_RETCODE_TOO_CLOSE)
        {
            g_positions[idx].breakevenApplied = true; // Don't retry
            return false;
        }
        
        // Other errors will retry on next tick
        return false;
    }
    
    // Success
    g_positions[idx].breakevenApplied = true;
    g_positions[idx].breakevenTime = TimeCurrent();
    
    Print("Breakeven applied to #", ticket, ": SL moved to ", targetSL, 
          " (entry: ", g_positions[idx].openPrice, ", adjustment: ", 
          MathAbs(targetSL - g_positions[idx].openPrice)/_Point, " pts)");
    
    return true;
}
```

### 4.3 Commission Detection

```mq5
//+------------------------------------------------------------------+
//| Initialize commission detection on startup                        |
//+------------------------------------------------------------------+
void InitializeCommissionDetection()
{
    g_detectedCommissionPerLot = 0;
    
    // Try SymbolInfo first
    g_detectedCommissionPerLot = DetectCommissionFromSymbolInfo();
    
    if(g_detectedCommissionPerLot <= 0)
    {
        // Try history analysis
        g_detectedCommissionPerLot = DetectCommissionFromHistory();
    }
    
    if(g_detectedCommissionPerLot <= 0)
    {
        // Fallback
        g_detectedCommissionPerLot = 4.00;
        Print("WARNING: Commission auto-detection failed. Using fallback $4.00/lot");
    }
    else
    {
        Print("Commission detected: $", DoubleToString(g_detectedCommissionPerLot, 2), "/lot round-trip");
    }
}

//+------------------------------------------------------------------+
//| Detect commission from symbol info                                |
//+------------------------------------------------------------------+
double DetectCommissionFromSymbolInfo()
{
    // SYMBOL_TRADE_COMMISSION returns per-side commission
    double commission = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_COMMISSION);
    
    if(commission > 0)
    {
        return commission * 2; // Round-trip
    }
    
    return 0;
}

//+------------------------------------------------------------------+
//| Detect commission from recent trade history                       |
//+------------------------------------------------------------------+
double DetectCommissionFromHistory()
{
    datetime from = TimeCurrent() - PeriodSeconds(PERIOD_D1) * 30; // Last 30 days
    HistorySelect(from, TimeCurrent());
    
    double totalCommission = 0;
    double totalLots = 0;
    int samples = 0;
    
    for(int i = HistoryDealsTotal() - 1; i >= 0 && samples < 10; i--)
    {
        ulong ticket = HistoryDealGetTicket(i);
        if(ticket == 0) continue;
        
        string symbol = HistoryDealGetString(ticket, DEAL_SYMBOL);
        if(symbol != _Symbol) continue;
        
        // Only count entry deals (DEAL_ENTRY_IN)
        ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY);
        if(entry != DEAL_ENTRY_IN) continue;
        
        double lots = HistoryDealGetDouble(ticket, DEAL_VOLUME);
        double commission = HistoryDealGetDouble(ticket, DEAL_COMMISSION);
        
        if(lots > 0 && commission != 0)
        {
            totalCommission += MathAbs(commission);
            totalLots += lots;
            samples++;
        }
    }
    
    if(totalLots >= 0.1) // Need at least 0.1 lots for meaningful sample
    {
        double perLot = totalCommission / totalLots;
        // Commission in history is per-side (entry), double for round-trip
        return perLot * 2;
    }
    
    return 0;
}

//+------------------------------------------------------------------+
//| Get spread at specific historical time (best estimate)            |
//+------------------------------------------------------------------+
double GetSpreadAtTime(datetime targetTime)
{
    // We can't get exact historical spread at position open time
    // Use current spread as approximation, or get from M1 data if available
    
    MqlRates rates[];
    if(CopyRates(_Symbol, PERIOD_M1, targetTime, 1, rates) == 1)
    {
        return (rates[0].high - rates[0].low) / _Point; // Approximation
    }
    
    // Fallback to current spread
    return (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
}
```

---

## 5. Dashboard Updates

**New Display Elements:**

| Element | Location | Content |
|---------|----------|---------|
| Session Column | After "Type" | ASIA / LONDON / NY |
| Breakeven Status | In Status column | BE-SET / BE-FAIL |
| Commission Display | Footer | "Comm: $X.XX/lot" |

**Color Coding:**
- Breakeven applied: Light green background on SL column
- Breakeven failed: Orange text on status

---

## 6. Migration Guide from v2.2.0

### 6.1 Code Changes

**Files to Modify:**
- `TimeCutoffManager.mq5` — Main file

**Additions:**
1. New enums and constants at top
2. New global variables
3. New functions (Session detection, Breakeven, Commission)
4. Modified `AddPosition()`, `CheckCutoffs()`
5. Dashboard updates in `UpdateDashboard()`

### 6.2 User Configuration

**New Setfile Parameters (TCM):**
```
InpUseSessionTiming=true
InpAutoDetectDST=true
InpAsiaPartialMins=2
InpAsiaFinalMins=5
InpAsiaPartialPct=50
InpAsiaUseBreakeven=true
InpLondonPartialMins=2
InpLondonFinalMins=5
InpLondonPartialPct=50
InpLondonUseBreakeven=true
InpNYPartialMins=2
InpNYFinalMins=5
InpNYPartialPct=50
InpNYUseBreakeven=true
```

**Backward Compatibility:**
- Set `InpUseSessionTiming=false` → TCM behaves exactly like v2.2.0
- Legacy `InpPartialCloseDuration`, `InpCloseDuration` still used in legacy mode

---

## 7. Testing Checklist

### 7.1 Session Detection
- [ ] Position opened at 04:00 server (winter) → Detected as ASIA
- [ ] Position opened at 10:00 server (winter) → Detected as LONDON
- [ ] Position opened at 19:00 server (winter) → Detected as NY
- [ ] DST transition: Position opened before/after DST handled correctly

### 7.2 Breakeven
- [ ] Breakeven SL calculated correctly (account for commission + spread)
- [ ] BUY position: SL moved to entry - adjustment
- [ ] SELL position: SL moved to entry + adjustment
- [ ] SL already tighter: Skip modify
- [ ] Market too close: Abandon, don't retry
- [ ] Other modify failures: Retry next tick (max 3)

### 7.3 Per-Session Timing
- [ ] Asia position uses Asia timing
- [ ] London position uses London timing
- [ ] NY position uses NY timing
- [ ] Legacy mode (`InpUseSessionTiming=false`) uses global inputs

### 7.4 Commission Detection
- [ ] Auto-detection from SymbolInfo works
- [ ] Fallback to history scan works
- [ ] Ultimate fallback to $4.00 works
- [ ] Display in dashboard correct

### 7.5 Integration
- [ ] Partial close + breakeven simultaneous
- [ ] No race conditions with GU EA
- [ ] Recovery CSV updated correctly after partial close
- [ ] Dashboard displays session correctly

---

## 8. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Session misclassification (DST bug) | `InpAutoDetectDST` can be disabled; manual offset input added as escape hatch |
| Breakeven modify fails repeatedly | Max 3 retries; doesn't block partial close |
| Commission detection wrong | Manual override input: `InpManualCommissionPerLot` (0 = auto-detect) |
| Backward compatibility break | `InpUseSessionTiming` opt-in; default false for v2.2 behavior |

---

## 9. Open Questions (Pre-Implementation)

1. **Escape hatch for commission:** Should I add `InpManualCommissionPerLot` input (0 = auto, >0 = override)?
2. **DST manual override:** Should I add `InpManualGMTOffset` for emergency use?
3. **Breakeven logging:** Log every breakeven attempt to CSV for audit trail?

**Answer these before I proceed to implementation.**

---

## 10. Header for Implementation File

```mq5
//+------------------------------------------------------------------+
//|                                       TimeCutoffManager.mq5       |
//|                        Time-Based Position Cutoff Manager         |
//|                        VERSION 2.3.0 - WORK IN PROGRESS           |
//|                        DO NOT DEPLOY - TESTING PHASE              |
//|                                                                   |
//|  FEATURES v2.3.0:                                                 |
//|  - Automatic session detection (GMT-based, DST-aware)             |
//|  - Per-session timing profiles (Asia/London/NY independent)       |
//|  - True breakeven protection (commission + spread accounted)      |
//|  - Commission auto-detection with fallback                        |
//|                                                                   |
//|  FIXES v2.2:                                                      |
//|  - (See previous changelog)                                       |
//+------------------------------------------------------------------+
#property copyright "GU Trading"
#property link      ""
#property version   "2.30"
#property strict
```

---

**RFC Status:** Awaiting final approval on Open Questions #9 before implementation begins.

*Prepared by: Viktor Kozlov (MQ5 Systems Architect)*  
*Date: 2026-03-20*
