#!/usr/bin/env python3
"""
GU Set Creation Workflow
Generates MT5 setfiles following the established magic number and naming conventions.

Magic Number Pattern:
- First digit: Strategy (1=MH, 2=HR10, 3=HR05)
- Second digit: Session (0=Full-time, 1=Asia, 2=London, 3=NY)
- TEST sets: 3-digit (110, 111, 112, 113, 115...)

Comment Format:
- Active: GU_ASIA, GU_LONDON, GU_NEWYORK
- TEST: GU_TEST_XXX (where XXX is the 3-digit magic number)

Output Structure:
- Setfiles are saved in a date-stamped folder: Setfiles/YYYYMMDD/

Reference Files:
- Uses files from Setfiles/YYYYMMDD/Reference/ as templates
- Copies all parameters, modifying only magic, comment, and strategy-specific settings
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

_output_dir = None
_reference_dir = None

def get_output_dir() -> Path:
    """Get the output directory for setfiles."""
    global _output_dir
    if _output_dir is None:
        date_str = datetime.now().strftime('%Y%m%d')
        setfiles_base = Path(r"c:\Trading_GU\Setfiles")
        _output_dir = setfiles_base / date_str
        _output_dir.mkdir(parents=True, exist_ok=True)
    return _output_dir

def get_reference_dir() -> Path:
    """Get the reference directory containing template setfiles."""
    global _reference_dir
    if _reference_dir is None:
        _reference_dir = get_output_dir() / "Reference"
    return _reference_dir

def get_strategy_name(first_digit: int) -> str:
    """Get strategy name from first digit."""
    strategies = {1: "MH", 2: "HR10", 3: "HR05"}
    return strategies.get(first_digit, "UNKNOWN")

def get_session_name(second_digit: int) -> str:
    """Get session name from second digit."""
    sessions = {0: "Full", 1: "Asia", 2: "London", 3: "NY"}
    return sessions.get(second_digit, "UNKNOWN")

def get_comment_tag(second_digit: int, is_test: bool = False, magic: int = None) -> str:
    """Get comment tag based on session and type."""
    if is_test:
        return f"GU_TEST_{magic}"
    tags = {0: "GU_FULLTIME", 1: "GU_ASIA", 2: "GU_LONDON", 3: "GU_NEWYORK"}
    return tags.get(second_digit, "GU_UNKNOWN")

def read_setfile(filepath: Path) -> str:
    """Read a setfile and return content as string."""
    with open(filepath, 'rb') as f:
        raw = f.read()
    try:
        content = raw.decode('utf-16-le')
    except:
        content = raw.decode('utf-8', errors='ignore')
    if content.startswith('\ufeff'):
        content = content[1:]
    return content

def get_start_two_mode(strategy: str) -> str:
    """Get StartTwoMode based on strategy."""
    # MH = 2, HR05/HR10 = 3, TEST = 3
    if strategy == "MH":
        return "2"
    return "3"  # HR05, HR10, TEST all use 3

def get_initial_lots(session: str, is_test: bool = False) -> str:
    """Get initial lots based on session and type."""
    if is_test:
        return "0.01"  # Test sets
    if session == "Full":
        return "0.02"  # Full-time sets
    return "0.10"  # Session sets (Asia, London, NY)

def find_gu_reference(strategy: str, session: str) -> Path:
    """Find the best GU reference file."""
    ref_dir = get_reference_dir()
    session_lower = session.lower().replace("-", "_")
    
    # Try exact match first
    candidates = [
        ref_dir / f"gu_{strategy}_{session_lower}.set",
        ref_dir / f"gu_{strategy}_{session_lower.replace('_', '')}.set",
    ]
    
    # Try strategy-specific fallbacks
    if strategy == "MH":
        candidates.append(ref_dir / "gu_mh_asia.set")
    elif strategy == "HR05":
        candidates.append(ref_dir / "gu_hr05_asia.set")
    elif strategy == "HR10":
        candidates.append(ref_dir / "gu_hr10_asia.set")
    
    # Ultimate fallback
    candidates.append(ref_dir / "gu_mh_asia.set")
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    return None

def find_sl_reference(session: str) -> Path:
    """Find SL reference file for a session."""
    ref_dir = get_reference_dir()
    session_lower = session.lower().replace("-", "").replace("newyork", "newyork")
    
    candidates = [
        ref_dir / f"sl_{session_lower}.set",
        ref_dir / f"sl_{session_lower.replace('newyork', 'newyork')}.set",
        ref_dir / "sl_asia.set",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    return None

def create_gu_setfile(magic: int, comment: str, strategy: str, session: str, is_test: bool = False) -> str:
    """Create a GU setfile using reference as template."""
    output_dir = get_output_dir()
    
    # Determine filename
    magic_str = str(magic)
    if is_test:
        filename = f"gu_test_{magic}.set"
    else:
        session_file = session.lower().replace("-", "_")
        filename = f"gu_{strategy.lower()}_{session_file}.set"
    
    filepath = output_dir / filename
    
    # Find reference file
    ref_path = find_gu_reference(strategy, session)
    if not ref_path:
        raise FileNotFoundError(f"No reference file found for {strategy} {session}")
    
    ref_content = read_setfile(ref_path)
    
    # Parse and modify parameters
    lines = ref_content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    modifications = {
        'InpMagicNumber': str(magic),
        'InpCommentTag': comment,
        'InpStartOpenTwo': 'false',  # Always false
        'InpStartTwoMode': get_start_two_mode(strategy),
        'InpInitialLots': get_initial_lots(session, is_test),
    }
    
    # For full-time sets, adjust trading hours
    if len(magic_str) == 2 and magic_str[1] == '0':
        modifications['InpUseTradingHours'] = 'false'
        modifications['InpStartHour'] = '0'
        modifications['InpEndHour'] = '23'
    
    # Process lines
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        if '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in modifications:
                new_lines.append(f"{key}={modifications[key]}")
            else:
                new_lines.append(stripped)
        else:
            new_lines.append(stripped)
    
    content = '\n'.join(new_lines) + '\n'
    filepath.write_text(content, encoding='utf-16')
    
    return str(filepath)

def create_sl_setfile(session_code: str, session_name: str, comment: str) -> str:
    """Create an SL setfile using reference as template."""
    output_dir = get_output_dir()
    
    # Simple naming: sl_asia.set, sl_london.set, sl_newyork.set
    session_file = session_name.lower().replace("-", "").replace("ny", "newyork")
    if session_file == "newyork":
        session_file = "newyork"
    
    filename = f"sl_{session_file}.set"
    filepath = output_dir / filename
    
    # Find reference
    ref_path = find_sl_reference(session_name)
    if not ref_path:
        raise FileNotFoundError(f"No SL reference file found for {session_name}")
    
    ref_content = read_setfile(ref_path)
    lines = ref_content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    # Modify parameters
    modifications = {
        'comment_to_include': comment,
        'magic_number_to_include': '',  # Keep blank, use comments only
    }
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        if '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in modifications:
                new_lines.append(f"{key}={modifications[key]}")
            else:
                new_lines.append(stripped)
        else:
            new_lines.append(stripped)
    
    content = '\n'.join(new_lines) + '\n'
    filepath.write_text(content, encoding='utf-16')
    
    return str(filepath)

def create_active_set(magic: int) -> str:
    """Create an ACTIVE setfile (2-digit magic number)."""
    if magic < 10 or magic > 99:
        raise ValueError(f"Active sets must use 2-digit magic numbers. Got: {magic}")
    
    magic_str = str(magic)
    first_digit = int(magic_str[0])
    second_digit = int(magic_str[1])
    
    strategy = get_strategy_name(first_digit)
    session = get_session_name(second_digit)
    comment = get_comment_tag(second_digit)
    
    result_path = create_gu_setfile(magic, comment, strategy, session, is_test=False)
    
    print(f"Created ACTIVE set: {Path(result_path).name}")
    print(f"  Strategy: {strategy} (Mode: {get_start_two_mode(strategy)})")
    print(f"  Session: {session}")
    print(f"  Magic: {magic}")
    print(f"  Comment: {comment}")
    
    return result_path

def create_test_set(magic: int) -> str:
    """Create a TEST setfile (3-digit magic number)."""
    if magic < 100 or magic > 999:
        raise ValueError(f"TEST sets must use 3-digit magic numbers. Got: {magic}")
    
    comment = f"GU_TEST_{magic}"
    
    # TEST sets use StartTwoMode=3
    result_path = create_gu_setfile(magic, comment, "TEST", "Test", is_test=True)
    
    print(f"Created TEST set: {Path(result_path).name}")
    print(f"  Magic: {magic}")
    print(f"  Comment: {comment}")
    
    return result_path

def create_sl_set(session_code: str, session_name: str, comment: str) -> str:
    """Create an SL setfile for a session."""
    result_path = create_sl_setfile(session_code, session_name, comment)
    
    print(f"Created SL set: {Path(result_path).name}")
    print(f"  Session: {session_name}")
    print(f"  Comment filter: {comment}")
    
    return result_path

def create_batch_active_sets():
    """Create all active sets for current deployment."""
    print("=" * 60)
    print("Creating ACTIVE Sets (2-digit magic)")
    print("=" * 60)
    
    print("\n--- Full-time Sets ---")
    create_active_set(10)  # MH Full-time
    create_active_set(20)  # HR10 Full-time
    create_active_set(30)  # HR05 Full-time
    
    print("\n--- MH Session Sets ---")
    create_active_set(11)  # MH Asia
    create_active_set(12)  # MH London
    create_active_set(13)  # MH NY
    
    print("\n--- HR10 Session Sets ---")
    create_active_set(21)  # HR10 Asia
    create_active_set(22)  # HR10 London
    create_active_set(23)  # HR10 NY
    
    print("\n--- HR05 Session Sets ---")
    create_active_set(31)  # HR05 Asia
    create_active_set(32)  # HR05 London
    create_active_set(33)  # HR05 NY

def create_test_sl_set(magic: int) -> str:
    """Create an SL setfile for a test set."""
    output_dir = get_output_dir()
    ref_dir = get_reference_dir()
    
    filename = f"sl_test{magic}.set"
    filepath = output_dir / filename
    
    # Find reference - try test-specific first, then generic
    ref_candidates = [
        ref_dir / f"sl_test{magic}.set",
        ref_dir / "sl_test112.set",  # Fallback
    ]
    
    ref_path = None
    for candidate in ref_candidates:
        if candidate.exists():
            ref_path = candidate
            break
    
    if not ref_path:
        raise FileNotFoundError(f"No SL test reference file found for {magic}")
    
    ref_content = read_setfile(ref_path)
    lines = ref_content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    comment = f"GU_TEST_{magic}"
    modifications = {
        'comment_to_include': comment,
        'magic_number_to_include': '',
    }
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        if '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in modifications:
                new_lines.append(f"{key}={modifications[key]}")
            else:
                new_lines.append(stripped)
        else:
            new_lines.append(stripped)
    
    content = '\n'.join(new_lines) + '\n'
    filepath.write_text(content, encoding='utf-16')
    
    print(f"Created TEST SL set: {filepath.name}")
    print(f"  Monitors comment: {comment}")
    
    return str(filepath)

def create_batch_test_sets():
    """Create test sets (both GU and SL)."""
    print("\n" + "=" * 60)
    print("Creating TEST Sets (3-digit magic)")
    print("=" * 60)
    
    # Create both GU and SL for each test
    create_test_set(112)
    create_test_sl_set(112)
    
    print("\n(For future tests, both GU and SL files will be created)")
    print("  Example: create_test_set(115) + create_test_sl_set(115)")

def create_batch_sl_sets():
    """Create SL sets for all sessions."""
    print("\n" + "=" * 60)
    print("Creating SL Sets")
    print("=" * 60)
    
    create_sl_set("ASIA", "Asia", "GU_ASIA")
    create_sl_set("LONDON", "London", "GU_LONDON")
    create_sl_set("NEWYORK", "NY", "GU_NEWYORK")

def main():
    """Main entry point for set creation workflow."""
    print("GU Set Creation Workflow")
    print("=" * 60)
    print()
    print("Using Reference folder files as templates")
    print("Strategy-specific settings applied automatically")
    print()
    
    output_dir = get_output_dir()
    ref_dir = get_reference_dir()
    
    if not ref_dir.exists():
        print(f"ERROR: Reference folder not found: {ref_dir}")
        return
    
    create_batch_active_sets()
    create_batch_test_sets()
    create_batch_sl_sets()
    
    print("\n" + "=" * 60)
    print("Set creation complete!")
    print(f"Files saved to: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()
