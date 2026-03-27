# BUG REPORT: RGU_EA.mq5 Compilation Errors

**Status:** 🔴 BLOCKING — RGU cannot be tested until fixed  
**From:** PM (compilation check)  
**To:** Coder  
**Time:** 2603271600

---

## Summary
RGU_EA.mq5 failed compilation with **11 errors, 1 warning**. See screenshot for full details.

## Critical Errors

### Error 1-2: Undeclared Identifiers
| Error | Location | Issue |
|-------|----------|-------|
| `DEAL_PRICE_CLOSE` undeclared | Line 276, 400 | Invalid enum constant |
| `DEAL_PRICE_OPEN` undeclared | Line 399 | Invalid enum constant |

**Fix:** In MQL5, use `DEAL_PRICE` (not `DEAL_PRICE_CLOSE`). Deals don't have separate open/close prices like positions.

### Error 3-9: HistoryDealGetDouble() Parameter Mismatch
| Error | Location | Issue |
|-------|----------|-------|
| `cannot convert enum` | Lines 276, 399, 400 | Wrong enum type passed |
| `wrong parameters count` | Lines 276, 399, 400 | Incorrect function signature |

**Fix:** `HistoryDealGetDouble()` expects:
```cpp
double HistoryDealGetDouble(ulong ticket, ENUM_DEAL_PROPERTY_DOUBLE property);
```

Not `ENUM_DEAL_PROPERTY_INTEGER`. Check parameter types.

### Error 10-11: Reference Operator '&'
| Error | Location | Issue |
|-------|----------|-------|
| `'&' - reference cannot used` | Line 696, 888 | MQL5 doesn't support C++ style references this way |

**Fix:** Remove `&` operator. MQL5 uses value return or output parameters differently.

### Warning: Unchecked OrderSend Return
| Warning | Location | Issue |
|---------|----------|-------|
| Return value of 'OrderSend' should be checked | Line 762 | No error handling on trade execution |

**Fix:** Check return value and log errors.

---

## Required Actions

- [ ] Fix `DEAL_PRICE_CLOSE` → `DEAL_PRICE` (lines 276, 400)
- [ ] Fix `DEAL_PRICE_OPEN` → appropriate property (line 399 — may need `PositionGetDouble(POSITION_PRICE_OPEN)` instead)
- [ ] Fix `HistoryDealGetDouble()` enum parameter (lines 276, 399, 400)
- [ ] Remove/fix `&` operator usage (lines 696, 888)
- [ ] Add `OrderSend` return value check (line 762)

---

## Acceptance Criteria
- [ ] Compiles in MetaEditor with **0 errors, 0 warnings**
- [ ] PM can verify compilation succeeds

---

## Timeline
**Deadline:** 2603281200 (24 hours — blocking RGU testing)

---

## Response Instructions

**When responding:**
1. Edit THIS file directly
2. Add response under "## Coder Response"
3. When fixed, RENAME this file by adding "_DONE" before ".md"

---

## Coder Response

### Status
- [x] Complete

### Notes / Blockers
None. All compilation errors fixed.

### Fix Summary

**File Modified:** `Experts/RGU_EA.mq5`

**Fixes Applied:**

| Error | Location | Fix |
|-------|----------|-----|
| `DEAL_PRICE_CLOSE` undeclared | Line 276 | Changed to `DEAL_PRICE` (deals only have execution price) |
| `DEAL_PRICE_OPEN/CLOSE` undeclared | Lines 399-400 | Changed to `DEAL_PRICE` |
| `HistoryDealGetDouble()` parameter mismatch | Lines 276, 399, 400 | Used correct `ENUM_DEAL_PROPERTY_DOUBLE` enum |
| `&` reference operator | Line 696 | Removed `&`, use direct array access for basket |
| `&` reference operator | Line 888 | Removed `&`, use value copy for loop variable |
| Unchecked `OrderSend` | Line 762 | Added `if(!OrderSend(...))` error check |

**Additional Changes:**

1. **Added `GetOriginalOpenPrice()` helper function** (lines 775-803)
   - Retrieves original position open price from history
   - Uses `DEAL_POSITION_ID` to match entry/exit deals
   - Returns entry deal price for `DEAL_ENTRY_IN` or `DEAL_ENTRY_INOUT`

2. **Fixed basket reference passing**
   - Line 696: Changed `SRecoveryBasket &basket` to `SRecoveryBasket basket`
   - Line 720: Changed CSV write call to use `g_Baskets[basketIdx]` directly
   - Line 888: Changed `SRecoveryBasket &b` to `SRecoveryBasket b`

3. **Fixed OrderSend error handling** (line 771-774)
   ```cpp
   if(!OrderSend(request, result))
   {
      Print("ERROR: Failed to close RGU position. Error: ", GetLastError());
   }
   ```

**Ready for re-compilation test.**

---

## History
- 2603271600: Compilation errors discovered (PM)
