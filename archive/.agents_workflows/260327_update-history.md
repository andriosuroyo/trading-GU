---
description: Automatically fetches the latest closed GU trades (magic 282603xx) from MT5, formats them with strict UTC timestamps, appends DST context data, and merges them into `utc_history.csv`.
---

# Workflow: `/update-history`

When the user types `/update-history`, execute this workflow to dynamically sync the local analytical ground truth dataset `utc_history.csv` with the live broker history.

## 1. Execute the Update Script

// turbo-all
Run the dedicated python script to fetch, map, and merge the new closed GU positions:
```bash
python c:\Trading_GU\.agents\scripts\update_utc_history.py
```

## 2. Notify the User
Once the script completes, inform the user that `utc_history.csv` has been successfully updated with the newest closed positions. Remind them that all analytical operations requested should now run directly off `utc_history.csv` using absolute UTC values (ignoring the visual timezone of the MT5 software).
