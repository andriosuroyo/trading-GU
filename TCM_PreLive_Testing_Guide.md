# TimeCutoffManager Pre-Live Testing Guide

## Overview

This guide provides a structured approach to testing TimeCutoffManager v2.1 in pre-live conditions. The goal is to validate that position cutoff functionality works correctly **before** deploying to a live account.

---

## Testing Philosophy

**Never test on live accounts.** TCM interacts with open positions and will close them. Always test on demo accounts with the same broker/infrastructure you plan to use live.

**Test in phases:**
1. **Static Testing** - Compile-time validation
2. **Unit Testing** - Individual function validation
3. **Integration Testing** - Multi-EA interaction simulation
4. **Stress Testing** - High-frequency, edge case validation
5. **Dry-Run Testing** - Monitor without closing (validation mode)

---

## Phase 1: Static Testing

### 1.1 Compilation Validation

```bash
# In MetaEditor, compile with maximum warnings
# Settings → Compiler → Warning Level: Maximum
```

**Checklist:**
- [ ] No compiler warnings (warnings = future bugs)
- [ ] No implicit type conversions
- [ ] All enum values handled in switch statements
- [ ] String buffer sizes adequate

### 1.2 Code Review Checklist

Review the code for these specific patterns:

```cpp
// VERIFY: No Sleep() calls in trade path
// VERIFY: All PositionSelectByTicket() calls verify ticket matches
// VERIFY: All OrderSend/PositionClose paths have error handling
// VERIFY: File operations use mutex (FILE_COMMON race condition)
// VERIFY: SymbolSelect() called for multi-symbol monitoring
```

---

## Phase 2: Unit Testing (Demo Account)

### 2.1 Basic Functionality Test

**Setup:**
- Demo account with $10,000 balance
- XAUUSD chart, M1 timeframe
- TCM attached with these settings:
  - Filter: Magic Number = 999 (test EA magic)
  - Duration: 30 seconds (short for testing)
  - Warning: 5 seconds

**Test Script:**
```mq5
// TestPositionOpener.mq5 - Companion test EA
input int InpTestMagic = 999;
input int InpOpenDelaySeconds = 5;

int OnInit() {
    EventSetTimer(1);
    return INIT_SUCCEEDED;
}

void OnTimer() {
    static datetime startTime = TimeCurrent();
    if(TimeCurrent() - startTime == InpOpenDelaySeconds) {
        // Open test position
        MqlTradeRequest req = {};
        MqlTradeResult res = {};
        req.action = TRADE_ACTION_DEAL;
        req.symbol = Symbol();
        req.volume = 0.01;
        req.type = ORDER_TYPE_BUY;
        req.price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
        req.deviation = 10;
        req.magic = InpTestMagic;
        req.comment = "TCM_TEST";
        
        if(!OrderSend(req, res)) {
            Print("Failed to open test position: ", GetLastError());
        } else {
            Print("Test position opened: ", res.order);
        }
    }
}
```

**Expected Results:**
1. Position opens at T+5 seconds
2. TCM detects position within 1 second
3. Dashboard shows countdown starting at 30 seconds
4. At T+25 seconds, warning appears (yellow)
5. At T+30 seconds, position closes
6. Log shows: "Position #XXXXX confirmed closed"

**Validation Points:**
- [ ] Position closed exactly at 30 seconds (±1 second tolerance)
- [ ] No errors in Experts tab
- [ ] Recovery file updated (if enabled)
- [ ] Dashboard reflects closed status

### 2.2 Multi-Position Test

**Setup:**
- Open 5 positions simultaneously using the test EA
- Set TCM duration: 60 seconds

**Expected Results:**
- [ ] All 5 positions tracked independently
- [ ] Countdowns accurate for each
- [ ] All close within 2 seconds of each other
- [ ] No "ticket mismatch" errors in log

### 2.3 Spread Filter Test

**Setup:**
- TCM: Max Spread = 50 points
- Test during high spread period (8:30 AM EST NFP news)

**Expected Results:**
- [ ] When spread > 50 points, close is delayed
- [ ] Log shows: "Delaying close for #XXXX - spread too high"
- [ ] When spread normalizes, position closes

---

## Phase 3: Integration Testing

### 3.1 GU EA Coexistence Test

**Setup:**
- Attach TCM to chart
- Attach GU EA with:
  - Magic Number = 11
  - Short TP/SL (to test race conditions)
- TCM settings:
  - Filter: Magic Numbers = 11
  - Duration: 2 minutes

**Test Scenarios:**

#### Scenario A: TCM Closes Before TP/SL
1. GU EA opens position
2. Wait 2 minutes
3. TCM attempts close

**Expected:**
- [ ] Position closes via TCM
- [ ] No duplicate close errors
- [ ] GU EA handles the closure gracefully

#### Scenario B: TP/SL Hits Before TCM Cutoff
1. GU EA opens position
2. Price moves to hit TP within 1 minute
3. TCM should detect position is gone

**Expected:**
- [ ] TCM logs: "Position #XXXX already closed (not found)"
- [ ] No errors
- [ ] Position removed from dashboard

#### Scenario C: Simultaneous Close Attempt (Race Condition)
1. TCM cutoff time approaches
2. GU EA SL triggers at same time
3. Both attempt close within milliseconds

**Expected:**
- [ ] One succeeds, one logs "already closed"
- [ ] No ERR_INVALID_STOPS or ERR_TRADE_NOT_ALLOWED
- [ ] Final P&L recorded correctly

### 3.2 Multi-Instance TCM Test

**Setup:**
- Instance 1: Chart 1, Filter Magic = 11,12, Duration = 2 min
- Instance 2: Chart 2, Filter Magic = 21,22, Duration = 5 min
- Instance 3: Chart 3, Filter Magic = 31,32, Duration = 10 min

**Expected:**
- [ ] Each instance tracks only its assigned magic numbers
- [ ] Recovery file uses mutex (no corruption)
- [ ] No "file in use" errors

**Validation:**
Check `loss_recovery.csv` after test:
```csv
Date,Symbol,Loss,Lots,Ticket,Recovered
2024.01.15 14:30:45,XAUUSD,45.50,0.10,12345678,0
```

---

## Phase 4: Stress Testing

### 4.1 High-Frequency Position Test

**Setup:**
- Test EA opens position every 10 seconds
- TCM duration: 30 seconds
- Run for 10 minutes = 60 positions

**Expected:**
- [ ] Memory usage stable (no leaks)
- [ ] Dashboard responsive
- [ ] All positions closed within tolerance
- [ ] Array cleanup occurs (check logs for "Cleaned up position array")

### 4.2 Connection Loss Simulation

**Setup:**
- TCM running with active position
- Disconnect internet for 30 seconds
- Reconnect

**Expected:**
- [ ] Log: "WARNING: Terminal connection LOST"
- [ ] Dashboard shows red connection indicator
- [ ] No close attempts during disconnection
- [ ] Log: "INFO: Terminal connection RESTORED"
- [ ] Position tracking resumes
- [ ] Close occurs if cutoff passed during outage

**To Simulate:**
- Use Windows Firewall to block terminal.exe
- Or physically disconnect network cable

### 4.3 Terminal Restart Test

**Setup:**
- TCM tracking 3 positions
- Close MT5 terminal (simulating crash)
- Reopen MT5

**Expected:**
- [ ] TCM restarts successfully
- [ ] Detects existing positions (if still open)
- [ ] Recovery data loaded correctly
- [ ] Cutoff times recalculated from position open time

### 4.4 Spread Spike Test

**Setup:**
- TCM: Duration = 1 minute
- Open position
- Use news event or manually widen spread

**Validation:**
Use this debug output to verify spread detection:
```
Delaying close for #12345 - spread too high (850 > 500)
```

---

## Phase 5: Dry-Run Mode (Validation Without Risk)

### 5.1 Enable Dry-Run Mode

Modify TCM temporarily for testing:

```cpp
// Add to input parameters
input bool InpDryRunMode = true;  // Log only, don't actually close

// In ClosePosition():
if(InpDryRunMode) {
    Print("DRY RUN: Would close position #", ticket);
    g_positions[idx].closed = true; // Mark as "closed" for tracking
    return;
}
```

**Use this to:**
- Validate cutoff timing logic without risking real positions
- Test on live account (monitoring only)
- Verify filter logic matches intended positions

### 5.2 Dry-Run Validation Checklist

Run for 24 hours on demo with dry-run enabled:
- [ ] All intended positions detected
- [ ] Cutoff times calculated correctly
- [ ] No false positives (closing positions that shouldn't be closed)
- [ ] No false negatives (missing positions that should be closed)

---

## Phase 6: Pre-Production Checklist

Before attaching to live account:

### Account Validation
- [ ] Account is live (not demo)
- [ ] Account balance > $1000 (or your minimum)
- [ ] Trading permissions enabled (check Ctrl+T → Journal)
- [ ] No "read-only" login

### TCM Configuration Validation
- [ ] Filter Magic Numbers = correct GU instance numbers
- [ ] Duration = intended cutoff (2 minutes for your use case)
- [ ] Max Spread = appropriate for session (100-500 points for XAUUSD)
- [ ] Max Retries = 3 (default)
- [ ] Retry Delay = 250ms (default)

### Infrastructure Validation
- [ ] VPS ping to broker < 50ms
- [ ] Terminal allowed through firewall
- [ ] Auto-trading enabled in terminal
- [ ] "Allow Algo Trading" button pressed

### Logging Validation
Add this to your TCM to verify live environment:

```cpp
int OnInit() {
    // ... existing code ...
    
    // Log critical environment info
    Print("=== TCM LIVE ENVIRONMENT ===");
    Print("Account: ", AccountInfoString(ACCOUNT_NAME));
    Print("Server: ", AccountInfoString(ACCOUNT_SERVER));
    Print("Balance: $", DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
    Print("Leverage: 1:", IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)));
    Print("Trade Allowed: ", TerminalInfoInteger(TERMINAL_TRADE_ALLOWED));
    Print("Connected: ", TerminalInfoInteger(TERMINAL_CONNECTED));
    Print("Ping to server: ", IntegerToString(TerminalInfoInteger(TERMINAL_PING_LAST)), " ms");
    Print("============================");
    
    return INIT_SUCCEEDED;
}
```

---

## Testing Schedule Recommendation

| Phase | Duration | Environment | Pass Criteria |
|-------|----------|-------------|---------------|
| Static | 1 day | MetaEditor | Zero warnings |
| Unit | 3 days | Demo account | 100% pass rate |
| Integration | 3 days | Demo + GU EA | No race conditions |
| Stress | 2 days | Demo account | <1% error rate |
| Dry-Run | 7 days | Demo account | Zero errors |
| **LIVE** | **Ongoing** | **Live account** | **Monitor closely** |

---

## Emergency Rollback Procedure

If TCM misbehaves in live environment:

1. **Immediate:** Click "Remove Expert" from chart
2. **Verify:** Check Terminal → Experts tab for "TimeCutoffManager deinitialized"
3. **Validate:** Confirm no TCM labels remain on chart
4. **Manual Check:** Verify no positions are in unexpected states

To prevent accidental live deployment:
```cpp
// Add safety check in OnInit()
if(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_REAL && !InpConfirmedLive) {
    Alert("LIVE ACCOUNT DETECTED! Set InpConfirmedLive=true to proceed.");
    return INIT_FAILED;
}
```

---

## Log File Analysis

After testing, check these log patterns:

**Good Signs:**
```
Position #12345 confirmed closed. P&L: $12.50
Cleaned up position array: 3 active positions retained
Connection: OK | Trade: OK | Tracked: 3
```

**Warning Signs:**
```
WARNING: Terminal connection LOST
Retrying close for position #12345 (attempt 2/3)
Delaying close for #12345 - spread too high
```

**Critical Errors (stop and fix):**
```
ERROR: Ticket mismatch in ScanPositions!
ERROR: Max retries (3) exceeded for position #12345
ERROR: Cannot acquire file mutex
CRITICAL: Terminal not connected to broker
```

---

## Summary

**Minimum viable testing before live:**
1. Compile with zero warnings
2. Run unit test (30-second duration) × 10 iterations
3. Run integration test with GU EA (2-minute duration) × 5 iterations
4. Verify no "ticket mismatch" errors in 100+ position sample
5. Confirm recovery file write/read works across terminal restarts

**Never skip:** Multi-position stress test. Race conditions only appear under load.

**Red flags that prevent live deployment:**
- Any "ticket mismatch" errors
- Memory growth over time
- Unexplained position close delays > 5 seconds
- File corruption in recovery data

---

*Document Version: 1.0*
*Last Updated: 2026-03-19*
*TCM Version: 2.1*
