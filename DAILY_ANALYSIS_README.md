# Daily Analysis Runner

Automated execution of the three daily QA analyses required by TEAM_CHARTER.md Section 6.

## Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `qa_daily_recovery.py` | RecoveryAnalysis - Track loss baskets, evaluate multi-layer recovery | `{date}_RecoveryAnalysis.xlsx` |
| `qa_daily_time.py` | TimeAnalysis - Evaluate time-based SL (1-30 min) | `{date}_TimeAnalysis.xlsx` |
| `qa_daily_mae.py` | MAEAnalysis - Evaluate ATR-based SL (3x-30x) | `{date}_MAEAnalysis.xlsx` |

## Quick Start

### Run for Yesterday (Default)
```bash
# Python (cross-platform)
python run-analysis.py

# Windows Batch
run-analysis.bat

# PowerShell
.\run-analysis.ps1
```

### Run for Specific Date
```bash
# Python
python run-analysis.py 2026-03-27

# Windows Batch
run-analysis.bat 2026-03-27

# PowerShell
.\run-analysis.ps1 2026-03-27
```

## Output Location

All output files are saved to `data/` folder:
```
data/
├── 20260327_RecoveryAnalysis.xlsx
├── 20260327_TimeAnalysis.xlsx
└── 20260327_MAEAnalysis.xlsx
```

## Scheduling (08:00 UTC Daily)

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task: "Daily QA Analysis"
3. Trigger: Daily at 08:00 UTC
4. Action: Start a program
5. Program: `python`
6. Arguments: `run-analysis.py`
7. Start in: `C:\Trading_GU`

### Cron (Linux/Mac)
```bash
# Add to crontab (runs at 08:00 UTC daily)
0 8 * * * cd /path/to/Trading_GU && python run-analysis.py >> logs/daily_analysis.log 2>&1
```

## Requirements

- Python 3.8+
- MetaTrader5 terminal access (Windows)
- Vantage and BlackBull MT5 accounts configured in `.env`
- Required packages: `pandas`, `openpyxl`, `numpy`

## Error Handling

The runner stops immediately if any analysis fails:
- Exit code 0: All analyses successful
- Exit code 1: One or more analyses failed

Check console output for specific error details.

## Daily Workflow (TEAM_CHARTER.md Compliance)

```
08:00 UTC - Run analysis
    ↓
Check output files generated
    ↓
Review DailyLog.md for anomalies
    ↓
Escalate if needed (within 4 hours)
```

## Escalation Criteria

Escalate to PM immediately if:
- Recovery rate < 70%
- Any strategy shows negative P&L for 3+ days
- Optimal SL > 15 min in TimeAnalysis
- Data anomalies detected

## System Requirements

### NEW CommentTag-Based System (Current)
- Filters by `CommentTag` containing "GU_"
- Strategy identification: CommentTag (e.g., "GU_m1052005")
- Session derived from `OpenTime` timestamp
- Excel sheets named by strategy (not magic numbers)

### OLD System (Deprecated)
- ~~Magic number ranges (11-13, 21-23, 31-33)~~
- ~~Session from magic number encoding~~

## Support

See `.agents/QA/Persona.md` for QA responsibilities.
See `TEAM_CHARTER.md` Section 6 for daily deliverables specification.
