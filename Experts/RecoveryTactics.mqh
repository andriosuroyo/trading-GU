//+------------------------------------------------------------------+
//|                                            RecoveryTactics.mqh  |
//|                  Recovery Strategy Framework for Losses           |
//|                                                                   |
//|  This header provides recovery tactics that can be integrated     |
//|  with the TimeCutoffManager or used standalone                    |
//+------------------------------------------------------------------+

#ifndef RECOVERY_TACTICS_MQH
#define RECOVERY_TACTICS_MQH

#include <Trade\Trade.mqh>

//--- Recovery Strategy Types
enum ENUM_RECOVERY_STRATEGY
{
    RECOVERY_NONE,           // No recovery, just track losses
    RECOVERY_MARTINGALE,     // Double lot size after loss
    RECOVERY_FIBONACCI,      // Fibonacci lot progression
    RECOVERY_FIXED_STEP,     // Fixed lot increment
    RECOVERY_PROFIT_TARGET,  // Increase target to cover loss
    RECOVERY_HYBRID          // Combination of above
};

//--- Recovery State
struct RecoveryState
{
    double   baseLotSize;        // Original lot size
    double   currentLotSize;     // Current lot size for recovery
    double   totalLoss;          // Accumulated loss to recover
    double   recoveredAmount;    // Amount already recovered
    int      recoveryLevel;      // Current recovery level (0 = base)
    datetime lastLossTime;       // Time of last loss
    bool     inRecoveryMode;     // Currently in recovery
    double   targetProfit;       // Target profit including recovery
    ulong    recoveryTradeTicket; // Ticket of current recovery trade
};

//+------------------------------------------------------------------+
//| Recovery Calculator Class                                        |
//+------------------------------------------------------------------+
class CRecoveryCalculator
{
private:
    RecoveryState m_state;
    ENUM_RECOVERY_STRATEGY m_strategy;
    
    // Parameters
    double   m_maxLotSize;
    double   m_maxRiskPercent;
    int      m_maxRecoveryLevels;
    double   m_recoveryMultiplier;
    
public:
    // Constructor
    CRecoveryCalculator(ENUM_RECOVERY_STRATEGY strategy = RECOVERY_MARTINGALE)
    {
        m_strategy = strategy;
        Reset();
        
        // Default parameters
        m_maxLotSize = 10.0;
        m_maxRiskPercent = 5.0;
        m_maxRecoveryLevels = 5;
        m_recoveryMultiplier = 1.5;
    }
    
    // Set parameters
    void SetMaxLotSize(double maxLot) { m_maxLotSize = maxLot; }
    void SetMaxRiskPercent(double riskPct) { m_maxRiskPercent = riskPct; }
    void SetMaxRecoveryLevels(int maxLevels) { m_maxRecoveryLevels = maxLevels; }
    void SetRecoveryMultiplier(double multiplier) { m_recoveryMultiplier = multiplier; }
    void SetBaseLotSize(double baseLot) { m_state.baseLotSize = baseLot; }
    
    // Record a loss
    void RecordLoss(double loss, double lotSize)
    {
        if(loss >= 0) return; // Only record actual losses
        
        m_state.totalLoss += MathAbs(loss);
        m_state.lastLossTime = TimeCurrent();
        m_state.inRecoveryMode = true;
        m_state.recoveryLevel++;
        
        CalculateNextTradeSize();
        CalculateTargetProfit();
    }
    
    // Record a win (partial or full recovery)
    void RecordWin(double profit)
    {
        m_state.recoveredAmount += profit;
        
        // Check if fully recovered
        if(m_state.recoveredAmount >= m_state.totalLoss)
        {
            // Full recovery achieved
            double excess = m_state.recoveredAmount - m_state.totalLoss;
            Print("Full recovery achieved! Excess: $", DoubleToString(excess, 2));
            Reset();
        }
        else
        {
            // Partial recovery - continue
            m_state.totalLoss -= profit;
            CalculateNextTradeSize();
            CalculateTargetProfit();
        }
    }
    
    // Calculate next trade lot size based on strategy
    double CalculateNextTradeSize()
    {
        if(!m_state.inRecoveryMode)
            return m_state.baseLotSize;
        
        double nextLot = m_state.baseLotSize;
        
        switch(m_strategy)
        {
            case RECOVERY_MARTINGALE:
                // Double the previous lot size
                nextLot = m_state.baseLotSize * MathPow(2, m_state.recoveryLevel);
                break;
                
            case RECOVERY_FIBONACCI:
                // Fibonacci sequence: 1, 1, 2, 3, 5, 8, 13...
                {
                    double fib[] = {1, 1, 2, 3, 5, 8, 13, 21, 34};
                    int idx = MathMin(m_state.recoveryLevel, ArraySize(fib) - 1);
                    nextLot = m_state.baseLotSize * fib[idx];
                }
                break;
                
            case RECOVERY_FIXED_STEP:
                // Add fixed increment each level
                nextLot = m_state.baseLotSize + (m_state.baseLotSize * 0.5 * m_state.recoveryLevel);
                break;
                
            case RECOVERY_PROFIT_TARGET:
                // Keep same lot, increase target
                nextLot = m_state.baseLotSize;
                break;
                
            case RECOVERY_HYBRID:
                // Moderate increase with compounding
                nextLot = m_state.baseLotSize * MathPow(m_recoveryMultiplier, m_state.recoveryLevel);
                break;
                
            default:
                nextLot = m_state.baseLotSize;
        }
        
        // Apply limits
        nextLot = NormalizeDouble(nextLot, 2);
        nextLot = MathMin(nextLot, m_maxLotSize);
        
        m_state.currentLotSize = nextLot;
        return nextLot;
    }
    
    // Calculate target profit including recovery
    double CalculateTargetProfit()
    {
        if(!m_state.inRecoveryMode)
        {
            m_state.targetProfit = 0; // Normal operation
            return 0;
        }
        
        // Base target is to recover remaining loss
        double baseTarget = m_state.totalLoss;
        
        // Add some profit buffer
        double profitBuffer = baseTarget * 0.1; // 10% buffer
        
        m_state.targetProfit = baseTarget + profitBuffer;
        
        return m_state.targetProfit;
    }
    
    // Get current state info
    double GetCurrentLotSize() const { return m_state.currentLotSize; }
    double GetTargetProfit() const { return m_state.targetProfit; }
    double GetTotalLoss() const { return m_state.totalLoss; }
    double GetRecoveredAmount() const { return m_state.recoveredAmount; }
    double GetRemainingLoss() const { return m_state.totalLoss - m_state.recoveredAmount; }
    int GetRecoveryLevel() const { return m_state.recoveryLevel; }
    bool IsInRecoveryMode() const { return m_state.inRecoveryMode; }
    
    // Check if recovery is possible (risk limits)
    bool CanProceedWithRecovery()
    {
        if(m_state.recoveryLevel >= m_maxRecoveryLevels)
        {
            Print("Max recovery levels reached. Resetting.");
            Reset();
            return false;
        }
        
        if(m_state.currentLotSize > m_maxLotSize)
        {
            Print("Max lot size would be exceeded. Resetting.");
            Reset();
            return false;
        }
        
        // Check if total exposure is within risk limits
        // (Would need account balance info)
        
        return true;
    }
    
    // Reset recovery state
    void Reset()
    {
        m_state.totalLoss = 0;
        m_state.recoveredAmount = 0;
        m_state.recoveryLevel = 0;
        m_state.inRecoveryMode = false;
        m_state.targetProfit = 0;
        m_state.currentLotSize = m_state.baseLotSize;
    }
    
    // Get status string for dashboard
    string GetStatusString()
    {
        if(!m_state.inRecoveryMode)
            return "Normal";
        
        return StringFormat("Recovery L%d: Target $%.2f", 
               m_state.recoveryLevel, m_state.targetProfit);
    }
    
    // Save state to file
    void SaveState(string filename)
    {
        int handle = FileOpen(filename, FILE_WRITE|FILE_BIN|FILE_COMMON);
        if(handle != INVALID_HANDLE)
        {
            FileWriteStruct(handle, m_state);
            FileClose(handle);
        }
    }
    
    // Load state from file
    void LoadState(string filename)
    {
        int handle = FileOpen(filename, FILE_READ|FILE_BIN|FILE_COMMON);
        if(handle != INVALID_HANDLE)
        {
            FileReadStruct(handle, m_state);
            FileClose(handle);
        }
    }
};

//+------------------------------------------------------------------+
//| Recovery Trade Manager                                           |
//+------------------------------------------------------------------+
class CRecoveryTradeManager
{
private:
    CTrade      m_trade;
    CRecoveryCalculator* m_recovery;
    
    string      m_symbol;
    ulong       m_currentTicket;
    bool        m_waitingForResult;
    
public:
    CRecoveryTradeManager(CRecoveryCalculator* recovery)
    {
        m_recovery = recovery;
        m_currentTicket = 0;
        m_waitingForResult = false;
        m_symbol = _Symbol;
        
        m_trade.SetExpertMagicNumber(0);
    }
    
    void SetSymbol(string symbol) { m_symbol = symbol; }
    
    // Open recovery trade
    bool OpenRecoveryTrade(int orderType, double slPoints = 0, double tpPoints = 0)
    {
        if(m_waitingForResult)
        {
            Print("Already have an open recovery trade");
            return false;
        }
        
        if(!m_recovery.CanProceedWithRecovery())
        {
            Print("Cannot proceed with recovery - limits reached");
            return false;
        }
        
        double lotSize = m_recovery.GetCurrentLotSize();
        double price = (orderType == ORDER_TYPE_BUY) ? 
                       SymbolInfoDouble(m_symbol, SYMBOL_ASK) :
                       SymbolInfoDouble(m_symbol, SYMBOL_BID);
        
        double sl = (slPoints > 0) ? 
                    ((orderType == ORDER_TYPE_BUY) ? price - slPoints * _Point : price + slPoints * _Point) :
                    0;
        
        double tp = (tpPoints > 0) ? 
                    ((orderType == ORDER_TYPE_BUY) ? price + tpPoints * _Point : price - tpPoints * _Point) :
                    0;
        
        // If recovery mode, set TP to target profit
        if(m_recovery.IsInRecoveryMode() && tp == 0)
        {
            double tickValue = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE);
            double tpPointsFromTarget = m_recovery.GetTargetProfit() / (lotSize * tickValue);
            
            tp = (orderType == ORDER_TYPE_BUY) ? 
                 price + tpPointsFromTarget * _Point :
                 price - tpPointsFromTarget * _Point;
        }
        
        string comment = "Recovery L" + IntegerToString(m_recovery.GetRecoveryLevel());
        
        bool result = false;
        if(orderType == ORDER_TYPE_BUY)
            result = m_trade.Buy(lotSize, m_symbol, price, sl, tp, comment);
        else
            result = m_trade.Sell(lotSize, m_symbol, price, sl, tp, comment);
        
        if(result)
        {
            m_currentTicket = m_trade.ResultOrder();
            m_waitingForResult = true;
            Print("Recovery trade opened: #", m_currentTicket, " Lot: ", lotSize);
        }
        
        return result;
    }
    
    // Check position result
    void CheckPositionResult()
    {
        if(!m_waitingForResult || m_currentTicket == 0)
            return;
        
        // Check if position still exists
        if(!PositionSelectByTicket(m_currentTicket))
        {
            // Position closed - get result from history
            if(HistorySelect(0, TimeCurrent()))
            {
                for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
                {
                    ulong dealTicket = HistoryDealGetTicket(i);
                    if(dealTicket == 0) continue;
                    
                    ulong posID = HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID);
                    if(posID == m_currentTicket)
                    {
                        double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
                        
                        if(profit > 0)
                        {
                            Print("Recovery trade profitable: $", DoubleToString(profit, 2));
                            m_recovery.RecordWin(profit);
                        }
                        else
                        {
                            Print("Recovery trade loss: $", DoubleToString(profit, 2));
                            m_recovery.RecordLoss(profit, m_recovery.GetCurrentLotSize());
                        }
                        
                        m_waitingForResult = false;
                        m_currentTicket = 0;
                        break;
                    }
                }
            }
        }
    }
    
    bool IsWaitingForResult() const { return m_waitingForResult; }
};

//+------------------------------------------------------------------+
//| Utility Functions                                                |
//+------------------------------------------------------------------+

// Calculate optimal lot size based on loss recovery
double CalculateOptimalRecoveryLot(double lossToRecover, double targetPoints, string symbol)
{
    double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
    double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
    
    if(tickSize == 0 || tickValue == 0) return 0;
    
    double pointsPerTick = tickSize / _Point;
    double valuePerPoint = tickValue * pointsPerTick;
    
    // Lot = Loss / (TargetPoints * ValuePerPoint)
    double lot = lossToRecover / (targetPoints * valuePerPoint);
    
    // Round to lot step
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    
    lot = MathFloor(lot / lotStep) * lotStep;
    lot = MathMax(lot, minLot);
    lot = MathMin(lot, maxLot);
    
    return lot;
}

// Get suggested recovery parameters based on loss size
void GetRecoverySuggestion(double loss, double baseLot, string &suggestion)
{
    double ratio = loss / (baseLot * 10); // Rough estimate
    
    if(ratio < 1)
        suggestion = "Standard recovery - 1-2x lot size";
    else if(ratio < 3)
        suggestion = "Moderate recovery - 2-3x lot size, extended target";
    else if(ratio < 5)
        suggestion = "Aggressive recovery - 3-5x lot size, consider splitting";
    else
        suggestion = "Major loss - Consider manual intervention or accept loss";
}

#endif // RECOVERY_TACTICS_MQH
