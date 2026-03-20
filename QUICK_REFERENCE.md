# TCM Quick Reference Card

## Current Config (v2.2)
```
Filter:    Magic = 11,12,13
Partial:   1 min @ 50%
Final:     2 min @ 100%
Spread:    Max 500 pts
```

## Partial Close Behavior
- **0.10 lot** → 0.05 @ 1min, 0.05 @ 2min ✓ Balanced
- **0.03 lot** → 0.02 @ 1min, 0.01 @ 2min ⚠️ Uneven
- **0.01 lot** → No partial (below min), full close @ 2min

## Key Inputs
| Input | Value | Purpose |
|-------|-------|---------|
| `InpUsePartialClose` | true | Master switch |
| `InpPartialCloseDuration` | 1 | Mid-time |
| `InpPartialClosePct` | 50 | % to close |
| `InpCloseDuration` | 2 | Final time |
| `InpMaxSpreadPoints` | 500 | Spread filter |

## File Locations
- **TCM Code:** `Experts/TimeCutoffManager.mq5`
- **Docs:** `TimeCutoffManager_Documentation_v2.md`
- **Setfiles:** `Setfiles/Main/`
- **Git:** https://github.com/andriosuroyo/trading-GU.git

## Mobile Workflow
```bash
# Pull latest
git pull origin main

# Edit docs/analysis
# ... make changes ...

# Push updates
git add .
git commit -m "Update"
git push origin main
```

## Dashboard Colors
| Color | Meaning |
|-------|---------|
| White | Normal |
| Yellow | Warning (< 10s) |
| Red | Critical (< 5s) |
| DodgerBlue | Partial close done |
| Aqua | Trailing mode |
| Orange | Closing in progress |

*Keep this on your phone for quick reference.*
