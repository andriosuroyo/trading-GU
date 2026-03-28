#!/usr/bin/env python3
"""
Daily Analysis Runner - Execute all three QA daily analyses

Usage:
    python run-analysis.py              # Run for yesterday (default)
    python run-analysis.py 2026-03-27   # Run for specific date

This runs:
    1. qa_daily_recovery.py - RecoveryAnalysis
    2. qa_daily_time.py     - TimeAnalysis
    3. qa_daily_mae.py      - MAEAnalysis

Output files saved to data/:
    YYYYMMDD_RecoveryAnalysis.xlsx
    YYYYMMDD_TimeAnalysis.xlsx
    YYYYMMDD_MAEAnalysis.xlsx
"""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
import argparse


def get_yesterday():
    """Get yesterday's date in YYYY-MM-DD format."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def run_script(script_name, date_arg):
    """Run a Python script with the given date argument."""
    cmd = ['python', script_name]
    if date_arg:
        cmd.extend(['--date', date_arg])
    
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    if date_arg:
        print(f"Date: {date_arg}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n[ERROR] {script_name} failed with code {result.returncode}")
        return False
    
    print(f"\n[SUCCESS] {script_name} completed")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Run all three daily QA analyses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run-analysis.py              # Run for yesterday
    python run-analysis.py 2026-03-27   # Run for specific date
        """
    )
    parser.add_argument(
        'date',
        nargs='?',
        help='Date in YYYY-MM-DD format (default: yesterday)'
    )
    
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = args.date
        # Validate date format
        try:
            datetime.strptime(target_date, '%Y-%m-%d')
        except ValueError:
            print("[ERROR] Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = get_yesterday()
        print(f"No date provided - using yesterday: {target_date}")
    
    print("="*60)
    print("Daily Analysis Runner")
    print("="*60)
    print(f"Target Date: {target_date}")
    print(f"Start Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Scripts to run in order
    scripts = [
        ('qa_daily_recovery.py', 'RecoveryAnalysis'),
        ('qa_daily_time.py', 'TimeAnalysis'),
        ('qa_daily_mae.py', 'MAEAnalysis')
    ]
    
    success_count = 0
    
    for i, (script, name) in enumerate(scripts, 1):
        print(f"\n[{i}/{len(scripts)}] Starting {name}...")
        
        if run_script(script, target_date):
            success_count += 1
        else:
            print(f"\n[ABORT] Stopping due to failure in {name}")
            sys.exit(1)
    
    # Summary
    print("\n" + "="*60)
    print("RUN COMPLETE")
    print("="*60)
    print(f"Completed: {success_count}/{len(scripts)} analyses")
    print(f"End Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Output file locations
    file_date = target_date.replace('-', '')
    print("\nOutput Files:")
    print(f"  data/{file_date}_RecoveryAnalysis.xlsx")
    print(f"  data/{file_date}_TimeAnalysis.xlsx")
    print(f"  data/{file_date}_MAEAnalysis.xlsx")
    print("="*60)
    
    if success_count == len(scripts):
        print("\n[SUCCESS] All analyses completed successfully")
        sys.exit(0)
    else:
        print(f"\n[WARNING] Only {success_count}/{len(scripts)} analyses completed")
        sys.exit(1)


if __name__ == "__main__":
    main()
