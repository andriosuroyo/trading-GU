# RGU EA v3.0 - Quick Start Guide

## Installation

1. Copy `Experts/RGU_EA.mq5` to your MT5 `Experts/` folder
2. Copy `Experts/GUM/*.mqh` files if not already present (GUM structures dependency)
3. Compile in MetaEditor
4. Load set file: `Setfiles/RGU/RGU_EA_Optimized.set`

## Optimized Settings (Pre-configured)

| Parameter | Value | Why |
|-----------|-------|-----|
| **ATR_Multiplier** | 1.0x | Aggressive spacing = more entries = higher profit |
| **MaxLayers** | 3 | 4+ layers = 0% recovery rate |
| **UseLayer1Immediate** | **false** | CRITICAL: true = destroys profitability |
| **RecoveryWindow** | 120 min | Optimal balance |
| **EmergencySL** | 30,000 pts | Covers 95th percentile MAE |

## How It Works

1. **Monitors** GU positions for time-based SL hits
2. **Waits** for GU confirmation (same-direction position opens at better price)
3. **Enters** Layer 1 when GU confirms with ATR×1.0 spacing
4. **Adds** Layers 2-3 with same criteria (max 3 layers)
5. **Closes** all layers when:
   - Price hits target (WIN)
   - Time expires 120 min (CLOSE)
   - Emergency SL hit (LOSS)

## Expected Performance

Based on March 23-25, 2026 data:
- **Net Profit**: +83,083 points over 3 days
- **Daily Average**: +27,694 points
- **Recovery Rate**: 78%
- **No Entry Rate**: ~23% (filters poor setups)

## Dashboard Colors

| Color | Meaning |
|-------|---------|
| Green | BUY direction / Recovered |
| Red | SELL direction |
| White | Active, healthy |
| Yellow | Warning (< 30 min remaining) |
| Red | Critical (< 5 min remaining) |
| Gray | Lost / No entry |

## Warnings

⚠️ **NEVER** set `UseLayer1Immediate = true`
- Simulation shows -102,371 point difference vs waiting for GU
- Immediate entry catches falling knives

⚠️ **DO NOT** increase MaxLayers beyond 3
- Layer 4+ showed 0% recovery rate in testing

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No baskets appearing | Check GU positions are closing with loss |
| No entries | Normal - 23% of baskets never get GU confirmation |
| Too many losses | Check emergency SL is appropriate for symbol |

## Files

- `Experts/RGU_EA.mq5` - The EA
- `Setfiles/RGU/RGU_EA_Optimized.set` - Optimized parameters
- `RGU_EA_Specification_v3.md` - Full documentation
