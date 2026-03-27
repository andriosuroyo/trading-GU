# MAE/MFE Analysis CSV Schema Proposal

## Core Principle
Measure price action over **15 minutes from entry** (900 seconds), regardless of actual position duration.

## Proposed Columns

### 1. Position Identification
| Column | Description |
|--------|-------------|
| `position_id` | MT5 position ticket |
| `magic_number` | Strategy identifier (20=HR10, 30=HR05, etc.) |
| `strategy` | Human-readable strategy name |
| `symbol` | Trading symbol (XAUUSD+) |
| `direction` | BUY or SELL |
| `volume` | Lot size |

### 2. Timing
| Column | Description |
|--------|-------------|
| `open_time` | Position open timestamp (UTC) |
| `close_time` | Position close timestamp (UTC) |
| `actual_duration_sec` | Actual seconds position was open |
| `analysis_window_end` | 15-min mark from open (for reference) |

### 3. Price Data
| Column | Description |
|--------|-------------|
| `entry_price` | Position open price (from MT5) |
| `exit_price` | Position close price (from MT5) |
| `tick_entry_bid` | Bid at entry time (from tick data) |
| `tick_entry_ask` | Ask at entry time (from tick data) |
| `tick_exit_bid` | Bid at exit time (from tick data) |
| `tick_exit_ask` | Ask at exit time (from tick data) |

### 4. MAE/MFE (15-Minute Window)
| Column | Description |
|--------|-------------|
| `mae_price` | Maximum Adverse Excursion price (worst against position) |
| `mae_points` | Distance from entry to MAE in points |
| `mfe_price` | Maximum Favorable Excursion price (best for position) |
| `mfe_points` | Distance from entry to MFE in points |
| `mae_time` | Timestamp when MAE occurred |
| `mfe_time` | Timestamp when MFE occurred |
| `time_to_mae_sec` | Seconds from open to MAE |
| `time_to_mfe_sec` | Seconds from open to MFE |

### 5. P&L Metrics
| Column | Description |
|--------|-------------|
| `actual_gross_pl` | Gross P/L as reported by MT5 |
| `actual_net_pl` | Net P/L (gross - commission) |
| `actual_points` | Price difference captured (exit - entry for BUY, entry - exit for SELL) |
| `normalized_net_pl` | Net P/L normalized to 0.01 lot |
| `normalized_points` | Points per 0.01 lot |

### 6. Efficiency Ratios
| Column | Description |
|--------|-------------|
| `mfe_capture_pct` | (actual_points / mfe_points) × 100 - how much of max profit was captured |
| `mae_exposure_pct` | (actual_points / mae_points) × 100 - risk taken vs reward gained |
| `efficiency_ratio` | mfe_points / mae_points - reward potential vs risk taken |

### 7. ATR Context (for Magic 20/30)
| Column | Description |
|--------|-------------|
| `atr_m1_60` | ATR(60) on M1 at entry time (if available) |
| `atr_tp_target` | atr_m1_60 × 0.5 (expected TP distance) |
| `atr_tp_hit` | Boolean - did MFE reach atr_tp_target? |
| `mfe_vs_atr_pct` | (mfe_points / atr_tp_target) × 100 |

### 8. Time-Based Exit Analysis
| Column | Description |
|--------|-------------|
| `exit_reason` | TP, SL, Time-Cutoff, or Other (inferred from duration) |
| `partial_close_eligible` | Was position open at 2-min mark? |
| `full_close_eligible` | Was position open at 5-min mark? |
| `reached_2min` | Did position survive to 2 minutes? |
| `reached_5min` | Did position survive to 5 minutes? |
| `reached_15min` | Did position survive full 15 minutes? |

### 9. Market Context
| Column | Description |
|--------|-------------|
| `session` | Asia/London/NY/Off-Session based on entry hour |
| `hour_utc` | Hour of entry (0-23) |
| `tick_count_15min` | Number of ticks in 15-min analysis window |
| `avg_spread_15min` | Average spread during 15-min window |
| `max_spread_15min` | Maximum spread during 15-min window |

### 10. Data Quality
| Column | Description |
|--------|-------------|
| `tick_data_source` | BlackBull or Vantage |
| `entry_alignment_pts` | |entry_price - tick_entry_price| |
| `exit_alignment_pts` | |exit_price - tick_exit_price| |
| `data_quality_score` | High/Medium/Low based on alignment |

## Questions for Discussion

1. **Should we include post-exit price action?**
   - If position closes at 3 min, do we care what happened at 10 min?
   - Current proposal: NO, analysis stops at exit OR 15 min, whichever comes first
   - Alternative: Always analyze full 15 min regardless of exit time

2. **ATR data availability?**
   - Do we have historical ATR(60) M1 values?
   - If not, we may need to fetch OHLC M1 data and calculate ATR

3. **Volume/profile data?**
   - Should we include volume at entry/MAE/MFE?
   - Could help identify high-volume rejection zones

4. **Partial close reconstruction?**
   - Without EA logs, we can't know for certain if partial close occurred
   - Should we infer from duration patterns?

5. **Session-specific analysis?**
   - Should we include session overlap indicators (e.g., London-NY overlap)?
   - Pre-news volatility flags?

## Recommended Minimum Viable Columns
For immediate implementation:
- Position ID, Magic, Strategy, Direction, Volume
- Open/Close Time, Actual Duration
- Entry/Exit Prices
- MAE/MFE Prices & Points
- MFE Capture %
- Actual/Normalized P&L
- Session
- Tick Count
- Data Quality Score
