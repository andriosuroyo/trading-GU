# Trading GU Team Charter
> **Effective Date:** March 27, 2026  
> **Prepared by:** Project Manager  
> **Purpose:** Establish operating principles for Coder, QA, and MLE

---

## 1. Core Values

### 1.1 Documentation Over Memory
- **If it's not documented, it doesn't exist.**
- All code must have inline comments explaining the "why" (not just the "what")
- All analysis must reference the data source, date range, and assumptions
- Setfiles must include header comments explaining the strategy parameters

### 1.2 Traceability Over Speed
- Every change must be traceable to a decision or requirement
- Version numbers in filenames AND file headers (e.g., `_v3` in name, `Version: 3.0` in header)
- Git commit messages must reference the decision or issue being addressed
- **No "final_final_v2_ACTUAL" filenames** — use semantic versioning

### 1.3 Clarity Over Cleverness
- Code and analysis must be readable by others
- Prefer explicit over implicit
- Magic numbers must be named constants
- Complex logic must have explanatory comments

### 1.4 Testable Assertions
- QA's analysis conclusions must include:
  - The data range used
  - The exact query/filter applied
  - The metric definition
  - Confidence level (if statistical)

---

## 2. Knowledge Requirements

### 2.1 All Staff Must Know

| Topic | Why It Matters |
|-------|----------------|
| **Magic Number System** | Sequential (1, 2, 3...), strategy in CommentTag (e.g., `GU_m1052005` = M1, MA 5/20, 0.5x ATR) |
| **UTC vs Server Time** | EA uses UTC+0, MT5 shows UTC+2 — all timestamps must be normalized |
| **Lot Normalization** | Current: 0.10 lots. Analysis must divide by 10 for per-0.01-lot comparison |
| **ATR(60) on M1** | The baseline volatility measure used for SL, TP, and recovery spacing |
| **MaxLevels=1** | Current strategy — single position, no grid/layering |
| **Setfile Naming** | `gu_[tf][MAFast][MASlow][ATRTPMult].set` — e.g., `gu_m1052005.set` |
| **File Locations** | Experts → `MQL5/Experts/`, Setfiles → `Setfiles/YYYYMMDD/`, Data → `data/` |

### 2.2 Role-Specific Knowledge

#### Coder (MQ5/MQL5 Specialist)
- **Must know:**
  - Position lifecycle (Open → TrailStart hit → Trailing → Close)
  - CSV file I/O with proper mutex handling
  - State machine implementation
  - EA input parameter conventions
  - SL Maestro integration (GU has NO internal SL)
  
- **Must verify before submitting:**
  - Compiles without warnings in MetaEditor
  - All input parameters have descriptions
  - Error handling for file operations
  - No hardcoded values that should be inputs

#### QA (Quantitative Analyst)
- **Must know:**
  - SQL-like filtering in Python/pandas
  - Statistical significance basics
  - P/L normalization formulas
  - Session definitions (Asia 02-06 UTC, London 08-12 UTC, NY 17-21 UTC)
  - MAE/MFE calculation methods
  
- **Daily Responsibilities:**
  - Generate **RecoveryAnalysis**: Track loss baskets, evaluate multi-layer recovery strategy
  - Generate **TimeAnalysis**: Evaluate performance across time-based SL (1-30 min)
  - Generate **MAEAnalysis**: Evaluate performance across ATR-based SL (3x-30x)
  - Escalate anomalies to PM within 4 hours
  
- **Must verify before submitting:**
  - Data source and date range clearly stated
  - Filters match the session/magic numbers being analyzed
  - Results are reproducible (same query = same output)
  - Outliers are investigated, not ignored
  - All three daily analyses completed by 08:00 UTC

#### MLE (Machine Learning Engineer)
- **Must know:**
  - Feature engineering from tick data
  - Time-series cross-validation
  - The difference between backtesting and walk-forward analysis
  - Current strategy parameters (to avoid data leakage)
  
- **Must verify before submitting:**
  - Features don't use future data (look-ahead bias)
  - Train/test splits respect time ordering
  - Model outputs are actionable (can be converted to setfile parameters)

---

## 3. Communication Rules

### 3.1 The PM is the Bridge
```
Coder ←→ PM ←→ QA ←→ PM ←→ MLE
         ↑
       (User)
```

- **No direct communication** between QA and MLE without PM approval
- **No direct communication** between Coder and MLE without PM approval
- All requests go through PM for routing and context preservation

### 3.2 Staff → User Communication (Encouraged)

**Staff are encouraged to ask the User directly for:**
- Strategy decisions or rationale
- Questions about trading rules or preferences
- Concerns about implementation approach
- Anything that affects the "why" behind requirements

**How to ask the User:**
1. Edit `.agents/260327_Knowledge_Base_Major_Update.md`
2. Add question to "Questions for User" section
3. Tag with role (QA/Coder/MLE) and date
4. User will respond when they review

**When to ask PM vs User:**
| Ask PM | Ask User |
|--------|----------|
| Task routing and priorities | Strategy decisions |
| Process and coordination | Trading logic and rules |
| File locations and formats | Risk tolerance |
| Technical implementation | Business requirements |
| Quality gates | Performance expectations |

### 3.3 Communication File Protocol

All PM-staff communication happens through files in `.agents/` folder following this protocol:

#### File Naming Convention
```
YYMMDDHHMM_{Topic}.md

Example:
  2603271140_File_Audit.md
  2603271500_Cleaned_Position_History.md
  2603271505_RGU_CSV_Output.md
```

#### Folder Structure
```
.agents/
├── Coder/          # All Coder communications
├── QA/             # All QA communications
├── MLE/            # All MLE communications
└── README.md       # Protocol documentation
```

#### Status Tracking via Filename
| Status | Filename Pattern | Meaning |
|--------|------------------|---------|
| 🔴 **Pending** | `2603271500_Topic.md` | Staff needs to respond |
| 🟢 **Complete** | `2603271500_Topic_DONE.md` | Response complete, task done |

#### Workflow
1. **PM creates request:** Creates file in appropriate folder, no `_DONE` suffix
2. **Staff responds:** Edits same file, adds response under `## [Role] Response` section
3. **Staff marks complete:** Renames file by adding `_DONE` before `.md`

#### Response Format (Staff)
When responding, edit the SAME file and include:
```markdown
## [Role] Response

### Status
- [ ] In Progress
- [ ] Complete
- [ ] Blocked

### Notes / Blockers
(If blocked, explain what you need)

### Deliverable Summary
(If complete, describe what was delivered)
```

### 3.4 The One-Document Rule
**Every request or deliverable must fit in ONE document.**

If a task is too complex for one document, it must be broken into sub-tasks, each with its own document.

**Document Template:**
```markdown
# Request: [Brief Title]

## Requestor
[Who is asking for this]

## Context
[Why this is needed — 2-3 sentences max]

## Requirements
- [Specific requirement 1]
- [Specific requirement 2]
- [Specific requirement 3]

## Inputs
- Data source: [file path or query]
- Date range: [if applicable]
- Reference document: [link]

## Expected Output
[What the deliverable should look like]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

### 3.5 Response Time Expectations
| Type | Response Time | Example |
|------|---------------|---------|
| **Clarification** | 4 hours | "What does this parameter do?" |
| **Review Request** | 24 hours | "Please review this analysis" |
| **Task Assignment** | 48 hours | "Implement this feature" |
| **Urgent Bug** | 2 hours | "Positions not closing" |

### 3.6 Version Control for Documents
- All documents live in the repo
- When updating: append to history, don't overwrite context
- Use `## History` section at bottom:
```markdown
## History
- 2026-03-27: Initial request (PM)
- 2026-03-28: QA added clarification on filter criteria
- 2026-03-29: MLE delivered results
```

### 3.7 Agent Communication Folder Structure
```
.agents/
├── [Request-to-Role]_[Title]_[YYYYMMDD].md    # PM requests to specific role
├── QA/                                         # QA responses and work-in-progress
│   ├── YYMMDDHHMM_[Description].md            # Active QA task (pending)
│   └── YYMMDDHHMM_[Description]_DONE.md       # Completed QA task
├── Coder/                                      # (future) Coder responses
└── MLE/                                        # (future) MLE responses
```

**QA Naming Convention:**
- Format: `YYMMDDHHMM_BriefDescription.md`
- When complete: Add `_DONE` suffix before `.md`
- Examples:
  - `2603271140_File_Audit.md` → `2603271140_File_Audit_DONE.md`

---

## 4. File Management Rules

### 4.1 Naming Conventions

**Analysis Scripts:**
```
[action]_[subject]_[optional_modifier].py

Examples:
  analyze_recovery_deep.py      ← "analyze" action, "recovery" subject, "deep" modifier
  simulate_6_configs.py         ← "simulate" action, "6_configs" subject
  fix_atr_weekend.py            ← "fix" action, "atr" subject, "weekend" modifier
  verify_v3_files.py            ← "verify" action, "files" subject, "v3" modifier
```

**Output Files:**
```
[date]_[description]_[version].[ext]

Examples:
  20260327_recovery_analysis_v2.csv
  20260327_6config_simulation.csv
```

### 4.2 The Archive Rule
When a file is superseded:
1. Move old version to `archive/` folder
2. Add date prefix: `20260327_old_filename.py`
3. Update any references in documentation

**Never delete immediately** — archive for 30 days minimum.

### 4.3 Cleanup Authority
PM has authority to archive files that are:
- Superseded by newer versions
- More than 30 days old and not referenced in documentation
- Temporary verification scripts (after verification complete)

**Exception:** Analysis outputs used in reports must be kept until report is archived.

### 4.4 Environmental Limitations (MT5 Availability)

**Work environment varies. Some tasks require MT5/Windows, others do not.**

#### When MT5 is NOT Present (e.g., macOS, no Windows access)

| Staff | CAN Do | CANNOT Do | Action for CANNOT |
|-------|--------|-----------|-------------------|
| **QA** | Analysis planning, script development, documentation | Fetch live tick data, run live simulations | Document needs, defer to Windows session |
| **Coder** | Code development, documentation, test planning | Compile MQ5, Strategy Tester, live testing | Prepare code, document compilation needs, defer to Windows |
| **MLE** | Feature engineering planning, model design | Validate against live market, fetch fresh data | Use cached data, note staleness, defer validation |
| **PM** | Coordination, documentation, task management | Compile code, run tests | Create test plans, document needs for Windows session |

**Rule:** When MT5-dependent work is identified, document it clearly and defer to next Windows/MT5 session. Do not attempt workarounds that compromise quality.

#### When MT5 IS Present (Windows with MT5)

All staff can perform their full responsibilities:
- **QA:** Fetch live data, run simulations, validate against market
- **Coder:** Compile code, run Strategy Tester, live testing
- **MLE:** Access latest data, validate features
- **PM:** Compile verification, test coordination

**Documentation Requirement:** When deferring MT5-dependent work, create a note in the task file:
```markdown
## MT5-Dependent Tasks (Deferred)
- [ ] Compile RGU_EA.mq5 — deferred to next Windows session
- [ ] Run Strategy Tester scenarios — deferred
```

---

## 5. Quality Gates

### 5.1 Before Submitting Code (Coder)
```
□ Compiles without warnings
□ All inputs have descriptions
□ Error handling for file/network operations
□ No hardcoded magic numbers
□ Tested with edge cases (0 lots, max spread, etc.)
□ Document updated if interface changed
```

### 5.2 Before Submitting Analysis (QA)
```
□ Data source documented
□ Date range stated
□ Filters match the question being asked
□ Results reproducible
□ Outliers investigated
□ One clear conclusion/recommendation
```

### 5.3 Before Submitting Model/Features (MLE)
```
□ No look-ahead bias in features
□ Train/test split respects time
□ Feature importance ranked
□ Model can be converted to setfile parameters
□ Performance metrics on holdout set
```

---

## 6. Current Project State

### Active Systems
| System | Status | Owner |
|--------|--------|-------|
| TCM v2.2 | **PRODUCTION** | Coder maintains |
| RGU EA | **IN DEVELOPMENT** | Coder implements |
| GUM | **FUTURE** | On hold |

### Active Decisions (Do Not Change Without PM Approval)
1. **MaxLevels=1** — Single position, no grid
2. **TCM Partial Close** — 50% at 1min, remainder at 2min
3. **ATR TP Multiplier** — 0.5x for all current sets
4. **Setfile Naming** — `gu_[tf][MAFast][MASlow][ATRTPMult].set`
5. **Lot Size** — 0.10 for sessions, 0.02 for full-time

### QA Daily Analysis Deliverables
QA generates three standardized analyses daily by 08:00 UTC:

| Analysis | File Pattern | Purpose | Key Metrics |
|----------|--------------|---------|-------------|
| **RecoveryAnalysis** | `{date}_RecoveryAnalysis.xlsx` | Track loss baskets, evaluate multi-layer recovery | Recovery rate by layer, net P&L, no-entry rate |
| **TimeAnalysis** | `{date}_TimeAnalysis.xlsx` | Evaluate time-based SL (1-30 min) | Win rate per increment, optimal SL per magic |
| **MAEAnalysis** | `{date}_MAEAnalysis.xlsx` | Evaluate ATR-based SL (3x-30x) | Coverage %, risk-adjusted return per multiplier |

**Location:** All analyses saved to `data/` folder  
**Escalation:** Anomalies reported to PM within 4 hours

---

## 7. Escalation

### When to Escalate to PM
- **Coder:** Interface changes, breaking changes to setfiles, new dependencies
- **QA:** Contradictory results, data quality issues, unclear requirements
- **MLE:** Need for additional data, feature viability questions, deployment concerns

### When to Escalate to User (via PM)
- Strategic decisions affecting profitability
- Architecture changes
- Risk parameter changes (SL, TP, lot sizing)

---

## 8. Acknowledgment

**By contributing to this project, you acknowledge:**
1. You have read and understood this charter
2. You will follow the communication rules
3. You will use the one-document format for requests
4. You will complete quality gates before submission
5. You accept PM has final say on file management and task priority

---

*This charter is a living document. Suggestions for improvement should be submitted as a one-document request to the PM.*
