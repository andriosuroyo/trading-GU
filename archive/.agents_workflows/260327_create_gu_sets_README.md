# GU Set Creation Workflow

## Quick Start

```bash
# Create all standard active and test sets
python .agents/workflows/create_gu_sets.py

# Create single active set
python -c "from create_gu_sets import create_active_set; create_active_set(22)"

# Create single test set  
python -c "from create_gu_sets import create_test_set; create_test_set(115)"
```

## Magic Number Reference

### ACTIVE Sets (2-Digit)

| Magic | Strategy | Session | Filename |
|-------|----------|---------|----------|
| 10 | MH | Full-time | gu_mh_fulltime.set |
| 11 | MH | Asia | gu_mh_asia.set |
| 12 | MH | London | gu_mh_london.set |
| 13 | MH | NY | gu_mh_ny.set |
| 20 | HR05 | Full-time | gu_hr05_fulltime.set |
| 21 | HR05 | Asia | gu_hr05_asia.set |
| 22 | HR05 | London | gu_hr05_london.set |
| 23 | HR05 | NY | gu_hr05_ny.set |
| 30 | HR10 | Full-time | gu_hr10_fulltime.set |
| 31 | HR10 | Asia | gu_hr10_asia.set |
| 32 | HR10 | London | gu_hr10_london.set |
| 33 | HR10 | NY | gu_hr10_ny.set |

### TEST Sets (3-Digit)

| Magic | Comment | Filename |
|-------|---------|----------|
| 112 | GU_TEST_112 | gu_test_112.set |
| 115 | GU_TEST_115 | gu_test_115.set |

## Pattern Rules

- **First digit** = Strategy: 1=MH, 2=HR05, 3=HR10
- **Second digit** = Session: 0=Full-time, 1=Asia, 2=London, 3=NY
- **3-digit** = TEST set with comment GU_TEST_XXX

## Analysis Date Cutoff

- **Before March 12, 2026**: Group by CommentTag only (session-level)
- **March 12, 2026 onwards**: Can breakdown by Magic Number (strategy-level)
