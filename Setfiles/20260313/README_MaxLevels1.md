# MaxLevels=1 Single-Position Scalping Strategy

## Overview
These setfiles configure the GU EA for pure scalping with NO grid/layering (MaxLevels=1).
Each trade stands alone - no second position is opened.

## Key Changes from Grid Strategy

| Parameter | Grid (MaxLevels=2) | Scalping (MaxLevels=1) |
|-----------|-------------------|----------------------|
| InpMaxLevels | 2 | 1 |
| InpUseATRStep | true | false |
| InpStepPoints | 650 | 0 |
| InpTargetProfitMoney | 2.5-5.0 (ATR-based) | Session-specific fixed |
| InpUseATRTPTarget | true | false |
| InpUseBasketTrail | true | false |

## Session-Specific Optimizations

Based on March 12-13 data analysis (138 trades):

### ASIA (00:00-08:00 UTC)
- **TargetProfitMoney: $4.50**
- Performance: 78.9% win rate, $96.30 profit
- Best at: Quick 5-min scalps (86.7% WR)
- Characteristic: Consistent small wins

### LONDON (08:00-16:00 UTC) ⚠️
- **TargetProfitMoney: $3.50** (Lower target = faster exits)
- Performance: 71.8% win rate, BUT -$1,340 loss
- **CRITICAL**: Long trades (>30min) = 0% win rate, -$1,614 loss
- **SOLUTION**: Lower profit target forces faster exits
- Without grid: Must scalp quickly or die

### NY (16:00-23:00 UTC)
- **TargetProfitMoney: $6.00** (Highest target)
- Performance: 83.3% win rate, $267.70 profit
- Best at: Quick scalps (90.2% WR on <5min trades)
- Characteristic: Strong momentum, can handle higher targets

## Rationale for Settings

### Why Fixed Targets (InpUseATRTPTarget=false)?
With MaxLevels=1, we cannot rely on ATR-based dynamic targets because:
1. No second position to average into
2. Must hit target on first attempt
3. Session volatility patterns differ significantly

### Why No ATR Step (InpUseATRStep=false, InpStepPoints=0)?
- No second position = no step needed
- Pure single-entry scalping

### Why No Basket Trail (InpUseBasketTrail=false)?
- Single position only
- Trail would interfere with fixed profit target

## Performance Data Summary

| Session | Win Rate | Total P/L | Avg Duration | Best Duration |
|---------|----------|-----------|--------------|---------------|
| Asia | 78.9% | +$96.30 | 5.4 min | <5 min (86.7% WR) |
| London | 71.8% | -$1,340 | 9.2 min | <5 min (88.9% WR) |
| NY | 83.3% | +$267.70 | 2.6 min | <5 min (90.2% WR) |

## Risk Warning: London Session

London is problematic for single-position strategy:
- Grid strategy hides losses by averaging down
- Without grid, London's volatility causes large losses on long-duration trades
- **Recommendation**: Consider NOT trading London with MaxLevels=1, or use very tight time stop

## Files Created

1. `gu_mh_asia_max1.set` - ASIA optimized
2. `gu_mh_london_max1.set` - LONDON optimized (conservative)
3. `gu_mh_ny_max1.set` - NY optimized (aggressive target)

## Next Steps

1. Test these setfiles in demo
2. Monitor London closely - consider 10-minute max duration exit
3. If London continues to lose, exclude it from MaxLevels=1 trading
4. Asia and NY show promise for pure scalping
