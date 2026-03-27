# DEV/MAC Environment Synchronization Protocol

**Last Updated:** 260327  
**Purpose:** Ensure Git always mirrors DEV (Windows/MT5) environment while supporting MAC (macOS/no MT5) contributions

---

## Environment Definitions

| Environment | Platform | MT5 Access | Purpose |
|-------------|----------|------------|---------|
| **DEV** | Windows | ✅ Full | Development, compilation, testing, live trading |
| **MAC** | macOS | ❌ None | Planning, documentation, analysis scripts |

---

## Core Principle

```
Git Repository = Mirror of DEV Environment
                    ↑↓ Sync
MAC Environment = Contributes docs/scripts, pulls DEV updates
```

**Git is the single source of truth that keeps DEV and MAC synchronized.**

---

## File Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  DEV (Windows + MT5)                                        │
│  ───────────────────                                        │
│  Source of Truth for:                                       │
│  • Compiled EX5 files (not in Git - generated)              │
│  • Live test results                                        │
│  • MT5 data exports                                         │
│  • Setfile validation                                       │
└─────────────────────────────────────────────────────────────┘
                              ↑↓
                    ┌─────────────────┐
                    │   Git/GitHub    │
                    │  (Single Truth) │
                    └─────────────────┘
                              ↑↓
┌─────────────────────────────────────────────────────────────┐
│  MAC (macOS, no MT5)                                        │
│  ───────────────────                                        │
│  Contributes:                                               │
│  • Documentation updates                                    │
│  • Python analysis scripts (planning only)                  │
│  • Task coordination files (.agents/)                       │
│                                                             │
│  Never modifies:                                            │
│  • MQ5 source (can't compile)                               │
│  • Setfiles (can't validate)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Sync Rules

### Rule 1: Git Always Mirrors DEV

**DEV → Git:** Push all meaningful changes immediately
**Git → DEV:** Pull before starting work

**DEV Must Never Be Behind Git:**
```bash
# DEV workflow
git pull origin main     # Always start here
git add -A
git commit -m "[Coder] Compile: RGU v3.0 verified"
git push origin main     # Immediately push
```

### Rule 2: MAC Contributes, Then Syncs

**MAC → Git:** Push documentation/script changes
**Git → DEV:** DEV pulls MAC changes

**MAC Must Pull Before Push:**
```bash
# MAC workflow
git pull origin main     # Get latest DEV changes
git add -A
git commit -m "[PM] Docs: Updated knowledge_base"
git push origin main     # Push to share with DEV
```

### Rule 3: No Workarounds for Missing MT5

| On MAC | Action | Never Do |
|--------|--------|----------|
| Can't compile MQ5 | Document need, defer | Don't fake compilation |
| Can't test live | Write test plan, defer | Don't skip testing |
| Can't fetch ticks | Use cached data, note date | Don't use stale data silently |

---

## Conflict Resolution Priority

When DEV and MAC diverge:

1. **DEV wins on code/compilation issues**
   - DEV has ground truth (runs MT5)
   - MAC accepts DEV's compilation fixes

2. **MAC wins on documentation** (if accurate)
   - MAC has time to write detailed docs
   - DEV accepts documentation updates

3. **User decides on strategy conflicts**
   - PM escalates to User
   - Winner's version committed

---

## Git Status Checks

### DEV Check (Every Session)
```bash
git status
# Should show: "Your branch is up to date with 'origin/main'"
# Or: "Your branch is ahead" (unpushed commits)

# If "behind":
git pull origin main

# If "diverged":
git pull origin main --no-rebase
# Resolve conflicts (see GIT_WORKFLOW.md)
```

### MAC Check (Every Session)
```bash
git status
# Should show: "Your branch is up to date with 'origin/main'"

# If "behind":
git pull origin main
# Review DEV changes before pushing new work
```

---

## What Goes Into Git

### From DEV (Windows/MT5)
✅ MQ5 source files (.mq5)  
✅ Setfiles (.set) after validation  
✅ Test results and logs  
✅ Analysis outputs (FINAL versions)  
✅ Documentation updates  

❌ EX5 files (generated, use .gitignore)  
❌ Temporary CSV outputs  
❌ MT5 cache files  

### From MAC (macOS)
✅ Markdown documentation  
✅ Python scripts (analysis planning)  
✅ Task files (.agents/)  
✅ Configuration files  

❌ Never commit files requiring MT5 validation  
❌ Never modify MQ5 without DEV verification  

---

## Sync Checklist

### Before Switching Environments

**Leaving DEV:**
- [ ] Commit all changes
- [ ] Push to origin
- [ ] Verify `git status` clean

**Leaving MAC:**
- [ ] Commit documentation changes
- [ ] Push to origin
- [ ] Note any MT5-dependent work for DEV

### After Switching Environments

**Arriving at DEV:**
- [ ] `git pull origin main`
- [ ] Review MAC changes (documentation)
- [ ] Validate any setfile changes in MT5

**Arriving at MAC:**
- [ ] `git pull origin main`
- [ ] Review DEV changes (code, tests)
- [ ] Update documentation to reflect DEV state

---

## Emergency: Fixing Sync Issues

### DEV is Behind (Critical)
```bash
# On DEV
git fetch origin
git status

# If behind:
git pull origin main
# Review changes, test if needed
git push origin main
```

### MAC Can't Push (Behind)
```bash
# On MAC
git pull origin main
# Review DEV changes
# Resolve any conflicts
# Then push
```

### Complete Out-of-Sync (Nuclear)
```bash
# Save local work
cp -r project project_backup_$(date +%Y%m%d)

# Reset to remote
git fetch origin
git reset --hard origin/main

# Re-apply local changes manually
```

---

## Success Indicators

| Indicator | Good State | Bad State |
|-----------|-----------|-----------|
| `git status` | "up to date" or "ahead" | "behind" or "diverged" |
| `git log` | Shows recent commits from both environments | Only one environment's commits |
| File timestamps | DEV and MAC files intermixed | All files from one environment |
| Content | DEV has compiled EX5 (not in Git) | DEV missing MAC's doc updates |

---

## History
- 260327: Protocol created
