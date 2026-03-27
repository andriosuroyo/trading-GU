# 🚨 ALL STAFF: Knowledge Base Major Update

**Date:** 260327  
**Type:** Critical Knowledge Update — All Staff Must Read  
**From:** PM  
**To:** QA, Coder, MLE, and all future staff

---

## ⚠️ CRITICAL CHANGE: Magic Number System Overhauled

Effective **March 23, 2026**, the magic number system and setfile organization have completely changed. This affects **all analysis, coding, and modeling work**.

---

## What Changed

### OLD System (Deprecated — Do Not Use)
```
Magic numbers encoded session + strategy:
  11 = MH Asia      21 = HR10 Asia      31 = HR05 Asia
  12 = MH London    22 = HR10 London    32 = HR05 London
  13 = MH NY        23 = HR10 NY        33 = HR05 NY

Setfiles organized by session:
  gu_mh_asia.set, gu_mh_london.set, gu_mh_ny.set
```

### NEW System (Current — Use This)
```
Magic numbers are SEQUENTIAL: 1, 2, 3, 4, 5...
Strategy encoded in CommentTag: GU_m1052005, GU_m1208005, etc.

Setfile naming:
  gu_[timeframe][MAFast][MASlow][ATRTPMult].set
  
Examples:
  gu_m1052005.set = M1, MA 5/20, 0.5x ATR TP, Magic=1
  gu_m1208005.set = M1, MA 20/80, 0.5x ATR TP, Magic=3
  gu_m1104005.set = M1, MA 10/40, 0.5x ATR TP, Magic=2
```

---

## Impact by Role

### For QA (Quantitative Analyst)
**OLD:** Analyze by magic number groupings (11-13, 21-23, 31-33)  
**NEW:** Analyze by **CommentTag** (e.g., GU_m1052005, GU_m1208005)

**What You Must Change:**
- All analysis scripts: Filter by CommentTag, not magic number ranges
- Daily analyses (RecoveryAnalysis, TimeAnalysis, MAEAnalysis): Organize sheets by strategy name, not "Magic11, Magic12"
- Session analysis: Derive session from OpenTime, not from magic number

**Reference File:** `knowledge_base.md` — "Current Setfile System" section

---

### For Coder (MQ5/MQL5 Specialist)
**OLD:** Filter by magic numbers like "11,12,13"  
**NEW:** Filter by CommentTag containing "GU_" or magic numbers individually

**What You Must Change:**
- RGU EA: Already uses CommentTag filter ("GU_") — ✅ correct
- TCM: Filter by CommentTag "GU_" or magic number list "1,2,3,4,5..."
- Any hardcoded magic references: Update to new sequential system

**Reference File:** `knowledge_base.md` — "Current Setfile System" section

---

### For MLE (Machine Learning Engineer)
**OLD:** Magic numbers (11-13, 21-23, 31-33) as categorical features  
**NEW:** **CommentTag** (e.g., GU_m1052005) as categorical feature

**What You Must Change:**
- Feature engineering: Use CommentTag for strategy identification
- Session feature: Derive from OpenTime (Asia 02-06, London 08-12, NY 17-21 UTC)
- Do not use magic numbers as strategy identifiers

**Reference File:** `knowledge_base.md` — "Session Analysis" and "Current Setfile System" sections

---

## Why This Changed

**User Decision (March 23, 2026):**
- Decoupled strategy from session for more flexible testing
- Unified trading window (02:00-23:00 UTC) avoids open/close volatility
- Session analysis still valuable post-trade but doesn't dictate organization

**Root Cause:** Previous PM (me) propagated outdated info from old `knowledge_base.md` without validating against actual setfiles.

---

## Single Source of Truth

**`knowledge_base.md` is now the ONLY authoritative source.**

- All other documents derive from this file
- Deprecated information clearly marked with dates
- Change log tracks all updates
- PM will update within 24 hours of any new information

**Do not assume other files are current.** Always validate against `knowledge_base.md`.

---

## Files Already Updated

✅ `knowledge_base.md` — Complete rewrite with new system  
✅ `PROJECT_SUMMARY.md` — Architecture diagram fixed  
✅ `TEAM_CHARTER.md` — Knowledge requirements updated  
✅ `.agents/QA/2603271705_Daily_Analysis_Workflow_DONE.md` — Analysis structure updated  
✅ `.agents/MLE/2603271510_Task1_Feature_Engineering.md` — Feature engineering specs updated  
✅ `.agents/README.md` — Summary updated  

---

## What You Must Do Now

### All Staff:
1. [ ] Read `knowledge_base.md` — "Current Setfile System" section
2. [ ] Read "Deprecated Information" section to understand what changed
3. [ ] Update any personal notes or scripts that reference old magic system
4. [ ] Confirm understanding by checking box below

### QA Specifically:
1. [ ] Update daily analysis scripts to use CommentTag, not magic ranges
2. [ ] Q1 (Data Source): ✅ Direct MT5 fetch is correct
3. [ ] Q2 (Active Magics): ✅ Organize by CommentTag (GU_m1052005, etc.)

### Coder Specifically:
1. [ ] Verify RGU and TCM use CommentTag filter correctly

### MLE Specifically:
1. [ ] Update feature engineering plan: CommentTag as categorical, not magic numbers

---

## Staff Confirmation & Communication

**When you have read and understood this update:**
1. Edit this file
2. Find your name below
3. Check the box: "I have read and understood the new magic number system"
4. Add any questions in "Questions/Clarifications"

### Direct Communication with User

**You are encouraged to ask the User directly for clarifications on:**
- Strategy decisions or rationale
- Questions about trading rules or preferences
- Concerns about implementation approach
- Anything that affects the "why" behind the work

**How to ask the User:**
1. Edit this file under "Questions for User" below
2. Tag your question with your role (QA/Coder/MLE) and date
3. The User will respond when they review

**When to ask PM vs User:**
| Ask PM | Ask User |
|--------|----------|
| Process questions | Strategy decisions |
| File locations | Trading logic |
| Task priorities | Risk tolerance |
| Coordination | Performance expectations |
| Technical implementation details | Business requirements |

### Questions for User

*(Staff: Add your questions here. Tag with role and date)*

**Example format:**
```
[QA - 260327]: Should TimeAnalysis include all 30 time increments or focus on 1-10 min range?
```

---

### Staff Confirmation Checkboxes

### QA Confirmation
- [ ] I have read and understood the new magic number system

**Questions/Clarifications:**
*(Add here)*

### Coder Confirmation
- [ ] I have read and understood the new magic number system

**Questions/Clarifications:**
*(Add here)*

### MLE Confirmation
- [ ] I have read and understood the new magic number system

**Questions/Clarifications:**
*(Add here)*

---

## Reference Materials

| File | Purpose |
|------|---------|
| `knowledge_base.md` | **Primary reference** — complete system documentation |
| `Setfiles/20260322/*.set` | **Ground truth** — actual current setfiles |
| `KNOWLEDGE_AUDIT_260327.md` | Audit report showing what was wrong |
| `KNOWLEDGE_FIX_SUMMARY_260327.md` | Summary of all fixes made |

---

## History
- 260323: System changed (user decision)
- 260323-260327: PM unknowingly propagated outdated information
- 260327: Knowledge audit revealed inconsistencies
- 260327: Knowledge base fixed, all documents updated
- 260327: This notification created
