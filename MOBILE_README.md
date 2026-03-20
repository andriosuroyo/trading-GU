# 🎯 Mobile Development Guide

> **Use this file first when working on macOS without MT5**

## What You Can Do Here (No MT5 Required)

- ✅ **Review architecture & settings** - Read PROJECT_SUMMARY.md
- ✅ **Plan features** - Edit TODO.md (create if needed)
- ✅ **Documentation** - Update any .md files
- ✅ **Analysis scripts** - Edit Python files (run on Windows later)
- ✅ **Strategy discussion** - Reference QUICK_REFERENCE.md
- ✅ **Setfile planning** - Review/edit .set files (text-based)

## What Requires MT5 (Do on Windows)

- ❌ **Compile MQ5** → Use MetaEditor on Windows
- ❌ **Live testing** → Run on Windows with MT5
- ❌ **Execute analysis** → Run Python on Windows with data

---

## 📂 Mobile-Optimized Structure

```
trading-GU/
├── 📄 MOBILE_README.md          ← You are here
├── 📄 PROJECT_SUMMARY.md         ← Start here for big picture
├── 📄 QUICK_REFERENCE.md         ← Quick lookup
│
├── 📁 Experts/                   ← Source code (read-only on Mac)
│   ├── TimeCutoffManager.mq5    ← Main EA (read, plan changes)
│   └── GUM/                     ← GU Manager EA
│
├── 📁 Setfiles/                  ← Configs (editable text files)
│   ├── Main/                    ← Active setfiles
│   └── archive/                 ← Old configs
│
├── 📁 analysis/                  ← Python scripts (edit, can't run)
│   └── *.py                     ← 66 analysis scripts
│
├── 📁 data/                      ← Scripts only (no CSVs)
│   └── *.py                     ← Data fetching scripts
│
├── 📄 TimeCutoffManager_Documentation_v2.md  ← Full manual
├── 📄 GU_Manager_Documentation.md           ← GU EA manual
└── 📄 knowledge_base.md                      ← Research notes
```

---

## 🔄 Mobile Workflow

### 1. Start Work Session
```bash
cd trading-GU
git pull origin main
```

### 2. Review Current State
```bash
# Read these in order:
cat MOBILE_README.md          # This file
cat PROJECT_SUMMARY.md         # Big picture
cat QUICK_REFERENCE.md         # Current settings
```

### 3. Plan Changes
```bash
# Create/edit TODO for planning
vim TODO.md

# Example TODO structure:
# ## Proposed Changes
# - [ ] Add breakeven protection before partial close
# - [ ] Test 70/30 split instead of 50/50
# - [ ] Create new setfile for London session v2
```

### 4. Document Ideas
```bash
# Edit any markdown file
vim PROJECT_SUMMARY.md
# - Update "Active Decisions" section
# - Add new questions to "Open Questions"
```

### 5. Review/Edit Setfiles
```bash
# Setfiles are plain text - editable on Mac
cat Setfiles/Main/gu_mh_asia.set

# Plan changes (apply on Windows MT5)
echo "MaxSpread=30" >> planned_changes.txt
```

### 6. Sync Changes
```bash
git add .
git commit -m "Mobile: Planning session updates"
git push origin main
```

---

## 📱 Mobile-Friendly Files

### Essential Reading (Start Here)
| File | Size | Purpose |
|------|------|---------|
| `MOBILE_README.md` | ~3 KB | This guide |
| `PROJECT_SUMMARY.md` | ~7 KB | Architecture, settings, decisions |
| `QUICK_REFERENCE.md` | ~1 KB | Pocket reference |

### Full Documentation
| File | Size | Content |
|------|------|---------|
| `TimeCutoffManager_Documentation_v2.md` | ~12 KB | Complete TCM manual |
| `TCM_PreLive_Testing_Guide.md` | ~12 KB | Testing procedures |
| `TCM_Test_Checklist.md` | ~8 KB | Validation checklist |
| `GU_Manager_Documentation.md` | ~15 KB | GU EA manual |

---

## 📝 Common Mobile Tasks

### Review TCM Settings
```bash
# Quick grep for current inputs
grep "^input" Experts/TimeCutoffManager.mq5 | head -20
```

### Check Recent Changes
```bash
# See git history
git log --oneline -10

# See what changed in last commit
git show --stat HEAD
```

### Plan Setfile Changes
```bash
# Compare two setfiles
diff Setfiles/Main/gu_mh_asia.set Setfiles/Main/gu_mh_london.set

# List all Asia configs
ls -la Setfiles/Main/*asia*
```

### Draft Documentation
```bash
# Create new idea document
vim IDEAS.md

# Or update existing
vim PROJECT_SUMMARY.md
```

---

## ⚡ Quick Commands Cheat Sheet

```bash
# Sync
git pull origin main          # Get latest
git push origin main          # Send changes

# Search
grep -r "partial close" *.md  # Find mentions
grep "InpPartial" *.mq5       # Find in code

# Review
cat PROJECT_SUMMARY.md        # Big picture
head -100 *.mq5               # Code preview
wc -l analysis/*.py           # Script count
```

---

## 🔗 Links

- **GitHub:** https://github.com/andriosuroyo/trading-GU.git
- **Windows MT5 Path:** `C:\Program Files\MetaTrader 5\terminal64.exe`
- **Recovery CSV:** (on Windows) `MQL5/Files/loss_recovery.csv`

---

## ✅ Pre-Flight Checklist (Before Windows Session)

Before switching to Windows with MT5:

- [ ] `git pull origin main` - Get any Windows changes
- [ ] Review `PROJECT_SUMMARY.md` - Refresh on current state
- [ ] Check `TODO.md` - What needs to be implemented?
- [ ] Read `QUICK_REFERENCE.md` - Current config at a glance
- [ ] Plan changes - Know what to test before opening MT5

---

**Remember:** This repository is optimized for your workflow:
- **Mac:** Planning, documentation, discussion, code review
- **Windows:** Implementation, compilation, testing, live trading

*Start every mobile session by reading PROJECT_SUMMARY.md*
