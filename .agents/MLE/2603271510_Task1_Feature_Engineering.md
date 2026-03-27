# Task Assignment: Phase 1 Feature Engineering

**Status:** 🟡 AWAITING DATA (Do not start until QA delivers)  
**From:** PM  
**To:** MLE  
**Time:** 2603271510

---

## ⏸️ TASK ON HOLD — Insufficient Data

QA has delivered `data/position_history_cleaned_260327.csv`, but **data is insufficient for ML training**.

**Status:** ⏸️ **ON HOLD** (do not start)
**Reason:** 
- Settings changed significantly since March 12
- Clean data only available from March 23 onwards
- Insufficient sample size for robust feature engineering

**Restart Trigger:** End of trading week (more data accumulated)

**ML Multi-Setting Approach — DECIDED:**
- ✅ **Option B: Unified model with setting as categorical feature**
- Strategy identifier (CommentTag, e.g., GU_m1052005) will be categorical features
- Rationale: More efficient, leverages patterns across settings
- **Implementation:** Include `Magic` as categorical in feature engineering

---

## Context
You have completed onboarding and are ready for your first task. QA is preparing cleaned position history with MAE/MFE calculations.

## Task: Exploratory Feature Engineering

### Objective
Identify 5-10 candidate features that predict whether a position will hit its TrailStart target.

### Prediction Target
**Primary:** Binary classification — `TrailStartHit` (Yes/No)

### Feature Categories to Explore

#### Category 1: Entry Context
- ATR(60) at entry time vs session average
- Spread at entry
- Time within session (minutes since session open)
- Recent volatility regime (ATR trending up/down)

#### Category 2: Market Structure
- Distance to nearest support/resistance
- Recent price velocity (points per minute, 5-min window)

#### Category 3: Session Characteristics
- Session identifier (derived from OpenTime: Asia 02-06, London 08-12, NY 17-21 UTC)
- Day of week
- Time of day (normalized)

#### Category 4: Historical Context
- Win rate of last N positions in same session
- Current daily P&L (from position history)
- Consecutive losses in session

### Constraints
- **NO look-ahead bias:** Features must use only data available at position open time
- **Time-series respect:** Use expanding window (not future data)
- **Actionable:** Features must be computable in real-time for live trading

## Inputs (When QA Delivers)
1. `data/position_history_cleaned_260327.csv` — Cleaned positions
2. `tick_data/mae_mfe_*.csv` — Pre-computed MAE/MFE files
3. `Setfiles/20260322/*.set` — Static strategy parameters

## Expected Output Document

Create a file: `.agents/MLE/2603XXXXXXXX_Feature_Engineering_Report.md`

Content structure:
```markdown
# Feature Engineering Report: TrailStart Prediction

## Feature Candidates (5-10 features)
### Feature 1: [Name]
- Description, Calculation, Data source, Rationale, Look-ahead safe?

## Exploratory Analysis
### Univariate Analysis
- Distribution of each feature
- Correlation with target

### Multivariate Analysis
- Feature correlation matrix

## Recommendations
### Top 3 Features for Model
1. [Feature] — [Reason]
2. [Feature] — [Reason]
3. [Feature] — [Reason]

## Next Steps
```

## Acceptance Criteria
- [ ] 5-10 feature candidates documented with calculations
- [ ] All features verified look-ahead safe
- [ ] Univariate analysis shows at least 3 features with |correlation| > 0.1 to target
- [ ] Feature correlation matrix provided
- [ ] Top 3 features recommended with rationale

## Timeline
**Original Start:** Upon QA data delivery  
**Status:** ON HOLD — awaiting sufficient data  
**Expected Restart:** End of current trading week (260331 or 260407)  
**Duration:** 3 days from restart  

**Prerequisites for restart:**
- [ ] Sufficient data accumulated (minimum 300+ positions recommended)
- [ ] Decision on multi-setting ML approach (User/PM)

---

## Response Instructions (For MLE)

**When responding:**
1. Edit THIS file directly — do not create a new file
2. Add your response below under "## MLE Response"
3. Include:
   - Status update (Waiting / In Progress / Complete / Blocked)
   - Any questions or clarifications needed
   - If complete: reference to your report file
   - If blocked: what you need from PM
4. When complete, RENAME this file by adding "_DONE" before ".md"
   Example: `2603271510_Task1_Feature_Engineering_DONE.md`

---

## MLE Response

*(MLE to acknowledge the hold status)*

### Status
- [x] On Hold — awaiting sufficient data and PM decision
- [ ] In Progress
- [ ] Complete
- [ ] Blocked

### Acknowledgment
- [ ] Understand task is on hold
- [ ] Will wait for PM restart signal
- [ ] Will review multi-setting ML approaches while waiting

### Notes / Blockers
*(If blocked, explain what you need)*

### Deliverable Reference
*(If complete, provide path to your report file)*

---

## History
- 2603271510: Task pre-assignment (PM)
- 2603271600: QA delivered data — task now active (PM)
- 2603271610: Task put ON HOLD — insufficient data, multi-setting approach undecided (PM)
