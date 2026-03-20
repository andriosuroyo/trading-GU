//+------------------------------------------------------------------+
//|                                          GUM_PositionManager.mqh |
//|                              Position tracking and state machine |
//+------------------------------------------------------------------+
#ifndef GUM_POSITIONMANAGER_MQH
#define GUM_POSITIONMANAGER_MQH

#include "GUM_Structures.mqh"
#include "GUM_CSVManager.mqh"

//+------------------------------------------------------------------+
//| Position Manager Class                                            |
//+------------------------------------------------------------------+
class CGUM_PositionManager
{
private:
   // Settings
   ENUM_GUM_FILTER_METHOD m_filterMethod;
   string                 m_filterValue;
   ENUM_GUM_DURATION_TYPE m_durationType;
   int                    m_durationValue;
   int                    m_durationSeconds;
   bool                   m_useTrailing;
   double                 m_trailDistance;
   SRecoveryHours         m_recoveryHours;
   
   // References
   CGUM_CSVManager*       m_csvManager;
   
   // Position storage
   SPositionRecord        m_activePositions[];   // Currently open positions
   SPositionRecord        m_recoveryPositions[]; // Positions in RECOVERY state (monitoring)
   SPositionRecord        m_historyPositions[];  // RECOVERED or LOST positions
   
   // Tracking for closed positions we need to process
   ulong                  m_lastKnownTickets[];
   
public:
   // Constructor
   CGUM_PositionManager()
   {
      m_filterMethod = GUM_FILTER_MAGIC;
      m_filterValue = "";
      m_durationType = GUM_DURATION_MINUTES;
      m_durationValue = 5;
      m_durationSeconds = 300;
      m_useTrailing = false;
      m_trailDistance = 0;
      m_csvManager = NULL;
      ArrayResize(m_activePositions, 0);
      ArrayResize(m_recoveryPositions, 0);
      ArrayResize(m_historyPositions, 0);
      ArrayResize(m_lastKnownTickets, 0);
   }
   
   // Initialize with settings
   void Initialize(
      ENUM_GUM_FILTER_METHOD filterMethod,
      string filterValue,
      ENUM_GUM_DURATION_TYPE durationType,
      int durationValue,
      bool useTrailing,
      double trailDistance,
      SRecoveryHours &hours,
      CGUM_CSVManager* csvManager
   )
   {
      m_filterMethod = filterMethod;
      m_filterValue = filterValue;
      m_durationType = durationType;
      m_durationValue = durationValue;
      m_durationSeconds = DurationToSeconds(durationType, durationValue);
      m_useTrailing = useTrailing;
      m_trailDistance = trailDistance;
      m_recoveryHours = hours;
      m_csvManager = csvManager;
      
      Print("GUM Position Manager initialized:");
      Print("  Filter: ", m_filterMethod == GUM_FILTER_MAGIC ? "Magic" : 
                     m_filterMethod == GUM_FILTER_COMMENT ? "Comment" : "Symbol",
            " = ", m_filterValue);
      Print("  Duration: ", m_durationValue, " ", 
            m_durationType == GUM_DURATION_SECONDS ? "seconds" :
            m_durationType == GUM_DURATION_MINUTES ? "minutes" : "hours");
      Print("  Recovery Hours - Asia:", m_recoveryHours.Asia, 
            " London:", m_recoveryHours.London,
            " NY:", m_recoveryHours.NY,
            " Full:", m_recoveryHours.Full);
   }
   
   // Load recovery positions from CSV (positions still being monitored)
   void LoadRecoveryPositions(CGUM_CSVManager* csvManager)
   {
      if(csvManager == NULL) return;
      
      SPositionRecord allPositions[];
      int count = csvManager.ReadAllPositions(allPositions);
      
      int recoveryCount = 0;
      for(int i = 0; i < count; i++)
      {
         if(allPositions[i].Status == GUM_STATUS_RECOVERY)
         {
            int size = ArraySize(m_recoveryPositions);
            ArrayResize(m_recoveryPositions, size + 1);
            m_recoveryPositions[size] = allPositions[i];
            recoveryCount++;
         }
         else if(allPositions[i].Status == GUM_STATUS_RECOVERED || 
                 allPositions[i].Status == GUM_STATUS_LOST)
         {
            int size = ArraySize(m_historyPositions);
            ArrayResize(m_historyPositions, size + 1);
            m_historyPositions[size] = allPositions[i];
         }
      }
      
      Print("Loaded ", recoveryCount, " recovery positions to monitor");
   }
   
   // Main processing function - call every tick/second
   void ProcessPositions()
   {
      // 1. Process active (open) positions
      ProcessActivePositions();
      
      // 2. Process recovery positions (monitoring)
      ProcessRecoveryPositions();
      
      // 3. Check for positions that were closed externally
      CheckForClosedPositions();
   }
   
   // Process active positions (from MT5)
   void ProcessActivePositions()
   {
      int total = PositionsTotal();
      static int lastReportedTotal = -1;
      
      // Report position count changes
      if(total != lastReportedTotal)
      {
         Print("TCM DEBUG: Found ", total, " total positions");
         lastReportedTotal = total;
      }
      
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         
         // Check if this position matches our filter
         bool success;
         SPositionRecord rec;
         PopulatePositionFromMT5(ticket, rec, success);
         if(!success) continue;
         
         // Debug: Check if new position
         if(FindActivePosition(ticket) < 0)
         {
            Print("TCM DEBUG: Checking position #", ticket, 
                  " Magic=", rec.MagicNumber, 
                  " Symbol=", rec.Symbol,
                  " FilterMatch=", rec.MatchesFilter(m_filterMethod, m_filterValue));
         }
         
         if(!rec.MatchesFilter(m_filterMethod, m_filterValue)) continue;
         
         // Check if we're already tracking this position
         int existingIdx = FindActivePosition(ticket);
         
         if(existingIdx >= 0)
         {
            // Update existing position
            UpdateActivePosition(existingIdx, rec);
         }
         else
         {
            // New position - add to tracking
            AddNewPosition(rec);
         }
      }
   }
   
   // Process recovery positions (monitor for recovery or timeout)
   void ProcessRecoveryPositions()
   {
      datetime now = TimeCurrent();
      
      for(int i = ArraySize(m_recoveryPositions) - 1; i >= 0; i--)
      {
         SPositionRecord rec = m_recoveryPositions[i];
         
         // Get recovery time limit for this session
         int recoveryHours = GetRecoveryHoursForSession(rec.Session, m_recoveryHours);
         datetime recoveryDeadline = rec.TimeClose + (recoveryHours * 3600);
         
         // Check if exceeded time limit -> LOST
         if(now > recoveryDeadline)
         {
            m_recoveryPositions[i].Status = GUM_STATUS_LOST;
            m_recoveryPositions[i].StatusChangedTime = now;
            
            Print("Position #", rec.Ticket, " marked as LOST (exceeded ", recoveryHours, " hours)");
            
            // Move to history
            MoveRecoveryToHistory(i);
            continue;
         }
         
         // Check if price recovered -> RECOVERED
         if(CheckPriceRecovered(rec))
         {
            m_recoveryPositions[i].Status = GUM_STATUS_RECOVERED;
            m_recoveryPositions[i].StatusChangedTime = now;
            m_recoveryPositions[i].TimeRecovered = now;
            
            Print("Position #", rec.Ticket, " marked as RECOVERED at ", SymbolInfoDouble(rec.Symbol, SYMBOL_BID));
            
            // Move to history (removed from recovery monitor)
            MoveRecoveryToHistory(i);
            continue;
         }
      }
   }
   
   // Check if price has recovered for a position
   bool CheckPriceRecovered(SPositionRecord &rec)
   {
      double currentPrice = (rec.Type == POSITION_TYPE_BUY) ? 
                           SymbolInfoDouble(rec.Symbol, SYMBOL_BID) :
                           SymbolInfoDouble(rec.Symbol, SYMBOL_ASK);
      
      if(rec.Type == POSITION_TYPE_BUY)
      {
         // For BUY: recovered when price >= PriceOpen
         return (currentPrice >= rec.PriceOpen);
      }
      else
      {
         // For SELL: recovered when price <= PriceOpen
         return (currentPrice <= rec.PriceOpen);
      }
   }
   
   // Check for positions that were closed externally
   void CheckForClosedPositions()
   {
      // Build list of currently open tickets
      bool openTickets[];
      ArrayResize(openTickets, 100000); // Max reasonable ticket number
      ArrayInitialize(openTickets, false);
      
      int total = PositionsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket < (ulong)ArraySize(openTickets))
            openTickets[(int)ticket] = true;
      }
      
      // Check our active positions
      for(int i = ArraySize(m_activePositions) - 1; i >= 0; i--)
      {
         ulong ticket = m_activePositions[i].Ticket;
         
         // If ticket is not open anymore, it was closed
         if(ticket >= (ulong)ArraySize(openTickets) || !openTickets[(int)ticket])
         {
            HandlePositionClosed(m_activePositions[i]);
            RemoveActivePosition(i);
         }
      }
      
      // Update last known tickets
      ArrayResize(m_lastKnownTickets, 0);
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         int size = ArraySize(m_lastKnownTickets);
         ArrayResize(m_lastKnownTickets, size + 1);
         m_lastKnownTickets[size] = ticket;
      }
   }
   
   // Handle a position that was closed
   void HandlePositionClosed(SPositionRecord &rec)
   {
      // Get close details from history
      if(HistorySelect(rec.TimeOpen, TimeCurrent()))
      {
         int deals = HistoryDealsTotal();
         for(int i = 0; i < deals; i++)
         {
            ulong dealTicket = HistoryDealGetTicket(i);
            if(HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID) == rec.Ticket)
            {
               rec.TimeClose = (datetime)HistoryDealGetInteger(dealTicket, DEAL_TIME);
               rec.PriceClose = HistoryDealGetDouble(dealTicket, DEAL_PRICE);
               rec.Profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
               break;
            }
         }
      }
      
      // Determine if it was CLEAR or RECOVERY based on final P&L
      if(rec.ShouldBeClear())
      {
         // CLEAR: Profit OR small loss (< $0.50 per 0.01)
         rec.Status = GUM_STATUS_CLEAR;
         if(rec.Profit >= 0)
            Print("Position #", rec.Ticket, " closed as CLEAR (profit: $", rec.Profit, ")");
         else
            Print("Position #", rec.Ticket, " closed as CLEAR (small loss: $", rec.Profit, ", likely slippage)");
      }
      else
      {
         // RECOVERY: Loss >= $0.50 per 0.01 - did not hit TrailStart
         rec.Status = GUM_STATUS_RECOVERY;
         rec.StatusChangedTime = TimeCurrent();
         
         Print("Position #", rec.Ticket, " closed as RECOVERY (loss: $", rec.Profit, ", did not hit TrailStart)");
         
         // Add to recovery monitoring
         int size = ArraySize(m_recoveryPositions);
         ArrayResize(m_recoveryPositions, size + 1);
         m_recoveryPositions[size] = rec;
      }
      
      // Save to CSV
      if(m_csvManager != NULL)
         m_csvManager.UpdatePosition(rec);
   }
   
   // Populate position record from MT5
   void PopulatePositionFromMT5(ulong ticket, SPositionRecord &rec, bool &success)
   {
      rec.Initialize();
      success = false;
      
      if(!PositionSelectByTicket(ticket)) return;
      
      rec.Ticket = ticket;
      rec.Symbol = PositionGetString(POSITION_SYMBOL);
      rec.Type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      rec.Comment = PositionGetString(POSITION_COMMENT);
      rec.MagicNumber = PositionGetInteger(POSITION_MAGIC);
      rec.TimeOpen = (datetime)PositionGetInteger(POSITION_TIME);
      rec.PriceOpen = PositionGetDouble(POSITION_PRICE_OPEN);
      rec.LotSize = PositionGetDouble(POSITION_VOLUME);
      rec.LotSizeNormalized = rec.CalculateNormalizedLots();
      rec.Profit = PositionGetDouble(POSITION_PROFIT);
      
      // Calculate cutoff time
      rec.CutoffTime = rec.TimeOpen + m_durationSeconds;
      
      // Detect session
      rec.DetectSession();
      
      success = true;
   }
   
   // Find position in active array
   int FindActivePosition(ulong ticket)
   {
      int count = ArraySize(m_activePositions);
      for(int i = 0; i < count; i++)
      {
         if(m_activePositions[i].Ticket == ticket)
            return i;
      }
      return -1;
   }
   
   // Add new position
   void AddNewPosition(SPositionRecord &rec)
   {
      int size = ArraySize(m_activePositions);
      ArrayResize(m_activePositions, size + 1);
      m_activePositions[size] = rec;
      
      Print("New position added #", rec.Ticket, " ", rec.Symbol, " ", rec.GetTypeString(),
            " Open:", rec.PriceOpen, " Lots:", rec.LotSize,
            " Cutoff:", TimeToString(rec.CutoffTime, TIME_MINUTES|TIME_SECONDS));
      
      // Save to CSV
      if(m_csvManager != NULL)
         m_csvManager.WritePosition(rec);
   }
   
   // Update existing active position
   void UpdateActivePosition(int idx, SPositionRecord &updated)
   {
      // Update mutable fields
      m_activePositions[idx].Profit = updated.Profit;
      m_activePositions[idx].MaxProfitPrice = CalculateMaxProfitPrice(idx);
      
      // Note: Status remains OPEN while position is active
      // CLEAR vs RECOVERY is determined AFTER the position closes
      // based on final P&L (see HandlePositionClosed)
      
      // Check for time cutoff
      CheckTimeCutoff(idx);
   }
   
   // Calculate max profit price for trailing
   double CalculateMaxProfitPrice(int idx)
   {
      SPositionRecord rec = m_activePositions[idx];
      double currentPrice = (rec.Type == POSITION_TYPE_BUY) ?
                           SymbolInfoDouble(rec.Symbol, SYMBOL_BID) :
                           SymbolInfoDouble(rec.Symbol, SYMBOL_ASK);
      
      if(rec.Type == POSITION_TYPE_BUY)
      {
         // For BUY, higher price is better
         return MathMax(rec.MaxProfitPrice, currentPrice);
      }
      else
      {
         // For SELL, lower price is better
         if(rec.MaxProfitPrice == 0) return currentPrice;
         return MathMin(rec.MaxProfitPrice, currentPrice);
      }
   }
   
   // Check if position should be closed due to time cutoff
   void CheckTimeCutoff(int idx)
   {
      SPositionRecord rec = m_activePositions[idx];
      datetime now = TimeCurrent();
      
      // Debug: Log when approaching cutoff
      int secondsRemaining = (int)(rec.CutoffTime - now);
      if(secondsRemaining <= 60 && secondsRemaining > 0 && secondsRemaining % 10 == 0)
      {
         Print("TCM DEBUG: Position #", rec.Ticket, " cutoff in ", secondsRemaining, "s");
      }
      
      if(now < rec.CutoffTime) return; // Not yet at cutoff
      
      Print("TCM DEBUG: CUTOFF REACHED for #", rec.Ticket, 
            " OpenTime=", TimeToString(rec.TimeOpen, TIME_MINUTES|TIME_SECONDS),
            " CutoffTime=", TimeToString(rec.CutoffTime, TIME_MINUTES|TIME_SECONDS),
            " Now=", TimeToString(now, TIME_MINUTES|TIME_SECONDS));
      
      // Cutoff reached
      if(!rec.IsTrailing)
      {
         if(m_useTrailing && m_trailDistance > 0)
         {
            // Enter trailing mode
            m_activePositions[idx].IsTrailing = true;
            m_activePositions[idx].MaxProfitPrice = (rec.Type == POSITION_TYPE_BUY) ?
                                 SymbolInfoDouble(rec.Symbol, SYMBOL_BID) :
                                 SymbolInfoDouble(rec.Symbol, SYMBOL_ASK);
            Print("Position #", rec.Ticket, " entered trailing mode at cutoff");
         }
         else
         {
            // Close position immediately
            Print("TCM DEBUG: Attempting to close position #", rec.Ticket);
            ClosePosition(rec);
         }
      }
      else
      {
         // Already in trailing mode - check if should close
         CheckTrailingStop(idx);
      }
   }
   
   // Check trailing stop
   void CheckTrailingStop(int idx)
   {
      SPositionRecord rec = m_activePositions[idx];
      if(!rec.IsTrailing) return;
      
      double currentPrice = (rec.Type == POSITION_TYPE_BUY) ?
                           SymbolInfoDouble(rec.Symbol, SYMBOL_BID) :
                           SymbolInfoDouble(rec.Symbol, SYMBOL_ASK);
      
      double trailPoints = m_trailDistance * SymbolInfoDouble(rec.Symbol, SYMBOL_POINT);
      bool shouldClose = false;
      
      if(rec.Type == POSITION_TYPE_BUY)
      {
         // For BUY: close if price drops below max - trail
         if(currentPrice < rec.MaxProfitPrice - trailPoints)
            shouldClose = true;
      }
      else
      {
         // For SELL: close if price rises above min + trail
         if(currentPrice > rec.MaxProfitPrice + trailPoints)
            shouldClose = true;
      }
      
      if(shouldClose)
      {
         Print("Position #", rec.Ticket, " trailing stop triggered");
         ClosePosition(rec);
      }
      else
      {
         // Update max profit
         if(rec.Type == POSITION_TYPE_BUY)
            m_activePositions[idx].MaxProfitPrice = MathMax(rec.MaxProfitPrice, currentPrice);
         else
            m_activePositions[idx].MaxProfitPrice = MathMin(rec.MaxProfitPrice, currentPrice);
      }
   }
   
   // Close a position
   void ClosePosition(SPositionRecord &rec)
   {
      Print("TCM DEBUG: ClosePosition START - Ticket #", rec.Ticket, 
            " Symbol=", rec.Symbol, " Type=", rec.GetTypeString(),
            " Volume=", rec.LotSize);
      
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_DEAL;
      request.position = rec.Ticket;
      request.symbol = rec.Symbol;
      request.volume = rec.LotSize;
      request.deviation = 10;
      request.magic = rec.MagicNumber;
      
      if(rec.Type == POSITION_TYPE_BUY)
      {
         request.type = ORDER_TYPE_SELL;
         request.price = SymbolInfoDouble(rec.Symbol, SYMBOL_BID);
      }
      else
      {
         request.type = ORDER_TYPE_BUY;
         request.price = SymbolInfoDouble(rec.Symbol, SYMBOL_ASK);
      }
      
      Print("TCM DEBUG: OrderSend - Action=", request.action, 
            " Type=", request.type, " Symbol=", request.symbol,
            " Volume=", request.volume, " Price=", request.price,
            " PositionID=", request.position);
      
      if(!OrderSend(request, result))
      {
         int error = GetLastError();
         Print("TCM ERROR: OrderSend failed for #", rec.Ticket, ", error: ", error);
         return;
      }
      
      if(result.retcode == TRADE_RETCODE_DONE)
      {
         Print("TCM SUCCESS: Position #", rec.Ticket, " closed at ", result.price);
      }
      else
      {
         Print("TCM WARNING: Position #", rec.Ticket, " retcode=", result.retcode, 
               " deal=", result.deal);
      }
      
      // Update record with close details
      rec.TimeClose = TimeCurrent();
      rec.PriceClose = result.price;
      
      // Note: The actual status (CLEAR or RECOVERY) will be determined in HandlePositionClosed
      // which will be called on next tick when we detect the position is no longer open
   }
   
   // Remove position from active array
   void RemoveActivePosition(int idx)
   {
      int count = ArraySize(m_activePositions);
      if(idx < 0 || idx >= count) return;
      
      // Shift elements
      for(int i = idx; i < count - 1; i++)
      {
         m_activePositions[i] = m_activePositions[i + 1];
      }
      
      ArrayResize(m_activePositions, count - 1);
   }
   
   // Move position from recovery to history
   void MoveRecoveryToHistory(int idx)
   {
      if(idx < 0 || idx >= ArraySize(m_recoveryPositions)) return;
      
      // Add to history
      int histSize = ArraySize(m_historyPositions);
      ArrayResize(m_historyPositions, histSize + 1);
      m_historyPositions[histSize] = m_recoveryPositions[idx];
      
      // Update CSV
      if(m_csvManager != NULL)
         m_csvManager.UpdatePosition(m_recoveryPositions[idx]);
      
      // Remove from recovery array
      int recSize = ArraySize(m_recoveryPositions);
      for(int i = idx; i < recSize - 1; i++)
      {
         m_recoveryPositions[i] = m_recoveryPositions[i + 1];
      }
      ArrayResize(m_recoveryPositions, recSize - 1);
   }
   
   // Save all positions to CSV
   void SaveAllPositions(CGUM_CSVManager* csvManager)
   {
      // Combine all arrays
      SPositionRecord allPositions[];
      int count = 0;
      
      // Add active
      int activeCount = ArraySize(m_activePositions);
      for(int i = 0; i < activeCount; i++)
      {
         ArrayResize(allPositions, count + 1);
         allPositions[count] = m_activePositions[i];
         count++;
      }
      
      // Add recovery
      int recoveryCount = ArraySize(m_recoveryPositions);
      for(int i = 0; i < recoveryCount; i++)
      {
         ArrayResize(allPositions, count + 1);
         allPositions[count] = m_recoveryPositions[i];
         count++;
      }
      
      // Add history
      int historyCount = ArraySize(m_historyPositions);
      for(int i = 0; i < historyCount; i++)
      {
         ArrayResize(allPositions, count + 1);
         allPositions[count] = m_historyPositions[i];
         count++;
      }
      
      // Write all
      if(csvManager != NULL)
         csvManager.WriteAllPositions(allPositions);
      Print("Saved ", count, " positions to CSV");
   }
   
   // Getters - returns array by copying (MQL5 doesn't support array references)
   void GetActivePositions(SPositionRecord &positions[]) 
   { 
      ArrayResize(positions, ArraySize(m_activePositions));
      for(int i = 0; i < ArraySize(m_activePositions); i++)
         positions[i] = m_activePositions[i];
   }
   void GetRecoveryPositions(SPositionRecord &positions[]) 
   { 
      ArrayResize(positions, ArraySize(m_recoveryPositions));
      for(int i = 0; i < ArraySize(m_recoveryPositions); i++)
         positions[i] = m_recoveryPositions[i];
   }
   int GetActiveCount() { return ArraySize(m_activePositions); }
   int GetRecoveryCount() { return ArraySize(m_recoveryPositions); }
   int GetHistoryCount() { return ArraySize(m_historyPositions); }
   
   // Get statistics
   void GetStatistics(int &total, int &open, int &clear, int &recovery, int &recovered, int &lost)
   {
      total = ArraySize(m_activePositions) + ArraySize(m_recoveryPositions) + ArraySize(m_historyPositions);
      open = 0;
      clear = 0;
      recovery = ArraySize(m_recoveryPositions);
      recovered = 0;
      lost = 0;
      
      for(int i = 0; i < ArraySize(m_activePositions); i++)
      {
         if(m_activePositions[i].Status == GUM_STATUS_OPEN)
            open++;
         else if(m_activePositions[i].Status == GUM_STATUS_CLEAR)
            clear++;
      }
      
      for(int i = 0; i < ArraySize(m_historyPositions); i++)
      {
         if(m_historyPositions[i].Status == GUM_STATUS_RECOVERED)
            recovered++;
         else if(m_historyPositions[i].Status == GUM_STATUS_LOST)
            lost++;
         else if(m_historyPositions[i].Status == GUM_STATUS_CLEAR)
            clear++;
      }
   }
};

#endif // GUM_POSITIONMANAGER_MQH
//+------------------------------------------------------------------+
