# RFC 002: GUS (GU Score) — Self-Optimizing Trade Quality Engine

> **Status:** READY FOR REVIEW  
> **Target Version:** 1.0.0  
> **Priority:** HIGH  
> **Type:** New EA (Standalone)  
> **Estimated Implementation:** ~4-5 hours  
> **Estimated Testing:** ~6-8 hours

---

## Executive Summary

GUS is a **machine learning feedback loop** for GU trade quality assessment. It evaluates every GU position at entry using 6 technical indicators, tracks the outcome (WIN/LOSS), and auto-adjusts factor weights to improve prediction accuracy over time.

**Core Philosophy:** *"The market teaches; GUS listens."*

---

## Architecture Overview

```
GU Opens Position → GUS Detects → Calculates 6-Factor Score → Monitors → Records Outcome
                                         ↓                                      ↓
                                    Discord Alert (≥80)                    Adjusts Weights
                                                                         (Gradient Descent)
```

**Key Design Principles:**
- Pure technical analysis (no manual inputs, no time penalties)
- Self-optimizing weights (auto-adjust after each trade)
- Separate from RecoveryManager (different lifecycle)
- Standalone EA (future GU integration planned for v2.0)

---

## 1. Indicator Set (6 Factors)

### Category 1: Trend & Momentum (3 indicators)

| # | Indicator | Calculation | Score Logic (0-100) |
|---|-----------|-------------|---------------------|
| 1 | **RSI Reversion** | `abs(iRSI(14) - 50)` | 100 when RSI = 50 (mean reversion), 0 when RSI = 0 or 100 (extreme) |
| 2 | **MA20 Distance** | `(Close - iMA(20)) / iATR(14)` | 100 when price at optimal distance (±0.5 ATR), 0 when >3 ATR away |
| 3 | **MACD Momentum** | Histogram slope (5-bar) | 100 when histogram rising from negative, 0 when falling from positive |

### Category 2: Volatility & Range (2 indicators)

| # | Indicator | Calculation | Score Logic (0-100) |
|---|-----------|-------------|---------------------|
| 4 | **ATR Ratio** | `iATR(14) / avg(iATR(14), 20)` | 100 when ATR at average (1.0), 0 when >2x or <0.5x average |
| 5 | **Spread Quality** | `SYMBOL_SPREAD / avg_spread(20)` | 100 when spread tight (<1.0x avg), 0 when >3x average |

### Category 3: Market Structure (1 indicator)

| # | Indicator | Calculation | Score Logic (0-100) |
|---|-----------|-------------|---------------------|
| 6 | **Range Position** | `(Close - DayLow) / (DayHigh - DayLow)` | 100 when at 50% of day's range (middle), 0 when at extremes (0% or 100%) |

**Total: 6 indicators** — all calculable from standard MT5 data, no external dependencies.

---

## 2. Scoring Algorithm

### 2.1 Initial Weights (v1.0 Baseline)

```mq5
double g_weights[6] = {
    0.25,  // RSI Reversion (25%) — mean reversion core
    0.20,  // MA20 Distance (20%) — trend alignment
    0.15,  // MACD Momentum (15%) — momentum confirmation
    0.20,  // ATR Ratio (20%) — volatility filter
    0.10,  // Spread Quality (10%) — execution quality
    0.10   // Range Position (10%) — structural location
};
// Sum: 100%
```

### 2.2 Score Calculation

```mq5
int CalculateGUScore(ulong ticket, string symbol, int positionType)
{
    double rawScores[6];
    
    rawScores[0] = CalculateRSIScore(symbol);        // 0-100
    rawScores[1] = CalculateMADistanceScore(symbol); // 0-100
    rawScores[2] = CalculateMACDScore(symbol);       // 0-100
    rawScores[3] = CalculateATRScore(symbol);        // 0-100
    rawScores[4] = CalculateSpreadScore(symbol);     // 0-100
    rawScores[5] = CalculateRangeScore(symbol);      // 0-100
    
    double finalScore = 0;
    for(int i = 0; i < 6; i++)
        finalScore += rawScores[i] * g_weights[i];
    
    return (int)MathRound(finalScore);
}
```

### 2.3 Individual Score Functions

**RSI Reversion Score:**
```mq5
int CalculateRSIScore(string symbol)
{
    double rsi = iRSI(symbol, PERIOD_M1, 14, PRICE_CLOSE, 0);
    double distanceFrom50 = MathAbs(rsi - 50.0);
    
    // 100 at RSI=50, 0 at RSI=0 or 100
    return (int)MathRound(100.0 - (distanceFrom50 * 2.0));
}
```

**MA20 Distance Score:**
```mq5
int CalculateMADistanceScore(string symbol)
{
    double ma20 = iMA(symbol, PERIOD_M1, 20, 0, MODE_SMA, PRICE_CLOSE, 0);
    double atr = iATR(symbol, PERIOD_M1, 14, 0);
    double close = iClose(symbol, PERIOD_M1, 0);
    
    if(atr == 0) return 50; // Neutral on error
    
    double distance = (close - ma20) / atr;
    double absDistance = MathAbs(distance);
    
    // Optimal: 0.5 ATR distance = 100
    // Poor: >3 ATR distance = 0
    if(absDistance <= 0.5) return 100;
    if(absDistance >= 3.0) return 0;
    
    return (int)MathRound(100.0 * (3.0 - absDistance) / 2.5);
}
```

**MACD Momentum Score:**
```mq5
int CalculateMACDScore(string symbol)
{
    double hist[5];
    for(int i = 0; i < 5; i++)
        hist[i] = iMACD(symbol, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_HISTOGRAM, i);
    
    double slope = hist[0] - hist[4]; // 5-bar change
    
    // Rising momentum from negative = best (100)
    // Falling momentum from positive = worst (0)
    if(hist[0] < 0 && slope > 0) return 100; // Rising from negative
    if(hist[0] > 0 && slope < 0) return 0;   // Falling from positive
    if(hist[0] < 0 && slope < 0) return 30;  // Falling, still negative
    if(hist[0] > 0 && slope > 0) return 70;  // Rising, already positive
    
    return 50;
}
```

**ATR Ratio Score:**
```mq5
int CalculateATRScore(string symbol)
{
    double currentATR = iATR(symbol, PERIOD_M1, 14, 0);
    double sumATR = 0;
    for(int i = 0; i < 20; i++)
        sumATR += iATR(symbol, PERIOD_M1, 14, i);
    double avgATR = sumATR / 20.0;
    
    if(avgATR == 0) return 50;
    
    double ratio = currentATR / avgATR;
    
    // 1.0 = perfect (100)
    // <0.5 or >2.0 = poor (0)
    if(ratio >= 0.8 && ratio <= 1.2) return 100;
    if(ratio < 0.5 || ratio > 2.0) return 0;
    
    if(ratio < 0.8)
        return (int)MathRound(100.0 * (ratio - 0.5) / 0.3);
    else
        return (int)MathRound(100.0 * (2.0 - ratio) / 0.8);
}
```

**Spread Quality Score:**
```mq5
int CalculateSpreadScore(string symbol)
{
    long currentSpread = SymbolInfoInteger(symbol, SYMBOL_SPREAD);
    
    // Calculate 20-bar average spread from tick data or use stored
    static double avgSpread = 0;
    if(avgSpread == 0) avgSpread = (double)currentSpread; // Init
    
    // Exponential moving average of spread
    avgSpread = avgSpread * 0.95 + (double)currentSpread * 0.05;
    
    if(avgSpread == 0) return 50;
    
    double ratio = (double)currentSpread / avgSpread;
    
    // <1.0x = 100, >3.0x = 0
    if(ratio <= 1.0) return 100;
    if(ratio >= 3.0) return 0;
    
    return (int)MathRound(100.0 * (3.0 - ratio) / 2.0);
}
```

**Range Position Score:**
```mq5
int CalculateRangeScore(string symbol)
{
    MqlRates rates[];
    if(CopyRates(symbol, PERIOD_D1, 0, 1, rates) < 1) return 50;
    
    double dayHigh = rates[0].high;
    double dayLow = rates[0].low;
    double close = iClose(symbol, PERIOD_M1, 0);
    
    double range = dayHigh - dayLow;
    if(range == 0) return 50;
    
    double position = (close - dayLow) / range;
    
    // 0.5 = middle = 100
    // 0.0 or 1.0 = extremes = 0
    double distanceFromMiddle = MathAbs(position - 0.5);
    return (int)MathRound(100.0 - (distanceFromMiddle * 200.0));
}
```

---

## 3. Auto-Adjustment Mechanism

### 3.1 Weight Update Logic (Gradient Descent)

After each position closes:

```mq5
void UpdateWeights(ulong ticket, bool isWin)
{
    double learningRate = 0.01; // Max 1% adjustment per trade
    
    // Get stored factor values for this position
    double factorValues[6];
    if(!GetFactorValuesFromHistory(ticket, factorValues))
        return;
    
    for(int i = 0; i < 6; i++)
    {
        double factorValue = factorValues[i]; // 0-100
        
        // Case 1: Win + High Factor → Increase weight (factor helped)
        if(isWin && factorValue > 50)
            g_weights[i] += learningRate * (factorValue / 100.0);
        
        // Case 2: Loss + High Factor → Decrease weight (factor misled)
        else if(!isWin && factorValue > 50)
            g_weights[i] -= learningRate * (factorValue / 100.0);
        
        // Case 3: Win + Low Factor → Decrease weight (factor opposed success)
        else if(isWin && factorValue <= 50)
            g_weights[i] -= learningRate * ((100 - factorValue) / 100.0);
        
        // Case 4: Loss + Low Factor → Increase weight (factor predicted loss)
        else if(!isWin && factorValue <= 50)
            g_weights[i] += learningRate * ((100 - factorValue) / 100.0);
        
        // Clamp weights: 0.01 to 0.50
        g_weights[i] = MathMax(0.01, MathMin(0.50, g_weights[i]));
    }
    
    // Renormalize to sum = 1.0
    NormalizeWeights();
    
    // Log the adjustment
    LogWeightAdjustment(ticket, isWin);
    
    // Save to CSV
    SaveWeightsToCSV();
}
```

### 3.2 Normalization

```mq5
void NormalizeWeights()
{
    double sum = 0;
    for(int i = 0; i < 6; i++)
        sum += g_weights[i];
    
    if(sum == 0) return; // Safety
    
    for(int i = 0; i < 6; i++)
        g_weights[i] = g_weights[i] / sum;
}
```

### 3.3 Correlation Tracking

For analytics, track correlation coefficient:

```mq5
void UpdateCorrelationStats(int factorIndex, double factorValue, bool isWin)
{
    // Simple moving correlation
    // Store in global arrays for reporting
    g_factorWins[factorIndex] += isWin ? 1 : 0;
    g_factorTotal[factorIndex]++;
    g_factorAvgValue[factorIndex] = (g_factorAvgValue[factorIndex] * (g_factorTotal[factorIndex] - 1) + factorValue) / g_factorTotal[factorIndex];
}
```

---

## 4. Data Architecture (CSV)

### 4.1 File 1: `gus_active_positions.csv`

```csv
position_id,ticket,symbol,entry_time,entry_price,position_type,final_score,rsi_score,ma_score,macd_score,atr_score,spread_score,range_score,status,detected_time
2026032001,123456789,XAUUSD,2026-03-20 10:00:00,1950.50,SELL,82,75,80,90,85,85,70,OPEN,2026-03-20 10:00:05
```

### 4.2 File 2: `gus_completed_trades.csv`

```csv
position_id,ticket,entry_time,close_time,entry_score,outcome,pnl,mae,mfe,duration_seconds,weight_adjustment_time
2026032001,123456789,2026-03-20 10:00:00,2026-03-20 10:05:00,82,WIN,15.50,-8.00,25.00,300,2026-03-20 10:05:02
2026032002,123456790,2026-03-20 10:15:00,2026-03-20 10:20:00,45,LOSS,-12.00,-15.00,3.00,300,2026-03-20 10:20:01
```

### 4.3 File 3: `gus_weights.csv` (Current Algorithm State)

```csv
factor_name,weight,total_trades,win_rate_when_high,correlation,last_updated,adjustment_count
RSI_Reversion,0.25,150,0.72,0.48,2026-03-20 16:00:00,23
MA20_Distance,0.20,150,0.68,0.42,2026-03-20 16:00:00,19
MACD_Momentum,0.15,150,0.65,0.38,2026-03-20 16:00:00,15
ATR_Ratio,0.20,150,0.61,0.31,2026-03-20 16:00:00,21
Spread_Quality,0.10,150,0.58,0.22,2026-03-20 16:00:00,12
Range_Position,0.10,150,0.55,0.18,2026-03-20 16:00:00,8
```

### 4.4 File 4: `gus_adjustment_log.csv` (Audit Trail)

```csv
adjustment_time,trade_ticket,trade_outcome,old_weights,new_weights,reason
2026-03-20 10:05:02,123456789,WIN,"0.25,0.20,0.15,0.20,0.10,0.10","0.252,0.201,0.151,0.201,0.098,0.097","Trade WIN with high RSI (75)"
```

---

## 5. Discord Integration

### 5.1 High Score Alert (Score ≥ 80)

```json
{
  "username": "GUS Scoring Engine",
  "avatar_url": "https://i.imgur.com/chart.png",
  "embeds": [{
    "title": "🎯 High-Probability GU Setup Detected",
    "color": 3066993,
    "timestamp": "2026-03-20T10:00:05.000Z",
    "fields": [
      {"name": "Position", "value": "SELL XAUUSD @ 1950.50 (#123456789)", "inline": false},
      {"name": "GUS Score", "value": "**82/100** (STRONG)", "inline": true},
      {"name": "Primary Factors", "value": "```\nRSI Reversion:    75/100\nMA20 Distance:    80/100\nMACD Momentum:    90/100\nATR Ratio:        85/100\nSpread Quality:   85/100\nRange Position:   70/100\n```", "inline": false},
      {"name": "Historical Accuracy", "value": "Score ≥ 80: 72% win rate (108 trades)", "inline": false}
    ]
  }]
}
```

### 5.2 Daily Summary Alert (Optional)

```json
{
  "title": "📊 GUS Algorithm Daily Summary",
  "fields": [
    {"name": "Trades Today", "value": "12", "inline": true},
    {"name": "Win Rate", "value": "67%", "inline": true},
    {"name": "Average Score", "value": "68.5", "inline": true},
    {"name": "Weight Adjustments", "value": "3", "inline": false},
    {"name": "Current Top Factor", "value": "RSI Reversion (0.26) — 0.48 correlation", "inline": false}
  ]
}
```

---

## 6. EA Architecture

### 6.1 File Structure

```
Experts/
└── GUS/
    ├── GUSScoringEngine.mq5      (Main EA)
    ├── GUS_Indicators.mqh        (6 factor calculations)
    ├── GUS_Database.mqh          (CSV I/O operations)
    ├── GUS_Discord.mqh           (Webhook functions)
    └── GUS_Dashboard.mqh         (Chart UI)
```

### 6.2 Core Class Structure

```mq5
class CGUS_Engine
{
private:
    double m_weights[6];
    string m_symbol;
    
    double CalculateRSIScore();
    double CalculateMADistanceScore();
    double CalculateMACDScore();
    double CalculateATRScore();
    double CalculateSpreadScore();
    double CalculateRangeScore();
    
public:
    bool Initialize();
    void ScanForNewPositions();
    void MonitorActivePositions();
    void ProcessClosedPosition(ulong ticket);
    void UpdateWeights(ulong ticket, bool isWin);
    int CalculateScore(ulong ticket);
    void SendDiscordAlert(ulong ticket, int score);
};
```

### 6.3 OnTick Workflow

```mq5
void OnTick()
{
    // 1. Check for new GU positions (magic filter: 11,12,13,etc)
    g_engine.ScanForNewPositions();
    
    // 2. Update PnL on active positions
    g_engine.MonitorActivePositions();
    
    // 3. Update dashboard
    g_dashboard.Update();
}

void OnTrade()
{
    // Check for newly closed positions
    g_engine.CheckForClosedPositions();
}
```

---

## 7. Input Parameters

```mq5
input group "=== GUS Core Settings ==="
input string InpGUSMagicNumbers = "11,12,13";    // GU magic numbers to monitor
input int    InpMinScoreForAlert = 80;           // Discord alert threshold (0-100)
input bool   InpAutoAdjustWeights = true;        // Enable self-optimization
input double InpLearningRate = 0.01;             // Max weight adjustment per trade

input group "=== RSI Settings ==="
input int    InpRSIPeriod = 14;                  // RSI period
input int    InpRSITimeframe = PERIOD_M1;        // RSI timeframe

input group "=== MA Settings ==="
input int    InpMAPeriod = 20;                   // MA period
input int    InpMATimeframe = PERIOD_M1;         // MA timeframe

input group "=== MACD Settings ==="
input int    InpMACDFast = 12;                   // MACD fast
input int    InpMACDSlow = 26;                   // MACD slow
input int    InpMACDSignal = 9;                  // MACD signal

input group "=== ATR Settings ==="
input int    InpATRPeriod = 14;                  // ATR period
input int    InpATRHistory = 20;                 // Bars for ATR average

input group "=== Discord Integration ==="
input string InpDiscordWebhook = "";             // Discord webhook URL
input bool   InpSendDailySummary = false;        // Send daily summary at 00:00

input group "=== File Paths ==="
input string InpActiveFile = "gus_active_positions.csv";
input string InpCompletedFile = "gus_completed_trades.csv";
input string InpWeightsFile = "gus_weights.csv";
input string InpAdjustmentLog = "gus_adjustment_log.csv";
```

---

## 8. Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ GUS SCORING ENGINE v1.0                                     │
├─────────────────────────────────────────────────────────────┤
│ Active Positions: 3    Total Scored: 147    Win Rate: 68%   │
├──────────┬──────────┬──────────┬─────────────┬──────────────┤
│ Ticket   │ Score    │ RSI      │ MA Dist     │ Status       │
├──────────┼──────────┼──────────┼─────────────┼──────────────┤
│ 123456789│ 82       │ 75       │ +0.8 ATR    │ OPEN (+$15)  │
│ 123456790│ 45       │ 35       │ -2.1 ATR    │ OPEN (-$8)   │
│ 123456791│ 91       │ 80       │ +0.4 ATR    │ OPEN (+$22)  │
└──────────┴──────────┴──────────┴─────────────┴──────────────┘

Current Weights:
RSI: 0.26  MA: 0.20  MACD: 0.15  ATR: 0.19  Spread: 0.10  Range: 0.10
Last Adjustment: 2026-03-20 10:05:02
```

---

## 9. Testing Protocol

### 9.1 Phase 1: Indicator Validation (1-2 hours)
- [ ] Verify RSI score = 100 when RSI=50
- [ ] Verify MA score peaks at ±0.5 ATR
- [ ] Verify MACD score logic (rising/falling histograms)
- [ ] Verify ATR score peaks at ratio=1.0
- [ ] Verify spread score tracks actual spread
- [ ] Verify range score = 100 at 50% of day

### 9.2 Phase 2: Scoring Validation (2-3 hours)
- [ ] Score calculation produces 0-100 range
- [ ] Weights sum to 100% after normalization
- [ ] High score positions (≥80) tracked separately
- [ ] All 6 factor values stored correctly

### 9.3 Phase 3: Outcome Tracking (2-3 hours)
- [ ] Position close detected via OnTrade()
- [ ] PnL recorded accurately
- [ ] MAE/MFE calculated from position history
- [ ] WIN/LOSS classification correct

### 9.4 Phase 4: Auto-Adjustment (2-3 hours)
- [ ] Weights adjust after each trade
- [ ] Adjustment respects ±1% limit
- [ ] Weights renormalize to 100%
- [ ] Adjustment logged to CSV
- [ ] Clamp respected (0.01-0.50 range)

### 9.5 Phase 5: Integration (1-2 hours)
- [ ] Discord alert fires for score ≥ 80
- [ ] Dashboard updates in real-time
- [ ] CSV files readable in Excel
- [ ] No conflicts with TCM v2.3.0

---

## 10. Success Metrics

After 100 trades, GUS should demonstrate:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Score ≥ 80 win rate | >65% | Compare to baseline (assume 55% GU win rate) |
| Score ≤ 40 win rate | <45% | Should be worse than baseline |
| Top factor correlation | >0.35 | RSI Reversion should dominate |
| Weight stability | <20% drift | No single factor should exceed 40% |
| Alert accuracy | >70% | Score ≥ 80 positions should win >70% |

---

## 11. Future Roadmap (v2.0+)

- **GU Filter Integration:** GUS score ≥ X required for GU to open
- **Multi-Timeframe Scoring:** M5, M15, H1 factor aggregation
- **Dynamic Threshold:** Alert threshold adjusts based on market regime
- **Machine Learning:** Replace gradient descent with neural network
- **RecoveryManager Integration:** Recovery candidates include GUS score of original trade

---

## 12. Header for Implementation

```mq5
//+------------------------------------------------------------------+
//|                                       GUSScoringEngine.mq5        |
//|                        GUS — GU Score Engine                      |
//|                        VERSION 1.0.0 - WORK IN PROGRESS           |
//|                        DO NOT DEPLOY - TESTING PHASE              |
//|                                                                   |
//|  FEATURES v1.0.0:                                                 |
//|  - 6-factor technical analysis scoring                            |
//|  - Self-optimizing weights (gradient descent)                     |
//|  - Binary outcome tracking (WIN/LOSS)                             |
//|  - Discord integration for high-score alerts                      |
//|  - CSV database for analysis                                      |
//|                                                                   |
//|  INDICATORS:                                                      |
//|  - RSI Reversion, MA20 Distance, MACD Momentum                    |
//|  - ATR Ratio, Spread Quality, Range Position                      |
//+------------------------------------------------------------------+
#property copyright "GU Trading"
#property link      ""
#property version   "1.00"
#property strict
```

---

**RFC Status:** ✅ APPROVED — Ready for implementation

**Dependencies:** None (pure technical indicators)

**Next Steps:**
1. Implement `GUSScoringEngine.mq5`
2. Implement 6 factor calculation functions
3. Implement CSV I/O
4. Implement Discord webhook
5. Test on Vantage Demo

*Prepared by: Viktor Kozlov (MQ5 Systems Architect)*  
*Date: 2026-03-20*
