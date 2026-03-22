# Implementation Brief: MQ5/MQL5 Specialist

> **Role:** MQ5/MQL5 Specialist  
> **Reports To:** Viktor Kozlov (Systems Architect)  
> **Start Date:** [TO BE FILLED]  
> **Priority:** IMMEDIATE - BLOCKS ALL OTHER WORK

---

## 1. Your Mission

Implement production-grade MQL5 code based on my architectural specifications. I design the systems; you make them compile, run, and survive in live trading. This is not "indicator development." This is real-time risk management systems where a bug doesn't just crash—it liquidates accounts.

**Current Status:**
- ✅ TCM v2.3.0 — Coded, needs testing/bug fixes
- 🔄 GUS v1.0.0 — RFC approved, ready for implementation
- 📋 RecoveryManager v1.0.0 — Spec pending, your input welcomed

---

## 2. Non-Negotiable Standards

### 2.1 Error Handling Mandate

**EVERY** external function call gets error checking. No exceptions. Not one.

```mq5
// WRONG - I will reject this in code review
CTrade trade;
trade.PositionClose(ticket);

// CORRECT - This passes review
CTrade trade;
if(!trade.PositionClose(ticket))
{
    int error = GetLastError();
    uint retcode = trade.ResultRetcode();
    Print("PositionClose failed. Ticket: ", ticket, 
          " Error: ", error, " Retcode: ", retcode);
    
    // Handle specific errors
    if(retcode == TRADE_RETCODE_REJECT)
        ScheduleRetry();
    else if(retcode == TRADE_RETCODE_POSITION_CLOSED)
        MarkAsClosed();
    // ... etc
}
```

### 2.2 Atomic Position Validation

Position pool enumeration is non-deterministic. Race conditions are real.

```mq5
// WRONG
for(int i = PositionsTotal() - 1; i >= 0; i--)
{
    ulong ticket = PositionGetTicket(i);
    long magic = PositionGetInteger(POSITION_MAGIC); // DANGER: Pool shifted
}

// CORRECT
for(int i = PositionsTotal() - 1; i >= 0; i--)
{
    ulong ticket = PositionGetTicket(i);
    if(ticket == 0) continue;
    
    if(!PositionSelectByTicket(ticket)) continue; // Re-select by ticket
    
    long magic = PositionGetInteger(POSITION_MAGIC); // SAFE
    ulong verify = PositionGetInteger(POSITION_TICKET);
    if(verify != ticket) continue; // Paranoid verification
}
```

### 2.3 State Machine Pattern

NO `Sleep()` in `OnTick()`. Ever. Use state machines.

```mq5
enum ENUM_OPERATION_STATE
{
   STATE_IDLE,
   STATE_PENDING,
   STATE_RETRY
};

struct OperationData {
   ENUM_OPERATION_STATE state;
   datetime lastAttempt;
   int retryCount;
};

void OnTick()
{
   ProcessPendingOperations(); // Check timeouts, schedule retries
   ExecuteNewOperations();     // Start new work
}
```

### 2.4 Memory Management

```mq5
// WRONG
void SomeFunction()
{
    double data[];
    ArrayResize(data, 100000); // Never freed
}

// CORRECT
void SomeFunction()
{
    double data[];
    ArrayResize(data, 100000);
    // ... use data ...
    ArrayFree(data); // Explicit cleanup
}

// OR use dynamic objects with destructors
class CDataBuffer
{
    double m_data[];
public:
    ~CDataBuffer() { ArrayFree(m_data); }
};
```

### 2.5 Git Discipline

```bash
# Branch naming
feature/TICKET-description  # e.g., feature/GUS-001-indicator-handles
bugfix/TICKET-description   # e.g., bugfix/TCM-003-retry-logic

# Commit messages
"TCM: Fix race condition in position enumeration"
"GUS: Implement RSI scoring function with error handling"
"Recovery: Add CSV parsing for manual zone input"

# NEVER
"fix bug"
"update"
"WIP"
```

---

## 3. Immediate Deliverables (Week 1-2)

### Task 1: TCM v2.3.0 Testing & Bug Fixes

**Reference:** `RFC_001_TCM_v2.3.0_SessionBreakeven.md`, `Experts/TimeCutoffManager.mq5`

**Your Actions:**
1. Pull repo, compile TCM v2.3.0 on Windows MetaEditor
2. Fix any compilation errors (report to me if architectural changes needed)
3. Test on Vantage Demo per TODO.md checklist
4. Document bugs in GitHub Issues with:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Log excerpts

**Success Criteria:**
- [ ] Compiles without warnings on strict mode
- [ ] Session detection works for Asia/London/NY
- [ ] Breakeven applies correctly (SL moved to entry + adjustment)
- [ ] Breakeven CSV log created and populated
- [ ] Partial close still works as in v2.2.0

### Task 2: Code Review Fixes

I will review your bug fixes. Expect:
- Line-by-line comments
- Rejection if error handling is missing
- Rejection if magic numbers are used
- Rejection if comments don't explain "why"

**Response Time:** You fix and push within 24 hours of my review.

---

## 4. Primary Deliverable (Week 3-6)

### Task 3: GUS v1.0.0 Implementation

**Reference:** `RFC_002_GUS_Scoring_Engine.md`

**Architecture:**
```
Experts/
└── GUS/
    ├── GUSScoringEngine.mq5      (Main EA - you write this)
    ├── GUS_Indicators.mqh        (6 factor calculations)
    ├── GUS_Database.mqh          (CSV I/O operations)
    ├── GUS_Discord.mqh           (Webhook functions)
    └── GUS_Dashboard.mqh         (Chart UI)
```

**Module Specifications:**

#### GUS_Indicators.mqh

```mq5
// Each function returns 0-100 score
int CalculateRSIScore(string symbol, ENUM_TIMEFRAMES tf=PERIOD_M1);
int CalculateMADistanceScore(string symbol, ENUM_TIMEFRAMES tf=PERIOD_M1);
int CalculateMACDScore(string symbol, ENUM_TIMEFRAMES tf=PERIOD_M1);
int CalculateATRScore(string symbol, ENUM_TIMEFRAMES tf=PERIOD_M1);
int CalculateSpreadScore(string symbol);
int CalculateRangeScore(string symbol);

// Main scoring function
int CalculateGUScore(ulong ticket, string symbol, int positionType, 
                     double &factorScores[6], string &factorNames[6]);
```

**Requirements:**
- Handle missing indicator data gracefully (return 50 neutral, log warning)
- Cache indicator handles (don't create/destroy in `OnTick()`)
- Normalize all outputs to 0-100 range
- Document the scoring logic in comments

#### GUS_Database.mqh

```mq5
class CGUS_Database
{
public:
    bool Initialize();
    bool AddPosition(ulong ticket, datetime entryTime, double entryPrice,
                     int positionType, int finalScore, double &factorScores[6]);
    bool UpdatePositionOutcome(ulong ticket, double pnl, double mae, 
                               double mfe, int durationSeconds);
    bool LoadWeights(double &weights[6]);
    bool SaveWeights(double &weights[6]);
    bool LogWeightAdjustment(ulong ticket, bool isWin, double &oldWeights[6], 
                             double &newWeights[6]);
};
```

**Requirements:**
- Use FILE_COMMON for all CSV files (shared across terminals)
- Implement file mutex (copy pattern from TCM)
- Handle concurrent access (GUS + manual Excel editing)
- Atomic writes (write to temp file, then move)

#### GUS_Discord.mqh

```mq5
class CGUS_Discord
{
    string m_webhookUrl;
public:
    bool Initialize(string webhookUrl);
    bool SendHighScoreAlert(ulong ticket, int score, double &factorScores[6], 
                            string symbol, double entryPrice, int positionType);
    bool SendDailySummary(int totalTrades, int wins, int losses, 
                          double avgScore, double winRate);
};
```

**Requirements:**
- Use WinHTTP (MQL5 native) or URLDownloadToFile
- Handle network failures (queue and retry, don't block)
- JSON formatting per RFC 002 spec
- Rate limiting (Discord allows 5 requests/2 seconds)

#### GUS_Dashboard.mqh

Follow TCM dashboard pattern:
- Rectangle backgrounds for panels
- Labels for text (don't use OBJ_TEXT)
- Color coding: <60 red, 60-79 yellow, 80+ green
- Update only changed elements (don't delete/recreate every tick)

### Task 4: Integration Testing

**Test Matrix:**
| Scenario | Expected Result |
|----------|----------------|
| GU opens SELL @ 1950 | GUS detects within 1 second, calculates score |
| Score = 82 | Discord alert fires within 5 seconds |
| Position closes +$15 | Recorded as WIN, weights adjusted |
| Position closes -$10 | Recorded as LOSS, weights adjusted |
| CSV opened in Excel | GUS continues writing without corruption |
| 10 positions in 60 seconds | All tracked, no missed detections |

---

## 5. Code Review Checklist

Before submitting any code for review, verify:

```markdown
- [ ] Every OrderSend/PositionClose/PositionModify has error handling
- [ ] No Sleep() calls in OnTick()
- [ ] All arrays properly freed or use RAII
- [ ] No magic numbers (use #define or enums)
- [ ] Comments explain WHY, not WHAT
- [ ] Function names are verbs (Calculate, Process, Validate)
- [ ] Variable names are descriptive (no `i`, `j`, `tmp`)
- [ ] Git commit messages follow convention
- [ ] Compiled with #property strict, zero warnings
- [ ] Tested on demo account, logs attached to PR
```

---

## 6. Communication Protocol

### Daily Standup (Async)

Post in [TO BE DETERMINED - Slack/Discord/Telegram]:
```
Yesterday: Fixed TCM session detection bug, tested Asia timing
Today: Implementing GUS RSI score calculation
Blockers: None
```

### Questions for Me

**Urgent (blocks your work):** DM me, expect response within 4 hours during business hours (UTC+8)
**Non-urgent:** Comment in GitHub issue, I'll respond within 24 hours
**Architecture questions:** Schedule 30-min call, I prefer voice for complex discussions

### Bug Reports

Use GitHub Issues template:
```markdown
**Component:** TCM v2.3.0 / GUS / Other
**Severity:** Critical (crashes/stops trading) / High (wrong behavior) / Medium (cosmetic)
**Steps to Reproduce:**
1. Attach EA to XAUUSD chart
2. Set inputs: X=Y
3. Wait for condition Z

**Expected:** Description
**Actual:** Description + screenshot/log
**Log Excerpt:**
```
2026.03.20 10:00:05.123 TCM: Breakeven failed for #123456
2026.03.20 10:00:05.124 TCM: Error: 146 (TRADE_MODIFY_DENIED)
```
```

---

## 7. Success Metrics (90-Day Review)

Your performance is measured by:

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Quality** | Zero critical bugs in production | Bugs found in first 30 days of live use |
| **Delivery Speed** | GUS v1.0.0 live within 6 weeks | Date of first live trade scored |
| **Review Rounds** | <2 major revision cycles per feature | Number of "Request Changes" on PRs |
| **Documentation** | Every function has docstring | Random audit of 20 functions |
| **Uptime** | GUS runs 24/5 without manual restart | Log analysis for crashes/restarts |

---

## 8. Questions for You

Before you start, I need answers:

1. **Development Environment:** Windows 10/11? MetaEditor version?
2. **Testing Access:** Do you have a Vantage Demo account, or do I need to arrange?
3. **Git Experience:** Comfortable with branching, rebasing, resolving conflicts?
4. **Trading Knowledge:** Have you traded live, or only backtests? Do you understand XAUUSD pip values?
5. **Availability:** Time zone? Hours available per week? London/NY overlap availability for critical bugs?

---

## 9. Access & Resources

**GitHub Repository:** https://github.com/andriosuroyo/trading-GU
**Documentation:** All RFCs in repo root
**Reference Code:** `Experts/TimeCutoffManager.mq5` (study this for my coding style)
**Communication:** [TO BE FILLED - Slack/Discord channel]

---

**Brief Version:** 1.0  
**Last Updated:** 2026-03-20  
**Author:** Viktor Kozlov (Systems Architect)

*Read this entire document. Confirm understanding before writing a single line of code.*
