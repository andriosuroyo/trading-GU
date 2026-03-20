# TCM v2.1 Test Validation Checklist

## Quick Reference Card

Use this checklist during testing to ensure all functionality is validated.

---

## Pre-Flight Checks (Before Each Test Session)

- [ ] MetaEditor: Zero compiler warnings
- [ ] Inputs verified: Magic numbers, duration, spread filter
- [ ] Demo account balance > $500
- [ ] Chart timeframe appropriate (M1 for fast testing)
- [ ] Terminal ping to broker < 100ms
- [ ] "Allow Algo Trading" enabled
- [ ] Experts tab visible (Ctrl+T)

---

## Core Functionality Tests

### Test 1: Basic Cutoff (30-Second Duration)
**Setup:** Duration=30s, Warning=5s, Magic=999

| Time | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| T+0 | Attach TCM | "TCM v2.1 INITIALIZED" in log | ☐ |
| T+5 | Open test position | Position appears in dashboard | ☐ |
| T+5 | Check dashboard | Countdown shows ~25s remaining | ☐ |
| T+25 | Warning trigger | Row turns yellow, log warning | ☐ |
| T+30 | Cutoff reached | Position closes, log confirmation | ☐ |
| T+31 | Verify | Dashboard shows "No monitored positions" | ☐ |

**Log Validation:**
```
✓ "Added position #XXXXX ... Cutoff: HH:MM:SS"
✓ "WARNING: Position #XXXXX closing in 5 seconds"
✓ "Attempting close for position #XXXXX (attempt 1/3)"
✓ "Close request accepted ... Awaiting confirmation..."
✓ "Position #XXXXX confirmed closed. P&L: $XX.XX"
```

---

### Test 2: Retry Logic Validation
**Setup:** Duration=30s, Max Retries=3, Retry Delay=250ms

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 1 | Block close (change magic after open) | Close fails | ☐ |
| 2 | Check retry | Log shows "Will retry in X seconds" | ☐ |
| 3 | Restore magic | Close succeeds on retry | ☐ |

**Log Validation:**
```
✓ "Close request failed for position #XXXXX Error: X Retcode: Y"
✓ "Will retry in 1 seconds (backoff)"
✓ "Retrying close for position #XXXX (attempt 2/3)"
```

---

### Test 3: Spread Filter
**Setup:** Max Spread=100 points

| Condition | Expected Behavior | Pass |
|-----------|-------------------|------|
| Spread < 100 | Close executes normally | ☐ |
| Spread > 100 | "Delaying close ... spread too high" | ☐ |
| Spread returns < 100 | Close executes | ☐ |

---

### Test 4: Multi-Position Tracking
**Setup:** Open 5 positions simultaneously

| Metric | Expected | Actual | Pass |
|--------|----------|--------|------|
| All detected | 5 positions in dashboard | ___ | ☐ |
| Independent countdowns | Each has own timer | ___ | ☐ |
| Close timing | All within 2s of target | ___ | ☐ |
| No ticket errors | Zero "ticket mismatch" logs | ___ | ☐ |

---

## Race Condition Tests

### Test 5: TP/SL vs TCM Race
**Setup:** GU EA with tight SL (5 pips), TCM duration=2min

| Scenario | Expected Result | Pass |
|----------|-----------------|------|
| SL hits first | TCM logs "already closed", no error | ☐ |
| TCM close first | GU EA handles gracefully | ☐ |
| Simultaneous | One succeeds, one "already closed" | ☐ |

**Critical:** No `ERR_INVALID_STOPS` or `ERR_TRADE_NOT_ALLOWED`

---

### Test 6: Connection Loss
**Setup:** Active position tracked, disconnect network

| Phase | Expected | Pass |
|-------|----------|------|
| Disconnect | "Terminal connection LOST" | ☐ |
| Disconnected | No close attempts, red indicator | ☐ |
| Reconnect | "Terminal connection RESTORED" | ☐ |
| Post-reconnect | Normal operation resumes | ☐ |

---

## Edge Case Tests

### Test 7: Terminal Restart
**Setup:** 3 positions open, close MT5, reopen

| Check | Expected | Pass |
|-------|----------|------|
| TCM restarts | INIT_SUCCEEDED | ☐ |
| Existing positions | Detected and tracked | ☐ |
| Cutoff times | Correct (from open time) | ☐ |
| Recovery data | Loaded correctly | ☐ |

---

### Test 8: Array Cleanup
**Setup:** Run for extended period (100+ positions)

| Check | Expected | Pass |
|-------|----------|------|
| Memory stable | No growth in Task Manager | ☐ |
| Log message | "Cleaned up position array" every 5 min | ☐ |
| Dashboard responsive | No lag when updating | ☐ |

---

### Test 9: File Mutex (Multi-Instance)
**Setup:** 3 TCM instances, same recovery file

| Check | Expected | Pass |
|-------|----------|------|
| No corruption | CSV readable, no garbage | ☐ |
| No "file in use" | Zero file access errors | ☐ |
| All data saved | Each instance's data present | ☐ |

---

## Dashboard Tests

### Test 10: Visual Elements

| Element | Expected | Pass |
|---------|----------|------|
| Title | "TIME CUTOFF MANAGER v2.1" | ☐ |
| Connection dot | Green when OK, Red when down | ☐ |
| Position rows | Update every second | ☐ |
| Countdown | Accurate to ±1 second | ☐ |
| Colors | White/Normal, Yellow/Warning, Red/Critical, Aqua/Trailing | ☐ |
| Recovery value | Matches calculated total | ☐ |

---

### Test 11: Status Indicators

| Status | Color | Condition | Pass |
|--------|-------|-----------|------|
| ACTIVE | White | Normal operation | ☐ |
| DUE | White | Cutoff reached, pending spread | ☐ |
| CLOSING | Orange | Close request sent | ☐ |
| RETRY | DarkOrange | Retry scheduled | ☐ |
| TRAILING | Aqua | Trailing mode active | ☐ |

---

## Input Validation Tests

### Test 12: Filter Methods

| Method | Input | Expected Result | Pass |
|--------|-------|-----------------|------|
| Magic | "11,12,13" | Tracks only these magics | ☐ |
| Magic | "0" | Tracks all positions | ☐ |
| Comment | "GU_ASIA" | Tracks comments containing text | ☐ |
| Symbol | "XAUUSDp" | Tracks only this symbol | ☐ |
| Symbol | "" (empty) | Tracks current chart symbol | ☐ |

---

### Test 13: Duration Types

| Type | Value | Expected Cutoff | Pass |
|------|-------|-----------------|------|
| Seconds | 30 | 30 seconds from open | ☐ |
| Minutes | 2 | 2 minutes from open | ☐ |
| Hours | 1 | 1 hour from open | ☐ |

---

## Error Handling Tests

### Test 14: Invalid States

| Invalid State | Expected Behavior | Pass |
|---------------|-------------------|------|
| Trading disabled | "CRITICAL: Trading not allowed", INIT_FAILED | ☐ |
| Not connected | "CRITICAL: Terminal not connected", INIT_FAILED | ☐ |
| Position not found | Mark closed, continue operation | ☐ |
| File mutex timeout | "ERROR: Cannot acquire file mutex", INIT_FAILED | ☐ |

---

## Performance Tests

### Test 15: Resource Usage

| Metric | Acceptable | Test Result | Pass |
|--------|------------|-------------|------|
| CPU | <1% when idle | ___% | ☐ |
| Memory | Stable (no growth) | ___MB | ☐ |
| GDI Objects | Stable | ___ handles | ☐ |
| Update frequency | Every 1 second | ___s | ☐ |

---

## Sign-Off

**Tester Name:** ___________________

**Date:** ___________________

**TCM Version:** 2.1

**Test Environment:** ☐ Demo  ☐ Live (not recommended for initial testing)

**Overall Result:** ☐ PASS  ☐ FAIL

**Critical Issues Found:** ___________________

**Approved for Live Deployment:** ☐ YES  ☐ NO

**Notes:**

_____________________________________

_____________________________________

---

## Quick Failure Reference

| Error Message | Meaning | Action |
|---------------|---------|--------|
| "Ticket mismatch" | Race condition detected | Review close timing, increase delays |
| "Max retries exceeded" | Broker rejecting closes | Check trading permissions, spread |
| "Cannot acquire file mutex" | Multiple TCM instances conflicting | Ensure only one instance per file |
| "Terminal connection LOST" | Network issue | Check VPS/internet connection |
| "Spread too high" | Filter working as intended | Normal during news, verify settings |

---

*Use this checklist for every TCM deployment. Keep completed checklists for audit trail.*
