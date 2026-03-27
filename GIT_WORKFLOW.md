# Git Workflow & Management Guide

**Last Updated:** 260327  
**Applies to:** PM, QA, Coder, MLE  
**Purpose:** Bulletproof Git management for Trading_GU project

---

## Repository Overview

```
GitHub: https://github.com/andriosuroyo/trading-GU.git
Local: c:\Trading_GU (Windows) or ~/Trading_GU (macOS)
Branch: main
```

---

## Two-Environment Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  MOBILE ENVIRONMENT (macOS, no MT5)                         │
│  ─────────────────────────────────                          │
│  Work: Documentation, planning, Python scripts (no run)     │
│  Git: Frequent commits, push to sync                        │
│  Pull: Before every session to get Windows changes          │
└─────────────────────────────────────────────────────────────┘
                              ↕ Sync via GitHub
┌─────────────────────────────────────────────────────────────┐
│  WINDOWS ENVIRONMENT (Windows, with MT5)                    │
│  ─────────────────────────────────                          │
│  Work: Compile MQ5, run tests, live trading                 │
│  Git: Commit after each significant change                  │
│  Pull: Before starting work to get mobile changes           │
└─────────────────────────────────────────────────────────────┘
```

---

## File Categories & Git Handling

### Category 1: Source Code (TRACK)
| File Type | Location | Example |
|-----------|----------|---------|
| MQ5 Source | `Experts/` | `RGU_EA.mq5`, `TimeCutoffManager.mq5` |
| Python Scripts | Root, `analysis/`, `tick_data/` | `qa_daily_recovery.py` |
| Setfiles | `Setfiles/` | `gu_m1052005.set` |
| Documentation | Root, `.agents/` | `knowledge_base.md`, `TEAM_CHARTER.md` |
| Config | Root | `.gitignore` |

**Rule:** Always commit source code changes immediately.

---

### Category 2: Generated Outputs (IGNORE)
| File Type | Pattern | Reason |
|-----------|---------|--------|
| Compiled EX5 | `*.ex5` | Generated from MQ5 |
| Excel Lock Files | `~$*.xlsx` | Temporary Office files |
| CSV Analysis Outputs | `*.csv` in root | Generated data (too large) |
| Recovery Logs | `recovery_*.csv` | Runtime generated |
| Parquet Files | `*.parquet` | Binary data files |

**Rule:** These are in `.gitignore`, never commit.

---

### Category 3: Reference Data (TRACK SELECTIVELY)
| File Type | Location | Rule |
|-----------|----------|------|
| Analysis Excel | `data/*.xlsx` | Commit FINAL versions only |
| Recovery Analysis | `data/*RecoveryAnalysis*.xlsx` | Commit FINAL, ignore drafts |
| Position History | `data/position_history_*.csv` | Commit cleaned versions |

**Rule:** Commit reference data used by multiple staff. Ignore temporary/draft files.

---

## Mobile (macOS) Git Protocol

### Before Every Session
```bash
# 1. Pull latest changes from Windows/Other devices
git pull origin main

# 2. Review what changed
git log --oneline -5

# 3. Check status
git status
```

### During Session
```bash
# Commit frequently (after each significant change)
git add <file>
git commit -m "[Role] [Type]: Brief description"

# Examples:
git commit -m "[PM] Docs: Updated knowledge_base with new magic system"
git commit -m "[QA] Analysis: Added MAE calculation to daily script"
git commit -m "[Coder] Fix: Resolved compilation warning in RGU"
```

### End of Session
```bash
# Push all commits
git push origin main

# Verify sync
git status  # Should show "Your branch is up to date"
```

---

## Windows (MT5) Git Protocol

### Before Every Session
```bash
# Pull latest mobile changes
git pull origin main

# Review any documentation updates
# Check .agents/ for new tasks
```

### During Session
```bash
# After compilation success
git add Experts/RGU_EA.mq5
git commit -m "[Coder] Compile: RGU v3.0 compiles with 0 warnings"

# After setfile changes
git add Setfiles/RGU/RGU_Test_v3.set
git commit -m "[Coder] Config: Created RGU test setfile"

# After live testing
git add -A
git commit -m "[PM] Test: RGU Strategy Tester results for 5 scenarios"
```

### End of Session
```bash
# Push all changes
git push origin main

# Notify if critical changes made
# (Update .agents/ files if tasks completed)
```

---

## Commit Message Format

### Template
```
[Role] [Type]: Brief description (50 chars or less)

[Optional longer description if needed]
```

### Roles
- `[PM]` — Project Manager
- `[QA]` — Quantitative Analyst  
- `[Coder]` — MQ5/MQL5 Specialist
- `[MLE]` — Machine Learning Engineer
- `[User]` — You (the project owner)

### Types
| Type | Use For |
|------|---------|
| `Docs` | Documentation changes |
| `Feat` | New feature/script |
| `Fix` | Bug fix |
| `Config` | Setfile/configuration changes |
| `Refactor` | Code restructuring |
| `Analysis` | Analysis script/output |
| `Compile` | Compilation/Build |
| `Test` | Testing results |
| `Archive` | File archival/cleanup |

### Examples
```bash
[PM] Docs: Updated TEAM_CHARTER with Git workflow
[QA] Feat: Created qa_daily_recovery.py script
[QA] Analysis: Added March 27 RecoveryAnalysis FINAL
[Coder] Fix: Resolved DEAL_PRICE_CLOSE error in RGU
[Coder] Compile: TCM v2.2 verified 0 warnings
[MLE] Feat: Initial feature engineering notebook
[PM] Archive: Moved deprecated scripts to archive/
```

---

## Handling Merge Conflicts

### Prevention
```bash
# Always pull before starting work
git pull origin main

# Commit and push frequently (smaller changes = fewer conflicts)
```

### If Conflict Occurs
```bash
# 1. See what's conflicting
git status

# 2. Open conflicting files in editor
# Look for <<<<<<< HEAD markers

# 3. Resolve conflicts (keep correct version)

# 4. Mark as resolved
git add <resolved-file>

# 5. Complete merge
git commit -m "[PM] Merge: Resolved conflict in PROJECT_SUMMARY.md"
```

### Common Conflict Scenarios

| Scenario | Resolution |
|----------|------------|
| Both edited same documentation | Use latest version, incorporate both changes |
| Coder compiled EX5, mobile edited MQ5 | Keep both (EX5 is generated, MQ5 is source) |
| QA committed analysis, PM committed summary | Merge content, ensure consistency |

---

## What NOT to Commit

### Already in .gitignore
```gitignore
# Generated files
*.ex5
*.csv
*.parquet
~$*.xlsx

# Temporary files
__pycache__/
*.pyc
*.tmp

# Large data
*.zip
*.tar.gz
tick_data/*.csv
data/*.csv
```

### Never Commit
- Live trading account credentials
- API keys
- Personal MT5 settings
- Large binary files (>10MB)

---

## Mobile-Specific Guidelines

### What You CAN Commit from Mobile
✅ Markdown documentation  
✅ Python scripts (analysis, planning)  
✅ Setfiles (text-based config)  
✅ Task files in `.agents/`  

### What You CANNOT Commit from Mobile
❌ Compiled EX5 files (need Windows/MT5)  
❌ Live test results (need Windows/MT5)  
❌ Excel lock files (`~$*.xlsx`)  

### Mobile Workflow Best Practice
```bash
# Start session
git pull origin main

# Work on documentation/scripts
vim knowledge_base.md
vim qa_script.py

# Commit frequently
git commit -am "[PM] Docs: Updated strategy parameters"

# End session
git push origin main
# (Windows will pull these changes)
```

---

## Windows-Specific Guidelines

### What You CAN Commit from Windows
✅ Everything from mobile list  
✅ Compiled EX5 files (wait — these are in .gitignore!)  
✅ MQ5 source changes  
✅ Test results and logs  
✅ Live trading data exports  

### Actually, EX5 Files
EX5 files are **generated** from MQ5 source. They are in `.gitignore` because:
1. They can be regenerated from source
2. They are binary and cause merge conflicts
3. Different MT5 builds may create different EX5

**Rule:** Only commit MQ5 source, never EX5.

---

## Emergency Procedures

### Accidentally Committed Wrong File
```bash
# Remove from last commit (if not pushed)
git reset --soft HEAD~1
git restore --staged <wrong-file>
git commit -c ORIG_HEAD

# If already pushed
git revert <commit-hash>
```

### Lost Local Changes
```bash
# Check reflog for recovery
git reflog

# Restore from specific point
git checkout <commit-hash> -- <file>
```

### Complete Reset (Nuclear Option)
```bash
# Save local changes first
cp -r Trading_GU Trading_GU_backup

# Reset to remote
git fetch origin
git reset --hard origin/main
```

---

## Sync Checklist

### Before Switching Devices
- [ ] Commit all changes
- [ ] Push to origin
- [ ] Verify `git status` is clean

### After Switching Devices
- [ ] Pull latest changes
- [ ] Review `git log` for what changed
- [ ] Continue work

---

## Git Status Quick Reference

| Status | Meaning | Action |
|--------|---------|--------|
| `Changes not staged` | Modified but not committed | `git add` then `git commit` |
| `Changes to be committed` | Staged, ready to commit | `git commit` |
| `Untracked files` | New files not in git | `git add` to track, or add to `.gitignore` |
| `Your branch is ahead` | Local commits not pushed | `git push origin main` |
| `Your branch is behind` | Remote has commits you don't have | `git pull origin main` |
| `Your branch has diverged` | Both local and remote have changes | `git pull` then resolve conflicts |

---

## History
- 260327: Git workflow created
