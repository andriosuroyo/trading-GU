"""
Magic Number to #code mapping configuration
Centralized mapping for analysis scripts
"""

# Magic number to code mapping
# Format: m{timeframe}{fast_ma}{slow_ma}{pt_mult}
# H = hundred (100), used to keep character count constant

MAGIC_CODES = {
    # DISCONTINUED
    1: {'code': 'm1082805', 'timeframe': 'M1', 'fast': 8, 'slow': 28, 'pt_mult': 0.5, 
        'status': 'DISCONTINUED', 'note': 'Too aggressive (8/28 ratio), bad positions'},
    
    # ACTIVE - Core 10/40 combinations
    2: {'code': 'm1104005', 'timeframe': 'M1', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
        'status': 'ACTIVE', 'note': 'Core winner - M1 10/40 0.5x'},
    3: {'code': 'm1208005', 'timeframe': 'M1', 'fast': 20, 'slow': 80, 'pt_mult': 0.5, 
        'status': 'ACTIVE', 'note': 'Slow MAs - moderate performance'},
    
    # M15 timeframe with H (hundred) notation
    4: {'code': 'm1501H05', 'timeframe': 'M15', 'fast': 1, 'slow': 100, 'pt_mult': 0.5, 
        'status': 'ACTIVE', 'note': 'M15 1/100 - sluggish'},
    5: {'code': 'm1502H05', 'timeframe': 'M15', 'fast': 2, 'slow': 100, 'pt_mult': 0.5, 
        'status': 'ACTIVE', 'note': 'M15 2/100 - sluggish'},
    6: {'code': 'm1H2H05', 'timeframe': 'M1', 'fast': 100, 'slow': 200, 'pt_mult': 0.5, 
        'status': 'ACTIVE', 'note': 'M1 100/200 - too slow for intraday'},
    
    # DEACTIVATED 2026.03.24 - All sets now use PT=0.5 (sweeping changes if adjusted)
    7: {'code': 'm1104003', 'timeframe': 'M1', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
        'status': 'DEACTIVATED', 'note': 'Was PT=0.3x - all sets now use 0.5x'},
    8: {'code': 'm1104007', 'timeframe': 'M1', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
        'status': 'DEACTIVATED', 'note': 'Was PT=0.7x - all sets now use 0.5x'},
    
    # DEACTIVATED 2026.03.24 - 8/28 ratio not profitable
    9: {'code': 'm5082803', 'timeframe': 'M5', 'fast': 8, 'slow': 28, 'pt_mult': 0.5, 
        'status': 'DEACTIVATED', 'note': '8/28 on M5 - data shows unprofitability'},
    10: {'code': 'm5082805', 'timeframe': 'M5', 'fast': 8, 'slow': 28, 'pt_mult': 0.5, 
        'status': 'DEACTIVATED', 'note': '8/28 on M5 - data shows unprofitability'},
    11: {'code': 'm2082805', 'timeframe': 'M2', 'fast': 8, 'slow': 28, 'pt_mult': 0.5, 
        'status': 'DEACTIVATED', 'note': '8/28 on M2 - data shows unprofitability'},
    
    # Best performer
    12: {'code': 'm2104005', 'timeframe': 'M2', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
        'status': 'ACTIVE', 'note': 'Core winner - M2 10/40 0.5x (BEST)'},
}

# ADDED 2026.03.24 - New test sets based on winning 10/40 ratio
# These are now ACTIVE in your list
MAGIC_CODES.update({
    13: {'code': 'm3104005', 'timeframe': 'M3', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
         'status': 'ACTIVE', 'note': 'Extend winning 10/40 to M3'},
    14: {'code': 'm4104005', 'timeframe': 'M4', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
         'status': 'ACTIVE', 'note': 'Extend winning 10/40 to M4'},
    15: {'code': 'm5104005', 'timeframe': 'M5', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
         'status': 'ACTIVE', 'note': 'Replace losing 8/28 on M5 with winning 10/40'},
    16: {'code': 'm6104005', 'timeframe': 'M6', 'fast': 10, 'slow': 40, 'pt_mult': 0.5, 
         'status': 'ACTIVE', 'note': 'Extend winning 10/40 to M6'},
    17: {'code': 'm1103505', 'timeframe': 'M1', 'fast': 10, 'slow': 35, 'pt_mult': 0.5, 
         'status': 'ACTIVE', 'note': 'Test tighter 10/35 ratio (1:3.5)'},
    18: {'code': 'm1104505', 'timeframe': 'M1', 'fast': 10, 'slow': 45, 'pt_mult': 0.5, 
         'status': 'ACTIVE', 'note': 'Test looser 10/45 ratio (1:4.5)'},
    19: {'code': 'm1124805', 'timeframe': 'M1', 'fast': 12, 'slow': 48, 'pt_mult': 0.5, 
         'status': 'ACTIVE', 'note': 'Maintain 1:4 ratio with higher MAs'},
})

# Redundant magic numbers (same entries, different PT)
# These should be considered for deactivation
REDUNDANT_GROUPS = {
    'M1_10_40': [2, 7, 8],  # Same entries, PT: 0.5, 0.3, 0.7
    'M2_10_40': [12],  # Only one variant active
}

def get_code_info(magic_number):
    """Get code info for a magic number"""
    return MAGIC_CODES.get(magic_number, {'code': 'UNKNOWN', 'note': 'Not configured'})

def format_code_string(code_dict):
    """Format code dict into human-readable string"""
    return f"{code_dict['code']} ({code_dict['timeframe']} Fast={code_dict['fast']} Slow={code_dict['slow']} PT={code_dict['pt_mult']}x)"

def is_redundant(magic_number):
    """Check if magic number is part of a redundant PT group"""
    for group_name, magics in REDUNDANT_GROUPS.items():
        if magic_number in magics and len(magics) > 1:
            return True, group_name
    return False, None
