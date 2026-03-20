#!/usr/bin/env python3
"""
Trading_GU Folder Organization Script

This script organizes the 100+ files in the Trading_GU root directory
into logical subfolders for better maintainability.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Define the organization structure
FOLDERS = {
    "analysis": {
        "description": "Data analysis, simulation, and comparison scripts",
        "patterns": [
            "*_analysis.py",
            "*_simulation.py",
            "compare_*.py",
            "multi_*.py",
            "*_comparison.py",
            "explore_*.py",
            "investigate_*.py",
            "trace_*.py",
            "*_corrected.py",
            "*_results.csv",
            "*_summary.csv",
            "*_detailed.csv",
        ],
        "files": [
            "analyze_london.py",
            "analyze_tp80.py",
            "asia_first_positions_analysis.py",
            "compare_sessions.py",
            "investigate_spike.py",
            "mfe_analysis_corrected.py",
            "time_exit_simulation.py",
            "trace_outlier.py",
            "asia_mfe_mae_analysis.csv",
            "asia_mfe_mae_correct.csv",
            "asia_simulation1_time_exit.csv",
            "asia_simulation2_target_profit.csv",
            "asia_target_profit_simulation.csv",
            "asia_time_exit_simulation.csv",
            "atr_simulation.py",
            "candle_close_analysis.py",
            "candle_tp_simulation.csv",
            "candle_tp_simulation.py",
            "capture_analysis_results.csv",
            "check_durations.py",
            "check_scale.py",
            "comprehensive_simulation.py",
            "daily_performance_table.py",
            "debug_prices.py",
            "duration_analysis_corrected.py",
            "duration_cap_results_table.md",
            "duration_simulation_table.py",
            "final_best_pnl_recommendations.py",
            "final_comparison.py",
            "final_recommendation.py",
            "final_summary_all_sessions.py",
            "granular_tp_analysis.py",
            "high_win_rate_config.py",
            "latest_analysis_best_pnl.py",
            "loss_analysis.py",
            "low_tp_simulation.py",
            "mfe_mae_analysis.py",
            "mfe_mae_correct.py",
            "mfe_mae_corrected_points.py",
            "mfe_mae_points.py",
            "multi_tp_candle_close.py",
            "multi_tp_candle_close_results.csv",
            "multi_tp_corrected.py",
            "multi_tp_corrected_results.csv",
            "multi_tp_simulation.csv",
            "multi_tp_simulation.py",
            "performance_analysis.py",
            "proposed_settings_analysis.py",
            "show_results.py",
            "simulate_proposed_settings.py",
            "simulate_trail_equal.py",
            "test_tick_precision.py",
            "tick_data_check.py",
            "tick_verification.py",
            "time_analysis_results.csv",
            "time_cutoff_comparison.csv",
            "time_cutoff_comparison.py",
            "time_exit_candle_results.csv",
            "time_exit_candle_sim.py",
            "time_exit_sim_fast.py",
            "time_exit_simulation_detailed.csv",
            "time_exit_simulation_final.py",
            "time_exit_simulation_results.csv",
            "time_exit_simulation_summary.csv",
            "time_exit_simulation_tp20.csv",
            "timed_exit_pro_recommendations.md",
            "tp_analysis_fixed.py",
            "tp_analysis_results.csv",
            "tp_breakdown.py",
            "tp_full_table.py",
            "trade_duration_analysis.py",
            "trailing_stop_recommendations.py",
            "trailing_stop_simulation.csv",
            "trailing_stop_simulation.py",
            "vantage_analysis.py",
            "verify_asia_analysis.py",
            "verify_miss_pnl.py",
            "verify_ny_change.py",
            "verify_one_position.py",
            "verify_real_data.py",
        ]
    },
    "tick_data": {
        "description": "Tick data storage and processing",
        "patterns": [],
        "files": [
            "run_tick_collection.bat",
            "tick_storage_manager.py",
            "check_tick_history.py",
            "compare_exit_methods.py",
            "analyze_durations.py",
            "explore_all_cutoffs.py",
            "compare_cutoff_times.py",
        ]
    },
    "data": {
        "description": "Static datasets and reference data",
        "patterns": [],
        "files": [
            "utc_history.csv",
            "magic_report_output.json",
            "magic_report.txt",
            "fetch_bb_history.py",
            "fetch_magic_performance.py",
            "fetch_magic_report.py",
        ]
    },
    "archive": {
        "description": "Older/legacy scripts (keep for reference)",
        "patterns": [],
        "files": [
            "conversation_log.md",
        ]
    },
    "references": {
        "description": "Documentation and reference materials",
        "patterns": ["*.docx", "*.md"],
        "files": [
            "Blahtech Supply Demand.docx",
            "walkthrough.md",
            "summary.md",
            "timed_exit_pro_recommendations.md",
            "duration_cap_results_table.md",
        ]
    }
}

# Files to keep in root (core utilities)
KEEP_IN_ROOT = [
    "gu_tools.py",
    "knowledge_base.md",
    "README.md",
    ".env",
    "organize_trading_gu.py",
]


def get_all_files(directory):
    """Get all files in directory, excluding folders and special files."""
    files = []
    for item in os.listdir(directory):
        if item.startswith('.') or item.startswith('__'):
            continue
        full_path = os.path.join(directory, item)
        if os.path.isfile(full_path):
            files.append(item)
    return files


def organize_files(dry_run=True):
    """Organize files into folders."""
    base_dir = Path.cwd()
    all_files = get_all_files(base_dir)
    
    print("=" * 80)
    print("TRADING_GU FOLDER ORGANIZATION")
    print("=" * 80)
    print(f"\nTotal files in root: {len(all_files)}")
    print(f"Mode: {'DRY RUN (no changes made)' if dry_run else 'EXECUTING'}")
    print()
    
    # Track file assignments
    assignments = {}
    moved_count = 0
    keep_count = 0
    unassigned = set(all_files)
    
    # Create folders and assign files
    for folder_name, config in FOLDERS.items():
        folder_path = base_dir / folder_name
        
        if not dry_run:
            folder_path.mkdir(exist_ok=True)
        
        assigned_to_folder = []
        
        for filename in all_files:
            if filename in config["files"]:
                assigned_to_folder.append(filename)
                unassigned.discard(filename)
        
        if assigned_to_folder:
            print(f"\n[FOLDER] {folder_name}/ ({config['description']})")
            for f in sorted(assigned_to_folder):
                print(f"   -> {f}")
                if not dry_run:
                    src = base_dir / f
                    dst = folder_path / f
                    if src.exists():
                        shutil.move(str(src), str(dst))
            moved_count += len(assigned_to_folder)
    
    # Check files to keep in root
    print(f"\n[ROOT] KEEP IN ROOT (core utilities)")
    for f in KEEP_IN_ROOT:
        if f in unassigned:
            print(f"   [OK] {f}")
            unassigned.discard(f)
            keep_count += 1
    
    # Handle unassigned files
    if unassigned:
        print(f"\n[!] UNASSIGNED FILES ({len(unassigned)} files)")
        print("   These files need manual review:")
        for f in sorted(unassigned):
            print(f"   [?] {f}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files to move: {moved_count}")
    print(f"Files to keep: {keep_count}")
    print(f"Unassigned: {len(unassigned)}")
    print()
    
    if dry_run:
        print("This was a dry run. No files were moved.")
        print("To execute the organization, run: python organize_trading_gu.py --execute")
    else:
        print("[DONE] Organization complete!")
        
        # Create organization README
        readme_path = base_dir / "ORGANIZATION_README.md"
        with open(readme_path, 'w') as f:
            f.write(f"""# Trading_GU Folder Organization

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Folder Structure

""")
            for folder_name, config in FOLDERS.items():
                f.write(f"### {folder_name}/\n")
                f.write(f"{config['description']}\n\n")
        
        print(f"Created {readme_path}")
    
    return moved_count, keep_count, len(unassigned)


if __name__ == "__main__":
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    try:
        organize_files(dry_run=dry_run)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
