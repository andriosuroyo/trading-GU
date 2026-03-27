---
description: Generates a daily performance report for GU sets
---

This workflow analyzes the previous calendar day's MT5 trading data for all GU magic numbers (282603xx).
It groups performance by strategy and session, identifies anomalies, and produces a summary artifact.

## 1. Create Daily Report Script

1. Review and execute the python script below to fetch and format the data.
2. The script will output raw markdown formatted results.

// turbo-all
```bash
python c:\Trading_GU\.agents\scripts\generate_daily_report.py
```

## 2. Generate Quant Analysis

1. Read the output of the Python script and evaluate the numbers.
2. Formulate your "Quant's Take":
   - Compare strategy expected win rates to actuals.
   - Look for specific anomalies (e.g., tight SL being hit systematically, unexpected high number of trades).
   - Provide concrete recommendations to the user (e.g., "Consider widening TESTS NY SL to 200 pts" or "HR10 ASIA is performing exactly to spec, no changes").
3. Create a clean artifact file named `daily_report_<YYYY-MM-DD>.md` containing both the data tables and your Quant's Take. Use the `write_to_file` tool to create this artifact in the artifacts directory.

## 3. Present to User
Notify the user that the daily report is ready using the `notify_user` tool with the path to the generated artifact.
