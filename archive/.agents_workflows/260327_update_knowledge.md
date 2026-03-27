# Knowledge Update Workflow

## Overview
Structured workflow for updating the GU Trading knowledge base with new findings and analysis.

**CRITICAL:** Changes must be discussed before saving to avoid incorrect information in the knowledge base.

---

## Knowledge Hierarchy

The knowledge base follows a top-down hierarchical structure:

```
1. Expert Advisors (EAs)
   1.1. GU Strategy
        1.1.0. What is GU and how does it work
        1.1.1. Architecture & Entry Logic
        1.1.2. Exit Logic & Parameters
        1.1.3. Session Configurations
        1.1.4. Magic Number Conventions
        1.1.5. Setfile Standards
        1.1.6. Analysis Findings (dated)
   1.2. SL Maestro
        1.2.0. Purpose & Function
        1.2.1. Configuration
        1.2.2. Session-Based Settings
        1.2.3. Known Issues
   1.3. Other Utilities
        1.3.x. [Future utilities]

2. Data & Analysis
   2.1. Data Sources
        2.1.1. MT5 History
        2.1.2. utc_history.csv
   2.2. Analysis Methods
        2.2.1. P/L Normalization
        2.2.2. Session Filtering
        2.2.3. Statistical Measures
   2.3. Historical Findings
        2.3.x. [Dated analysis entries]

3. Environment & Setup
   3.1. Broker Configuration
   3.2. MT5 Setup
   3.3. DST Adjustments

4. Workflows
   4.1. Setfile Creation
   4.2. Data Export
   4.3. Reporting
```

---

## Update Process (4 Steps)

### Step 1: Assess Existing Knowledge

Before adding new information:

1. **Locate relevant section** in knowledge hierarchy
2. **Review existing content** in that section
3. **Identify conflicts** between new and existing info
4. **Check for outdated information** that needs updating

**Questions to ask:**
- Where does this information fit in the hierarchy?
- Does it contradict existing knowledge?
- Does it update/extend existing knowledge?
- Is the existing information still valid?

### Step 2: Draft Changes (DO NOT SAVE YET)

Prepare the update for discussion:

```markdown
## PROPOSED UPDATE: [Topic]

**Section:** [e.g., 1.1.6. Analysis Findings]

**Type of Change:**
- [ ] New finding
- [ ] Correction to existing
- [ ] Update/refinement
- [ ] Deprecation of old info

**Content:**
[Draft the proposed content here]

**Rationale:**
[Explain why this change is needed]

**Conflicts with Existing:**
[List any contradictions with current knowledge]

**Supporting Data:**
[Attach analysis results, statistics, etc.]
```

### Step 3: DISCUSS Before Saving

**Present to user for approval:**
- Summary of proposed changes
- Impact on existing knowledge
- Any conflicts or questions

**Wait for explicit approval** before proceeding to Step 4.

### Step 4: Save to Knowledge Base

Only after discussion and approval:

1. Append/update the relevant section
2. Add cross-references if needed
3. Update "Last Modified" date
4. Verify formatting is correct

---

## Change Types & Handling

### Type A: New Finding
- **Action:** Add new dated subsection
- **Example:** "March 13, 2026 — MaxLevels=1 Analysis"
- **Process:** Draft → Discuss → Append

### Type B: Correction
- **Action:** Update existing content, add correction note
- **Example:** Fixing magic number mapping
- **Process:** Identify error → Draft correction → Discuss → Update

### Type C: Deprecation
- **Action:** Mark old info as deprecated, add new info
- **Example:** Old DST settings, old parameter values
- **Process:** Draft deprecation notice → Discuss → Update

### Type D: Convention Change
- **Action:** Update all affected sections
- **Example:** Filename conventions, lot sizes
- **Process:** Identify all occurrences → Draft changes → Discuss → Update all

---

## Quality Checklist

Before marking update complete:

- [ ] Change fits in knowledge hierarchy
- [ ] No contradictions with existing (unless correcting)
- [ ] Specific numbers/dates included
- [ ] Cross-references added
- [ ] User approved the change
- [ ] No TODO items in knowledge base (move to todo.md)

---

## Example: Adding New Analysis

**Scenario:** Completed MaxLevels=1 analysis

**Step 1 - Assess:**
- Fits in: 1.1.6 (GU Strategy → Analysis Findings)
- Related to: Session configurations, MaxLevels parameter
- Conflicts: None (new analysis)

**Step 2 - Draft:**
```markdown
## PROPOSED UPDATE: MaxLevels=1 Analysis

**Section:** 1.1.6. Analysis Findings

**Type:** New finding

**Content:**
[Include all findings from analysis...]

**Rationale:** Critical discovery about London requiring time exits
```

**Step 3 - Discuss:**
Present to user: "I've analyzed 138 positions and found London MUST have time-based exits. Here are the detailed findings... [present draft] Should I add this to the knowledge base?"

**Step 4 - Save:**
After user approval, append to knowledge_base.md

---

## Related Files

- `knowledge_base.md` — Main knowledge repository
- `todo.md` — Task tracking (separate from knowledge)
- `create_gu_sets.py` — Setfile generation workflow

## Maintenance

**Monthly:**
- Review todo.md for completed items
- Archive completed tasks

**Quarterly:**
- Review knowledge base for outdated information
- Update DST calendar
- Consolidate multiple findings on same topic

**Annually:**
- Full review of knowledge hierarchy
- Restructure if needed
- Archive very old findings to separate historical file
