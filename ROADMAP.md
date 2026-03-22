# Project Roadmap: Trading GU Systems

> **Project Leader:** Viktor Kozlov (Systems Architect)  
> **Last Updated:** 2026-03-20  
> **Status:** ACTIVE — TCM v2.3.0 Testing Phase  
> **Next Milestone:** TCM v2.3.0 Live Deployment

---

## Document Control

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-20 | Initial roadmap created | Viktor Kozlov |

### Change Protocol
**Who can modify:** Viktor Kozlov (primary), Andrio Suroyo (project owner)  
**How to request changes:** Open GitHub issue with label `roadmap-change`  
**Review cycle:** Roadmap reviewed weekly every Monday  
**Insertion of new items:** See Section 6 (Change Management Protocol)

---

## 1. Project Overview

### Vision
Build a self-optimizing, institutional-grade XAUUSD scalping system consisting of:
1. **TCM** — Time-based risk management with session awareness
2. **GUS** — Self-optimizing trade quality scoring engine
3. **RecoveryManager** — Mean reversion opportunity tracking

### Current Team
| Role | Name | Status | Start Date | Comms Protocol |
|------|------|--------|------------|----------------|
| Systems Architect | Viktor Kozlov | Active | 2026-03-20 | All via Andrio |
| Project Owner | Andrio Suroyo | Active | 2026-03-20 | Hub for all comms |
| MQ5 Specialist | [Hiring] | Pending | TBD | Via Andrio only |
| Quant Analyst | [Hiring] | Pending | TBD | Via Andrio only |
| ML Engineer | [Hiring] | Pending | TBD | Via Andrio only |

### Communication Architecture
```
Viktor (Architect) ↔ Andrio (Owner) ↔ Team (Implementers)
```
**Rule:** No direct contact between Viktor and implementers. All flows through Andrio.
**Rationale:** Single source of truth, reduced context switching, clear authority chain.

### Technology Stack
- **Platform:** MetaTrader 5 (Windows)
- **Language:** MQL5 (strict mode)
- **Broker:** VantageInternational-Demo (testing) → VantageInternational-Live (production)
- **Data Storage:** CSV (Phase 1) → PostgreSQL (Phase 3)
- **Notifications:** Discord Webhooks
- **Version Control:** GitHub
- **Project Management:** This roadmap + GitHub Issues
- **Communication:** Andrio as hub (single point of contact)

### MQ5 Specialist Profile (Confirmed)
- ✅ Git proficient (branching, merging, conflict resolution)
- ✅ Trading experience (understands XAUUSD, pips, sessions)
- ✅ Will use own Windows/MetaEditor setup
- ✅ Vantage Demo access provided by Andrio
- ⏳ Start date: [TO BE FILLED]

---

## 2. Phase Breakdown

### Phase 1: Foundation (Weeks 1-6) — CURRENT
**Goal:** Stabilize TCM v2.3.0, implement GUS v1.0.0, prove core concepts

| ID | Task | Owner | Dependencies | Status | Target Date | Completed Date |
|----|------|-------|--------------|--------|-------------|----------------|
| 1.1 | TCM v2.3.0 Testing | Andrio | 2.3.0 code complete | 🔄 IN PROGRESS | 2026-03-25 | |
| 1.2 | TCM v2.3.0 Bug Fixes | MQ5 Specialist | 1.1 complete | ⏳ PENDING | 2026-03-28 | |
| 1.3 | TCM v2.3.0 Live Deploy | Andrio | 1.2 complete | ⏳ PENDING | 2026-03-30 | |
| 1.4 | Hire MQ5 Specialist | Andrio | None | 🔄 IN PROGRESS | 2026-03-22 | |
| 1.5 | MQ5 Onboarding | Viktor | 1.4 complete | ⏳ PENDING | 2026-03-25 | |
| 1.6 | GUS v1.0.0 Implementation | MQ5 Specialist | 1.5 complete | ⏳ PENDING | 2026-04-15 | |
| 1.7 | GUS v1.0.0 Testing | Andrio | 1.6 complete | ⏳ PENDING | 2026-04-20 | |
| 1.8 | GUS v1.0.0 Live Deploy | Andrio | 1.7 complete | ⏳ PENDING | 2026-04-25 | |
| 1.9 | Collect 500-trade dataset | System | 1.8 complete | ⏳ PENDING | 2026-05-10 | |

**Phase 1 Success Criteria:**
- [ ] TCM v2.3.0 runs 30 days without critical bug
- [ ] GUS v1.0.0 scores 500+ trades
- [ ] GUS weight adjustments show convergence (top factor >0.30 correlation)
- [ ] Discord alerts functional (≥80 score triggers)

---

### Phase 2: Intelligence (Weeks 7-12)
**Goal:** Add quantitative validation and recovery tracking

| ID | Task | Owner | Dependencies | Status | Target Date | Completed Date |
|----|------|-------|--------------|--------|-------------|----------------|
| 2.1 | Hire Quant Analyst | Andrio | 1.9 complete | ⏳ PENDING | 2026-05-15 | |
| 2.2 | Quant Onboarding | Viktor | 2.1 complete | ⏳ PENDING | 2026-05-18 | |
| 2.3 | RFC 003: RecoveryManager Spec | Viktor | None | ⏳ PENDING | 2026-05-20 | |
| 2.4 | RecoveryManager Implementation | MQ5 Specialist | 2.3 complete | ⏳ PENDING | 2026-06-05 | |
| 2.5 | RecoveryManager Testing | Andrio | 2.4 complete | ⏳ PENDING | 2026-06-10 | |
| 2.6 | GUS Correlation Analysis | Quant | 1.9 complete | ⏳ PENDING | 2026-05-25 | |
| 2.7 | GUS Weight Optimization Report | Quant | 2.6 complete | ⏳ PENDING | 2026-05-30 | |
| 2.8 | Database Migration Plan | Viktor | 2.6 complete | ⏳ PENDING | 2026-06-01 | |

**Phase 2 Success Criteria:**
- [ ] RecoveryManager tracks 20+ recovery candidates
- [ ] Quant validates GUS score ≥80 has >65% win rate
- [ ] Database schema designed for 10k+ trades
- [ ] Recovery success rate >55% (vs random entry ~50%)

---

### Phase 3: Scale (Weeks 13-20)
**Goal:** Machine learning integration and portfolio risk management

| ID | Task | Owner | Dependencies | Status | Target Date | Completed Date |
|----|------|-------|--------------|--------|-------------|----------------|
| 3.1 | Hire ML Engineer | Andrio | 2.7 complete | ⏳ PENDING | 2026-06-15 | |
| 3.2 | ML Engineer Onboarding | Viktor | 3.1 complete | ⏳ PENDING | 2026-06-18 | |
| 3.3 | RFC 004: GUS v2.0 ML Spec | Viktor + ML | 2.7 complete | ⏳ PENDING | 2026-06-25 | |
| 3.4 | PostgreSQL Database Setup | DevOps | 2.8 complete | ⏳ PENDING | 2026-06-20 | |
| 3.5 | Data Migration (CSV → SQL) | MQ5 Specialist | 3.4 complete | ⏳ PENDING | 2026-06-30 | |
| 3.6 | GUS v2.0 ML Implementation | ML + MQ5 | 3.3 complete | ⏳ PENDING | 2026-07-20 | |
| 3.7 | Portfolio Risk Manager Spec | Viktor | 3.4 complete | ⏳ PENDING | 2026-07-01 | |
| 3.8 | Portfolio Risk Manager Implementation | MQ5 Specialist | 3.7 complete | ⏳ PENDING | 2026-07-25 | |
| 3.9 | Integrated Testing (All Systems) | All | 3.6, 3.8 complete | ⏳ PENDING | 2026-08-05 | |

**Phase 3 Success Criteria:**
- [ ] GUS v2.0 outperforms v1.0 by >10% (win rate or profit factor)
- [ ] Database handles 50k+ trades with <100ms query time
- [ ] Portfolio risk manager prevents correlation blow-ups
- [ ] System runs 3 sessions (Asia/London/NY) simultaneously

---

### Phase 4: Hardening (Weeks 21-26)
**Goal:** Production hardening, security, monitoring

| ID | Task | Owner | Dependencies | Status | Target Date | Completed Date |
|----|------|-------|--------------|--------|-------------|----------------|
| 4.1 | Security Audit | DevSecOps | 3.9 complete | ⏳ PENDING | 2026-08-15 | |
| 4.2 | Credentials Vault Implementation | DevSecOps | 4.1 complete | ⏳ PENDING | 2026-08-20 | |
| 4.3 | Grafana Monitoring Dashboard | DevOps | 3.4 complete | ⏳ PENDING | 2026-08-10 | |
| 4.4 | Automated Backup System | DevOps | 3.4 complete | ⏳ PENDING | 2026-08-15 | |
| 4.5 | Disaster Recovery Runbook | Viktor | 4.2, 4.4 complete | ⏳ PENDING | 2026-08-25 | |
| 4.6 | 30-Day Live Stress Test | All | 4.5 complete | ⏳ PENDING | 2026-09-15 | |

**Phase 4 Success Criteria:**
- [ ] Zero security vulnerabilities (penetration test passed)
- [ ] 99.9% uptime over 30 days
- [ ] <5 minute recovery from any single failure
- [ ] All credentials in vault, rotated monthly

---

### Phase 5: Optimization (Ongoing from Week 27+)
**Goal:** Continuous improvement, strategy expansion

| ID | Task | Owner | Dependencies | Status | Target Date | Completed Date |
|----|------|-------|--------------|--------|-------------|----------------|
| 5.1 | Strategy Expansion (New Pairs) | Quant + Viktor | 4.6 complete | ⏳ PENDING | 2026-10-01 | |
| 5.2 | GUS v3.0 Deep Learning | ML | 4.6 complete | ⏳ PENDING | 2026-11-01 | |
| 5.3 | Multi-Broker Arbitrage | Viktor | 4.6 complete | ⏳ PENDING | 2026-12-01 | |
| 5.4 | Signal Service (External Clients) | Business | 4.6 + track record | ⏳ PENDING | 2027-Q1 | |

---

## 3. Dependency Graph

```
[Start]
   │
   ├──→ [1.4 Hire MQ5] ──→ [1.5 Onboard MQ5] ──→ [1.6 GUS v1.0 Impl]
   │                                                    │
   │                            [1.1 TCM v2.3 Test] ──→ [1.2 Bug Fixes]
   │                               (parallel)              │
   │                                                       ↓
   │                            [1.3 TCM v2.3 Live] ←────┘
   │                               │
   │                               ↓
   │                            [1.9 Collect 500 trades]
   │                               │
   │                               ├──→ [2.1 Hire Quant]
   │                               │       │
   │                               │       └──→ [2.6 Correlation Analysis]
   │                               │               │
   │                               │               └──→ [2.7 Optimization Report]
   │                               │                       │
   │                               │                       └──→ [3.1 Hire ML]
   │                               │
   │                               └──→ [2.3 RFC RecoveryManager]
   │                                       │
   │                                       └──→ [2.4 Recovery Impl]
   │
   └──→ [Parallel Track: Infrastructure]
            │
            ├──→ [3.4 PostgreSQL Setup]
            │       │
            │       ├──→ [3.5 Data Migration]
            │       └──→ [4.3 Grafana Dashboard]
            │
            └──→ [4.1 Security Audit]
                    │
                    └──→ [4.2 Credentials Vault]
```

---

## 4. Weekly Rhythm

### Monday: Planning & Review (1 hour)
- **Attendees:** Viktor, Andrio, MQ5 Specialist (if hired)
- **Agenda:**
  1. Review completed tasks from last week
  2. Update roadmap dates/status
  3. Identify blockers
  4. Assign tasks for the week
- **Output:** Updated ROADMAP.md, GitHub issues created/updated

### Wednesday: Technical Sync (30 min)
- **Attendees:** Viktor, MQ5 Specialist
- **Agenda:**
  1. Code review of completed work
  2. Architecture questions
  3. Bug triage

### Friday: Demo & Retrospective (1 hour)
- **Attendees:** Full team
- **Agenda:**
  1. Demo working features
  2. Review metrics (trades scored, bugs found, etc.)
  3. Process improvements

---

## 5. Critical Path (Must Not Slip)

The following sequence has zero float:

```
1.4 Hire MQ5 → 1.5 Onboard → 1.6 GUS Impl → 1.7 GUS Test → 1.8 GUS Live → 1.9 Dataset
```

**If 1.4 (Hire MQ5) slips by 1 week, entire Phase 1 slips by 1 week.**

**Mitigation:**
- Have 2-3 candidates interviewed before 1.4 target date
- If hiring fails by 2026-03-25, Viktor implements GUS solo (slows Phase 2 by 4 weeks)

---

## 6. Change Management Protocol

### 6.1 Adding New Tasks

**Who can propose:** Anyone  
**How:** Open GitHub Issue with:
- Title: `[ROADMAP] Brief description`
- Body: Why needed, estimated effort, proposed phase/position

**Decision process:**
1. Viktor reviews within 48 hours
2. If <4 hours effort: Viktor approves directly, adds to current phase
3. If 4-16 hours: Andrio approves (business priority)
4. If >16 hours: Schedule call to discuss trade-offs

**Insertion rules:**
- **Phase 1:** Frozen except critical bugs. New features go to Phase 2.
- **Phase 2+:** Can insert if dependencies allow and target date <4 weeks out
- **Emergency:** Critical bug in live system can interrupt any phase

### 6.2 Handling Unforeseen Problems

**Problem Categories:**

| Category | Example | Response | Owner |
|----------|---------|----------|-------|
| **Critical Bug** | TCM v2.3.0 crashes in live trading | Stop all work, fix immediately | MQ5 Specialist + Viktor |
| **Architectural Blocker** | GUS can't work with TCM as designed | Viktor redesigns, team pivots | Viktor |
| **Resource Shortage** | MQ5 Specialist quits | Viktor covers, expedite rehire | Andrio |
| **External Dependency** | Vantage API changes | Assess impact, adjust timeline | Viktor |
| **Scope Creep** | "Can we also track EURUSD?" | Evaluate in next phase | Andrio decides |

**Escalation Path:**
1. Team member identifies problem → Post in #urgent channel
2. If not resolved in 4 hours → Viktor + Andrio call
3. If strategic impact → Update roadmap, notify team

### 6.3 Date Slippage Protocol

**If a task will miss target date:**
1. Owner updates status to 🔄 AT RISK 48 hours before deadline
2. Owner proposes new date with justification
3. Viktor assesses downstream impact
4. If Phase 1 critical path slips → Andrio approves new timeline

---

## 7. Definition of Done

### For Code Tasks
- [ ] Code written per implementation brief
- [ ] Error handling implemented (every external call)
- [ ] Compiled with #property strict, zero warnings
- [ ] Tested on demo account (minimum 10 test cases)
- [ ] Code reviewed by Viktor (approved)
- [ ] Merged to main branch
- [ ] Deployed to live (if applicable)
- [ ] ROADMAP.md updated (status = ✅ DONE, date filled)

### For Documentation Tasks
- [ ] RFC written per template
- [ ] Technical review by 1+ team member
- [ ] Approved by Andrio (business) and Viktor (technical)
- [ ] Published to repo
- [ ] ROADMAP.md updated

### For Hiring Tasks
- [ ] Job description posted
- [ ] 3+ candidates interviewed
- [ ] Reference checks completed
- [ ] Offer accepted
- [ ] Start date confirmed
- [ ] ROADMAP.md updated

---

## 8. Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Can't hire MQ5 Specialist | Medium | High | Viktor implements solo (slower) | Andrio |
| TCM v2.3.0 has critical bug in live | Low | Critical | Rollback to v2.2.0 within 5 minutes | Andrio |
| GUS weights don't converge | Medium | Medium | Manual override + quant analysis | Quant |
| Vantage changes API/spread model | Low | High | Multi-broker support in Phase 3 | Viktor |
| Discord webhook stops working | Medium | Low | Fallback to CSV logging | MQ5 Specialist |
| Data loss (CSV corruption) | Low | High | Daily automated backups | DevOps |

---

## 9. Success Metrics (Project-Level)

| Metric | Target | Current | Review Date |
|--------|--------|---------|-------------|
| **TCM Uptime** | >99% | N/A (not live) | Weekly |
| **GUS Score Correlation** | Top factor >0.40 | N/A (no data) | After 500 trades |
| **Recovery Win Rate** | >55% | N/A (not built) | After 50 recoveries |
| **System Latency** | <100ms per tick | N/A | Phase 3 |
| **Team Velocity** | 80% of tasks on time | N/A | Weekly |

---

## 10. Immediate Actions (Next 48 Hours)

| Action | Owner | Deadline |
|--------|-------|----------|
| Confirm MQ5 Specialist hiring timeline | Andrio | 2026-03-21 |
| Pull TCM v2.3.0 on Windows, attempt compile | Andrio | 2026-03-21 |
| Create GitHub issue templates (bug, feature, roadmap-change) | Viktor | 2026-03-21 |
| Set up communication channel (Discord/Slack) | Andrio | 2026-03-21 |
| Write Quant Analyst hiring brief | Viktor | 2026-03-22 |
| Write ML Engineer hiring brief | Viktor | 2026-03-22 |

---

**This roadmap is a living document. It guides our work, not constrains it. Update it as reality changes.**

*Maintained by: Viktor Kozlov*  
*Next Review: 2026-03-27 (Monday)*
