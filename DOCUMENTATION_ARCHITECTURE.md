# Documentation Architecture

## Three-Layer Documentation System

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: ENTRY POINT (README.md)                           │
│  ─────────────────────────────────                          │
│  Audience: Anyone (you, new staff, future collaborators)    │
│  Purpose: "What is this project? Where do I start?"         │
│  Content: High-level overview, navigation, quick links      │
│  Frequency: Rarely changes                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: KNOWLEDGE (knowledge_base.md)                     │
│  ─────────────────────────────────                          │
│  Audience: All staff (QA, Coder, MLE, PM)                   │
│  Purpose: "What is true about this trading system?"         │
│  Content: Strategy, parameters, decisions, deprecated info  │
│  Frequency: Changes when strategy/system changes            │
│  Status: SINGLE SOURCE OF TRUTH                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: OPERATIONS (TEAM_CHARTER.md, .agents/README.md)   │
│  ─────────────────────────────────                          │
│  Audience: Staff + PM                                       │
│  Purpose: "How do we work together?"                        │
│  Content: Processes, protocols, communication rules         │
│  Frequency: Changes when workflow changes                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Breakdown

### 1. README.md (Root)

**Purpose:** Project entry point and navigation hub

**Audience:**
- You (quick reference)
- New staff joining the project
- Future collaborators
- Anyone asking "What is Trading_GU?"

**Content:**
- One-paragraph project description
- Quick navigation links ("For strategy details → knowledge_base.md")
- Status dashboard (what's currently happening)
- How to get started

**Current State:** We don't have a main README.md (we have MOBILE_README.md and ORGANIZATION_README.md)

**Should Contain:**
```markdown
# Trading_GU

Automated XAUUSD scalping system with time-based risk management.

## Quick Navigation
- Strategy details: knowledge_base.md
- How we work: TEAM_CHARTER.md
- Current tasks: .agents/README.md

## Current Status
- RGU: In testing
- TCM: Production v2.2
- MLE: On hold (awaiting data)
```

---

### 2. knowledge_base.md

**Purpose:** Single source of truth for trading system knowledge

**Audience:**
- All staff (QA, Coder, MLE)
- You (ground truth reference)
- PM (to answer staff questions accurately)

**Content:**
- Trading strategy parameters
- Setfile naming conventions
- Magic number system
- Risk management rules
- What decisions were made and why
- What's deprecated

**Key Principle:**
> "If knowledge_base.md says X, then X is true. All other documents must align with it."

**Changes:**
- Updated when strategy/system changes
- PM updates within 24 hours of learning new info
- Clear deprecation markers for old info

---

### 3. TEAM_CHARTER.md

**Purpose:** How the team works together (process, not content)

**Audience:**
- Staff (QA, Coder, MLE)
- PM (reference for enforcing standards)

**Content:**
- Communication rules (PM as bridge)
- When to ask PM vs User
- File naming conventions
- Quality gates (what to check before submitting)
- Response time expectations

**Analogy:**
- knowledge_base.md = "What we're building"
- TEAM_CHARTER.md = "How we build it together"

**Changes:**
- Updated when workflow/process changes
- Not tied to trading strategy

---

### 4. .agents/README.md

**Purpose:** Communication protocol for the .agents/ folder specifically

**Audience:**
- PM (creating requests)
- Staff (responding to requests)

**Content:**
- File naming convention (YYMMDDHHMM_Topic.md)
- How to mark tasks complete (_DONE suffix)
- Current status of all active communications
- Quick template for new requests

**Scope:**
- ONLY covers the .agents/ folder workflow
- Operational/tactical, not strategic

**Changes:**
- Updated daily as tasks complete
- Staff update their own task status

---

## Summary Table

| File | Audience | Purpose | Content Type | Change Frequency |
|------|----------|---------|--------------|------------------|
| **README.md** (root) | Everyone | Entry point, navigation | Links, overview | Rarely |
| **knowledge_base.md** | All staff | Ground truth | Strategy, parameters, decisions | When strategy changes |
| **TEAM_CHARTER.md** | All staff | How we work | Processes, protocols, rules | When workflow changes |
| **.agents/README.md** | PM + Staff | Task coordination | Status, templates, protocol | Daily |

---

## Current Issue: No Root README.md

We currently have:
- ✅ knowledge_base.md (ground truth)
- ✅ TEAM_CHARTER.md (how we work)
- ✅ .agents/README.md (task coordination)
- ❌ README.md (entry point)

**Recommendation:** Create a root README.md as the navigation hub.

---

## Visual Flow

```
New person joins project
        │
        ▼
   README.md (root)
        │
        ├──→ "I need to understand strategy" ──→ knowledge_base.md
        │
        ├──→ "I need to know how to work" ───→ TEAM_CHARTER.md
        │
        └──→ "I need to see current tasks" ──→ .agents/README.md
```

---

## Your Question Answered

**README.md vs TEAM_CHARTER.md:**
- README.md = "Welcome, here's where to find things" (navigation)
- TEAM_CHARTER.md = "Here's how we work together" (operating rules)

**README.md vs knowledge_base.md:**
- README.md = "This is a trading project" (what it is)
- knowledge_base.md = "We trade XAUUSD with MA crossovers at 0.5x ATR" (how it works)

**.agents/README.md vs others:**
- .agents/README.md = "Task #2603271500 is pending QA response" (tactical status)
- Others = Strategic/operational documentation
