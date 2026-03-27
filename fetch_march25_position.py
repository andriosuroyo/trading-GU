"""Fetch specific March 25 position - BUY opened at 15:27, closed at 15:37"""
import subprocess
import json
from datetime import datetime

# Fetch all positions using the terminal
result = subprocess.run(
    ['python', 'gu_tools.py', 'list', '2026-03-25'],
    capture_output=True, text=True, timeout=120
)

print("Raw output from gu_tools:")
print(result.stdout[:2000])
print("\n" + "="*80)
print("Looking for position opened at 15:27...")

# Let's also try to get detailed info from MT5 directly
# The position should be around 15:27 open, 15:37 close (10 min duration), slight loss
# Looking for BUY positions with ~10 min duration and small negative P&L
