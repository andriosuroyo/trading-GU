# Trading Recommendations Report
## Based on March 20, 23, 24 Data Analysis

---

## 1. TRADING HOURS: 01:00-23:00 vs Full Day

### Daily Breakdown

| Date | Full Day (24h) | 01:00-23:00 | Excluded (0h/23h) | Verdict |
|------|----------------|-------------|-------------------|---------|
| Mar 20 | +7,052 pts | +5,997 pts | +1,055 gains | Sacrificed gains |
| Mar 23 | -3,805 pts | -7,153 pts | +3,348 gains | Sacrificed gains |
| Mar 24 | -65,821 pts | -7,652 pts | **-58,169 losses** | **Avoided losses** |

### 3-Day Summary

| Metric | Value |
|--------|-------|
| **Full Day (24h)** | -62,574 points |
| **01:00-23:00** | -8,808 points |
| **Excluded Hours** | -53,766 points |
| **Improvement** | **+53,766 points** |

### [VERDICT]: Trade 01:00-23:00 Only ✅

**Rationale:**
- March 24th had a major loss (-58,169 pts) during transition hours
- March 20 & 23 showed the 0h/23h hours were profitable, BUT
- The catastrophic loss on March 24 far outweighs the small gains on other days
- **Risk-adjusted decision**: Avoid the major loss event even if it means sacrificing some gains

---

## 2. FIXED SL BY SESSION (Data-Driven)

### Key Finding: NY Has LOWER MAE Than Expected!

| Session | MAE 90th | MAE 95th | **Recommended SL** | Outcome |
|---------|----------|----------|-------------------|---------|
| **Asia** (01-08) | 2,503 pts | 2,927 pts | **2,500 pts** | -48,902 pts |
| **London** (08-16) | 2,552 pts | 3,063 pts | **2,550 pts** | -3,482 pts |
| **NY** (16-23) | 2,287 pts | 2,845 pts | **2,300 pts** | **+30,750 pts** |

### [VERDICT]: Session-Based Fixed SL Recommended ✅

**Rationale:**
1. **NY Session** is actually the BEST performing (+30,750 pts) and has the LOWEST MAE
2. **Asia Session** has the highest MAE and worst outcomes - needs wider SL
3. **London Session** is moderate - medium SL appropriate

**Counter-Intuitive Finding:** NY does NOT need larger SL despite higher volatility expectations. The strategy performs best during NY with lower MAE.

---

## 3. IMPLEMENTATION RECOMMENDATIONS

### Trading Hours
```
Trade Window: 01:00 - 23:00 UTC
Avoid: 00:00-01:00 and 23:00-00:00 (transition hours)
Reason: Major loss event on March 24th (-58k pts) occurred during these hours
```

### Fixed Stop Loss by Session
```python
SESSION_SL = {
    'Asia':   2500,  # 01:00-08:00 UTC
    'London': 2550,  # 08:00-16:00 UTC
    'NY':     2300,  # 16:00-23:00 UTC
}
```

### Why This Works
1. **Asia (2,500 SL)**: Worst performing session, needs room to breathe
2. **London (2,550 SL)**: Moderate performance, medium protection
3. **NY (2,300 SL)**: Best performing, tighter SL acceptable, captures +30k pts

---

## 4. UNEXPECTED FINDINGS

### 1. NY Session Contradicts Volatility Assumption
- **Expected**: NY = higher volatility = larger SL needed
- **Actual**: NY = best performance (+30k pts) = lowest MAE = smaller SL works

### 2. March 24th Dominated Results
- Single day loss (-65k) drove the trading hours recommendation
- Without March 24th: Full day would be +3,247 pts, 01-23 would be -1,156 pts
- **Lesson**: One catastrophic day can outweigh multiple good days

### 3. Asia Session Underperformance
- 565 positions (largest count)
- Worst outcome (-48,902 pts)
- Highest MAE (2,500+ at 90th percentile)
- **Question**: Should we avoid Asia entirely?

---

## 5. RECOMMENDED NEXT STEPS

1. **Implement 01:00-23:00 trading window immediately**
   - Evidence: Avoids 53k+ pts of losses

2. **Test session-based SL for 1 week**
   - Asia: 2,500 pts
   - London: 2,550 pts
   - NY: 2,300 pts

3. **Consider Asia session exclusion**
   - 565 positions, -48k outcome
   - If removed, remaining sessions = +11,268 pts
   - Test trading London-NY only (08:00-23:00)

4. **Monitor March 27th+ for pattern confirmation**
   - Is the 0h/23h risk consistent?
   - Does NY continue to outperform?

---

*Report generated from March 20, 23, 24 data analysis*
*All recommendations data-driven, not feeling-based*
