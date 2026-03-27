# .agents/ Folder — Communication Protocol

**This folder contains all PM-staff communications.**

---

## Quick Reference

### For PM
**Create new request:**
1. Choose folder: `QA/`, `Coder/`, or `MLE/`
2. Name file: `YYMMDDHHMM_Topic.md` (e.g., `2603271500_File_Audit.md`)
3. Use template below
4. Do NOT add `_DONE` suffix (that's for staff to add when complete)

### For Staff (QA, Coder, MLE)
**Respond to request:**
1. Open the `.md` file PM created for you
2. Edit the SAME file (do not create new file)
3. Add your response under `## [Role] Response`
4. Update status: In Progress / Complete / Blocked / On Hold
5. **When complete:** Rename file by adding `_DONE` before `.md`
   - Example: `2603271500_Topic.md` → `2603271500_Topic_DONE.md`

**Ask User directly for clarifications:**
- Strategy decisions, trading rules, business logic
- Edit `.agents/260327_Knowledge_Base_Major_Update.md` — "Questions for User" section
- PM handles task routing; User handles strategy decisions

---

## Current Status (2603271457)

### Pending / Active (Awaiting Response)

| File | Staff | Topic | Deadline | Notes |
|------|-------|-------|----------|-------|
| *(none — QA developing scripts)* | — | — | — | — |

### On Hold (Awaiting Data Accumulation)

| File | Staff | Topic | Hold Reason | Decision Made |
|------|-------|-------|-------------|---------------|
| `2603271510_Task1_Feature_Engineering.md` | MLE | Phase 1 feature engineering | Insufficient data (need end of week) | ✅ Option B: Unified model with Magic as categorical |
| `2603271500_Cleaned_Position_History_ONHOLD.md` | QA | Regenerate dataset | Wait for more data (200+ positions) | March 23+ data only |

### Completed (Recently)

| File | Staff | Topic |
|------|-------|-------|
| `2603271705_Daily_Analysis_Workflow_DONE.md` | **QA** | Daily analysis workflow ✅ **ACKNOWLEDGED** |
| `2603271600_RGU_Compilation_Bug_DONE.md` | Coder | RGU compilation fixed ✅ |
| `2603271500_Cleaned_Position_History_DONE.md` | QA | Cleaned position history delivered ✅ |
| `2603271505_RGU_CSV_Output_DONE.md` | Coder | RGU CSV output implemented ✅ |
| `2603271140_File_Audit_DONE.md` | QA | File audit completed ✅ |
| `2603271142_RGU_Status_DONE.md` | Coder | RGU status confirmed ✅ |
| `2603271134_Onboarding_DONE.md` | MLE | Onboarding complete ✅ |

---

## Staff Status Summary

| Staff | Status | Current Focus | Pending / On Hold |
|-------|--------|---------------|-------------------|
| **QA** | 🟡 **DEVELOPING** | Creating 3 daily analysis scripts (24h) | ⏸️ Dataset regeneration (end of week) |
| **Coder** | 🟡 Next | RGU test setfile + testing support | — |
| **MLE** | ⏸️ ON HOLD | Awaiting data | End of week |
| **PM** | 🟡 Active | RGU testing coordination, answer QA Qs | — |

### Recent Milestone
✅ **QA acknowledged daily analysis workflow** — 3 clarification questions raised

---

## Priority Summary

### ✅ P1 — RGU Compilation Bug — FIXED
**File:** `2603271600_RGU_Compilation_Bug_DONE.md`  
**Staff:** Coder  
**Status:** ✅ **FIXED** — 0 errors, 0 warnings  
**Next:** RGU testing unblocked

### 🟡 P2 — RGU Testing — NOW ACTIVE  
**Staff:** PM + Coder  
**Tasks:**
- Create test setfile `Setfiles/RGU/RGU_Test_v3.set`
- Strategy Tester validation (5 scenarios)
- Document any bugs found

### 🟡 P3 — QA Daily Analysis Scripts — IN PROGRESS
**Staff:** QA  
**Timeline:** 24 hours  
**First Run:** March 28, 2026 08:00 UTC

### ⏸️ P4 — MLE Feature Engineering (ON HOLD)  
**File:** `2603271510_Task1_Feature_Engineering.md`  
**Staff:** MLE  
**Hold Reason:** Insufficient data (need end of week)  
**ML Approach:** ✅ Option B decided (unified model with Magic as categorical)

### ⏳ P5 — TCM Live Testing  
**Status:** Next Windows session  
**Staff:** PM

---

## QA Questions Requiring PM/User Input

### Q1: Data Source
**Issue:** MQL5/Files/ folder is empty. QA proposes fetching directly from MT5 terminals.  
**Decision needed:** Accept direct MT5 fetch, or wait for EA CSV output?

### Q2: Active Magic Numbers
**Issue:** Data shows primarily magics 11-13 (Sell strategies), minimal 21-23 and 31-33.  
**Decision needed:** Handle all 9 magics, or focus on active ones?

### Q3: MAEAnalysis Reference
**Issue:** No reference file exists for MAEAnalysis.  
**Status:** QA will design based on TimeAnalysis pattern — no action needed.

---

## Recent Decisions

| Decision | Selected | Impact |
|----------|----------|--------|
| **ML Multi-Setting Approach** | ✅ **Option B:** Unified model with Strategy as categorical | MLE will train one model; CommentTag (e.g., GU_m1052005) as categorical feature |

---

## File Template

```markdown
# [Request/Task]: [Brief Title]

**Status:** 🔴 PENDING RESPONSE / 🟡 IN PROGRESS / 🟢 COMPLETE / ⏸️ ON HOLD  
**From:** PM  
**To:** [QA/Coder/MLE]  
**Time:** YYMMDDHHMM

---

## Context
[Why this is needed]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Timeline
**Deadline:** YYMMDDHHMM

---

## Response Instructions

**When responding:**
1. Edit THIS file directly — do not create a new file
2. Add your response below under "## [Role] Response"
3. Check status checkbox and update as needed
4. When complete, RENAME this file by adding "_DONE" before ".md"

---

## [Role] Response

### Status
- [ ] In Progress
- [ ] Complete
- [ ] Blocked
- [ ] On Hold

### Notes / Blockers
[If blocked, explain what you need]

### Deliverable Summary
[If complete, describe what was delivered]

---

## History
- YYMMDDHHMM: Initial request (PM)
```

---

## Full Documentation

See `TEAM_CHARTER.md` Section 3.2 for complete protocol.

---

*Last updated: 260327 — Knowledge base major update created for all staff*
