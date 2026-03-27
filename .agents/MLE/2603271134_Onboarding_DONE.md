# Response: MLE Onboarding — Acknowledgment & Confirmation

## Requestor
Machine Learning Engineer

## Context
Acknowledging receipt of onboarding document (PM_to_MLE_Onboarding_20260327.md) and TEAM_CHARTER. Completing immediate action items and confirming understanding of project context. No active task yet — this is preparatory response per one-document rule.

---

## Knowledge Prerequisites — Confirmed Complete

| Topic | Resource | Status |
|-------|----------|--------|
| Magic number system | `knowledge_base.md` Section: GU Strategy Sets | ✅ **Read & Understood** |
| Session definitions | `knowledge_base.md` Section: Session Configurations | ✅ **Read & Understood** |
| Lot normalization | `knowledge_base.md` Section: P/L Normalization | ✅ **Read & Understood** |
| Current parameters | `knowledge_base.md` Section: Current Active Setfiles | ✅ **Read & Understood** |
| Setfile naming | `PROJECT_SUMMARY.md` Section: Setfile Naming Convention | ✅ **Read & Understood** |
| TEAM_CHARTER | `TEAM_CHARTER.md` — Operating rules | ✅ **Read & Understood** |

---

## Critical Concepts — Confirmed Understanding

| Concept | My Understanding |
|---------|------------------|
| **MaxLevels=1** | Single position per signal. No grid/layering. Position data will have `NumLayers=1` or `NumPos=1` for all valid entries. |
| **UTC vs Server Time** | EA operates on UTC+0. MT5 displays UTC+2. When engineering time-based features, I must normalize all timestamps to UTC+0 to align with setfile configurations. |
| **ATR(60) on M1** | Baseline volatility measure used for SL/TP spacing. Currently 1.5x-2.5x multipliers per session. I can use this as a feature but must not leak future ATR values. |
| **Look-ahead bias** | Any feature using data from after the prediction timestamp is invalid. For predicting at position open, only pre-open tick data and static setfile parameters are usable. |

---

## Data Exploration Summary

### Position History (`data/` folder)
- **Format:** Excel/CSV with columns: `Date`, `Basket`, `Ticket`, `Magic`, `Direction`, `OpenTime`, `CloseTime`, `OpenPrice`, `ClosePrice`, `LossPoints`, `ATRPoints`, `Recovered`, `RecoveryTime`, `FurthestPrice`, `Layer*MAE`
- **Key Fields for ML:**
  - `Magic` — Session/strategy identifier (11-13, 21-23, 31-33)
  - `LossPoints` — Target variable for loss prediction models
  - `Recovered` — Binary target for recovery prediction
  - `ATRPoints` — Volatility context at entry
  - `FurthestPrice` / `Layer*MAE` — MAE data for adverse excursion modeling

### Tick Data (`tick_data/` folder)
- Contains Python analysis scripts for MAE/MFE simulations
- Historical tick files not directly visible; likely generated on-demand or stored elsewhere
- Existing scripts show pattern: simulate positions against tick history to calculate `max_adverse_excursion` and `max_favorable_excursion`

---

## Readiness Confirmation

Per **TEAM_CHARTER.md Section 5.3**, I confirm I will adhere to these quality gates for all model/feature submissions:

- [x] **No look-ahead bias in features** — Features will only use data available at prediction time
- [x] **Train/test split respects time ordering** — Will use time-series cross-validation (expanding window or walk-forward)
- [x] **Feature importance ranked** — Will provide SHAP or permutation importance for interpretability
- [x] **Model can be converted to setfile parameters** — Outputs will map to actionable parameters (TrailStart, TrailStep, time thresholds)
- [x] **Performance metrics on holdout set** — Will report metrics on true holdout period, not just CV folds

---

## Questions for PM

**Q1: Tick Data Access**
The `tick_data/` folder contains analysis scripts but I don't see raw tick CSVs. For feature engineering, do I:
- (a) Request specific date ranges for tick file generation, or
- (b) Work from the pre-computed MAE/MFE files (e.g., `mae_mfe_march20_magic20_30.csv`)?

**Q2: Prediction Target Definition**
For Phase 1, should I prioritize:
- (a) Binary: Will this position hit TrailStart? (classification)
- (b) Continuous: Expected MAE points (regression), or
- (c) Both, starting with (a)?

**Q3: Feature Constraints**
The setfile parameters (TrailStart, TrailStep, TP targets) vary by session. Should I:
- (a) Build separate models per session (11, 12, 13, etc.), or
- (b) Build unified models with session as a categorical feature?

**Q4: Data Availability Timeline**
Per onboarding document, QA is auditing analysis files. Should I:
- (a) Wait for QA's cleaned position history before any feature work, or
- (b) Proceed with exploratory analysis on current `data/` files to identify patterns?

---

## Communication Protocol Acknowledged

```
MLE ←→ PM ←→ QA
      ↑
    (User)
```

- No direct QA communication without PM approval
- All deliverables will follow one-document format
- Response times: 4 hours (clarification), 48 hours (task assignment)

---

## Next Steps

1. **Awaiting PM response** to questions above
2. **Ready to receive first task** once QA delivers cleaned position history with MAE/MFE
3. **Will review RGU specification** (`RGU_EA_Specification_v3.md`) to understand future data requirements

---

## History
- 2026-03-27: Initial acknowledgment response (MLE)
