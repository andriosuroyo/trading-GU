"""Final report on tick data state"""
import pandas as pd
import os
from pathlib import Path

print("=" * 80)
print("FINAL TICK DATA STATE - MARCH 13-20, 2026")
print("=" * 80)
print(f"{'Date':<12} {'Ticks':>12} {'Size (MB)':>12} {'Status':<30}")
print("-" * 80)

storage_dir = Path(__file__).parent
files = sorted(storage_dir.glob("ticks_*.parquet"))

total_ticks = 0
total_size = 0

for f in files:
    df = pd.read_parquet(f)
    size_mb = f.stat().st_size / 1024 / 1024
    total_ticks += len(df)
    total_size += size_mb
    
    date_str = f.stem.replace("ticks_", "")
    
    # Determine status
    if date_str in ["20260316", "20260320"]:
        status = "New from Vantage (limited fidelity)"
    else:
        status = "Backup restored (high fidelity)"
    
    print(f"{date_str:<12} {len(df):>12,} {size_mb:>12.2f} {status:<30}")

print("-" * 80)
print(f"{'TOTAL':<12} {total_ticks:>12,} {total_size:>12.2f}")
print("=" * 80)

print("\nNOTES:")
print("- Mar 16 & 20: Use new data (backup was incomplete anyway)")
print("- Mar 13, 17, 18, 19: Use restored backups (10x higher fidelity)")
print("- Backup folder contains all original files for safety")
