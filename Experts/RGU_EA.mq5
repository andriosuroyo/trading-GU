//+------------------------------------------------------------------+
//|                                                   RGU_EA.mq5     |
//|                        Recovery GU Expert Advisor - Optimized    |
//|                                   Version 3.0 (March 2026)       |
//+------------------------------------------------------------------+
#property copyright "GU Strategy"
#property version   "3.00"
#property strict

#include "GUM\GUM_Structures.mqh"

//+------------------------------------------------------------------+
//| Input Parameters - OPTIMIZED SETTINGS                            |
//+------------------------------------------------------------------+
// Filter Settings - Monitor GU positions
input string   InpGUCommentFilter = "GU_";      // Comment filter for GU positions
input string   InpGUMagicNumbers  = "0";        // 0 = all, or comma-separated list

// Recovery Entry Settings - OPTIMIZED (DO NOT CHANGE)
input double   InpATRMultiplier      = 1.0;     // ATR multiplier (1.0 = OPTIMAL)
input int      InpMaxLayers          = 3;       // Maximum layers (3 = OPTIMAL)
input bool     InpUseLayer1Immediate = false;   // IMMEDIATE ENTRY DESTROYS PROFIT - ALWAYS FALSE
input int      InpEntryDistanceMax   = 5000;    // Max entry distance (points)

// Recovery Exit Settings
input int      InpRecoveryWindowMin  = 120;     // Recovery window (minutes)
input int      InpEmergencySLPoints  = 30000;   // Emergency SL (points, 95th %ile MAE)

// Position Sizing
input double   InpLotSizePerLayer    = 0.01;    // Lot size for each recovery layer
input double   InpMaxTotalLots       = 0.05;    // Maximum total lots per basket

// CSV Output Settings
input bool     InpEnableCSVOutput    = true;    // Enable CSV output for analysis
input string   InpCSVFileName        = "rgu_baskets.csv";  // CSV filename (in MQL5/Files/)

// Dashboard Settings
input int      InpDashboardX         = 10;
input int      InpDashboardY         = 250;
input int      InpRowHeight          = 18;
input color    InpBgColor            = C'20,20,40';
input color    InpTextColor          = clrWhite;
input color    InpBuyColor           = clrLime;
input color    InpSellColor          = clrSalmon;
input color    InpActiveColor        = clrWhite;
input color    InpWarnColor          = clrYellow;
input color    InpCriticalColor      = clrRed;

//+------------------------------------------------------------------+
//| Structures                                                        |
//+------------------------------------------------------------------+
struct SRecoveryLayer
{
   int      LayerNumber;      // 1, 2, 3
   double   EntryPrice;       // Entry price
   double   Lots;             // Lot size
   datetime EntryTime;        // When layer opened
   int      PotentialPoints;  // Distance to target
   bool     IsFilled;         // True if layer is active
   
   void Initialize(int num)
   {
      LayerNumber = num;
      EntryPrice = 0;
      Lots = 0;
      EntryTime = 0;
      PotentialPoints = 0;
      IsFilled = false;
   }
};

struct SRecoveryBasket
{
   // Original position info
   ulong             OriginalTicket;
   string            Symbol;
   ENUM_POSITION_TYPE Direction;
   double            TargetPrice;       // Original open price
   double            InitialClosePrice; // Where SL hit
   datetime          SLHitTime;         // When basket created
   long              OriginalMagic;
   string            OriginalComment;
   double            ATRAtLoss;         // ATR when SL hit (points)
   
   // Layers
   SRecoveryLayer    Layers[3];         // Max 3 layers
   int               FilledLayerCount;
   double            TotalLots;
   
   // Status
   bool              IsActive;
   bool              IsRecovered;
   bool              IsLost;
   datetime          CloseTime;
   int               TotalPotential;
   
   // Tracking
   double            FurthestPrice;     // Worst price seen
   int               MaxMAE;            // Maximum adverse excursion
   
   void Initialize()
   {
      OriginalTicket = 0;
      Symbol = "";
      Direction = POSITION_TYPE_BUY;
      TargetPrice = 0;
      InitialClosePrice = 0;
      SLHitTime = 0;
      OriginalMagic = 0;
      OriginalComment = "";
      ATRAtLoss = 0;
      
      for(int i = 0; i < 3; i++)
         Layers[i].Initialize(i+1);
      
      FilledLayerCount = 0;
      TotalLots = 0;
      IsActive = false;
      IsRecovered = false;
      IsLost = false;
      CloseTime = 0;
      TotalPotential = 0;
      FurthestPrice = 0;
      MaxMAE = 0;
   }
   
   bool CanAddLayer()
   {
      return (FilledLayerCount < InpMaxLayers && IsActive && !IsRecovered && !IsLost);
   }
   
   int GetRemainingMinutes()
   {
      if(!IsActive) return 0;
      datetime expiry = SLHitTime + (InpRecoveryWindowMin * 60);
      int remaining = (int)(expiry - TimeCurrent());
      return (remaining > 0) ? remaining / 60 : 0;
   }
   
   string GetStatusString()
   {
      if(IsRecovered) return "RECOVERED";
      if(IsLost) return "LOST";
      int rem = GetRemainingMinutes();
      if(rem < 5) return "CRITICAL";
      if(rem < 30) return "WARN";
      return "ACTIVE";
   }
};

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+
SRecoveryBasket g_Baskets[50];           // Active baskets
int             g_BasketCount = 0;
datetime        g_LastGUCheck = 0;
datetime        g_LastHistoryCheck = 0;
datetime        g_LastTickCheck = 0;
ulong           g_KnownGUPositions[100]; // Track GU positions we've seen
int             g_KnownGUCount = 0;

// Dashboard objects
string          g_DashPrefix = "RGU_Dash_";

// CSV file mutex
string          g_CSVFileMutexName = "TCM_FileMutex.lock";  // Shared with TCM
#define         CSV_MUTEX_TIMEOUT_MS 5000

//+------------------------------------------------------------------+
//| File Mutex Operations (shared with TCM)
//+------------------------------------------------------------------+
bool AcquireFileMutex()
{
   datetime start = TimeLocal();
   
   while(FileIsExist(g_CSVFileMutexName, FILE_COMMON))
   {
      if(TimeLocal() - start > CSV_MUTEX_TIMEOUT_MS / 1000)
      {
         Print("ERROR: File mutex timeout. Another instance is writing.");
         return false;
      }
      Sleep(100);
   }
   
   int handle = FileOpen(g_CSVFileMutexName, FILE_WRITE|FILE_BIN|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileWriteLong(handle, TimeLocal());
      FileClose(handle);
      return true;
   }
   
   return false;
}

//+------------------------------------------------------------------+
void ReleaseFileMutex()
{
   if(FileIsExist(g_CSVFileMutexName, FILE_COMMON))
   {
      FileDelete(g_CSVFileMutexName, FILE_COMMON);
   }
}

//+------------------------------------------------------------------+
//| Write basket data to CSV file
//+------------------------------------------------------------------+
void WriteBasketToCSV(SRecoveryBasket &basket, string status)
{
   if(!InpEnableCSVOutput) return;
   
   if(!AcquireFileMutex())
   {
      Print("WARNING: Could not acquire mutex for CSV write. Basket not logged.");
      return;
   }
   
   // Check if file exists to determine if we need header
   bool fileExists = FileIsExist(InpCSVFileName, FILE_COMMON);
   
   int handle = FileOpen(InpCSVFileName, FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_SHARE_READ);
   if(handle == INVALID_HANDLE)
   {
      Print("ERROR: Could not open CSV file: ", InpCSVFileName, " Error: ", GetLastError());
      ReleaseFileMutex();
      return;
   }
   
   // Seek to end for append
   FileSeek(handle, 0, SEEK_END);
   
   // Write header if new file
   if(!fileExists)
   {
      FileWrite(handle, "BasketID", "OriginalTicket", "Direction", "TargetPrice",
                "Layer1Entry", "Layer2Entry", "Layer3Entry",
                "Layer1Lots", "Layer2Lots", "Layer3Lots",
                "OpenTime", "CloseTime", "ClosePrice", "Profit", "Status");
   }
   
   // Generate BasketID
   string basketID = "RGU_" + TimeToString(basket.SLHitTime, TIME_DATE) + "_" + IntegerToString((int)basket.OriginalTicket);
   StringReplace(basketID, ".", "");
   
   // Get direction string
   string dirStr = (basket.Direction == POSITION_TYPE_BUY) ? "BUY" : "SELL";
   
   // Get layer data
   double l1Entry = basket.Layers[0].IsFilled ? basket.Layers[0].EntryPrice : 0;
   double l2Entry = basket.Layers[1].IsFilled ? basket.Layers[1].EntryPrice : 0;
   double l3Entry = basket.Layers[2].IsFilled ? basket.Layers[2].EntryPrice : 0;
   double l1Lots  = basket.Layers[0].IsFilled ? basket.Layers[0].Lots : 0;
   double l2Lots  = basket.Layers[1].IsFilled ? basket.Layers[1].Lots : 0;
   double l3Lots  = basket.Layers[2].IsFilled ? basket.Layers[2].Lots : 0;
   
   // Get close price and profit
   double closePrice = 0;
   double profit = 0;
   
   if(basket.IsRecovered || basket.IsLost)
   {
      // Calculate actual profit from closed positions
      HistorySelect(basket.SLHitTime, TimeCurrent());
      for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = HistoryDealGetTicket(i);
         if(ticket == 0) continue;
         
         string comment = HistoryDealGetString(ticket, DEAL_COMMENT);
         if(StringFind(comment, "RGU_L") == -1) continue;
         if(StringFind(comment, basket.OriginalComment) == -1) continue;
         
         profit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         if(closePrice == 0)
            closePrice = HistoryDealGetDouble(ticket, DEAL_PRICE);
      }
   }
   else
   {
      // Active basket - use current price
      closePrice = (basket.Direction == POSITION_TYPE_BUY) ? 
                   SymbolInfoDouble(basket.Symbol, SYMBOL_BID) : 
                   SymbolInfoDouble(basket.Symbol, SYMBOL_ASK);
   }
   
   // Write row
   FileWrite(handle, basketID, basket.OriginalTicket, dirStr, basket.TargetPrice,
             l1Entry, l2Entry, l3Entry, l1Lots, l2Lots, l3Lots,
             basket.SLHitTime, basket.CloseTime, closePrice, profit, status);
   
   FileClose(handle);
   ReleaseFileMutex();
   
   Print("Basket logged to CSV: ", basketID, " | Status: ", status);
}

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("=== RGU EA v3.0 (Optimized) Starting ===");
   Print("CRITICAL: UseLayer1Immediate = ", InpUseLayer1Immediate ? "true" : "false");
   
   if(InpUseLayer1Immediate)
   {
      Alert("WARNING: Layer1 immediate entry DESTROYS profitability. Setting to FALSE.");
      // We can't change input, but we can warn the user
   }
   
   // Initialize baskets
   for(int i = 0; i < 50; i++)
      g_Baskets[i].Initialize();
   
   // Clear dashboard
   ClearDashboard();
   
   // Create dashboard
   CreateDashboard();
   
   Print("RGU EA initialized. Monitoring GU positions for recovery...");
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ClearDashboard();
   Print("=== RGU EA Stopped ===");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check for closed GU positions every 5 seconds
   if(TimeCurrent() - g_LastHistoryCheck >= 5)
   {
      CheckForGULosses();
      g_LastHistoryCheck = TimeCurrent();
   }
   
   // Check for GU confirmations every 2 seconds
   if(TimeCurrent() - g_LastGUCheck >= 2)
   {
      CheckForGUConfirmations();
      g_LastGUCheck = TimeCurrent();
   }
   
   // Check basket status every tick (for price hits)
   CheckBasketStatus();
   
   // Update dashboard every second
   static datetime lastDashUpdate = 0;
   if(TimeCurrent() - lastDashUpdate >= 1)
   {
      UpdateDashboard();
      lastDashUpdate = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Check for GU positions that hit SL                                |
//+------------------------------------------------------------------+
void CheckForGULosses()
{
   // Get history from last check
   datetime fromDate = g_LastHistoryCheck - 60; // Look back 1 minute
   
   HistorySelect(fromDate, TimeCurrent());
   int total = HistoryDealsTotal();
   
   for(int i = 0; i < total; i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0) continue;
      
      // Check if this is a GU position
      string comment = HistoryDealGetString(ticket, DEAL_COMMENT);
      if(StringFind(comment, InpGUCommentFilter) == -1) continue;
      
      // Check if already processed
      if(IsBasketExists(ticket)) continue;
      
      // Check if it's a loss
      double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
      if(profit >= 0) continue; // Skip profitable closes
      
      // Get position details
      string symbol = HistoryDealGetString(ticket, DEAL_SYMBOL);
      ENUM_DEAL_TYPE dealType = (ENUM_DEAL_TYPE)HistoryDealGetInteger(ticket, DEAL_TYPE);
      long magic = HistoryDealGetInteger(ticket, DEAL_MAGIC);
      datetime closeTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
      // For deals, use DEAL_PRICE (deals only have execution price, not separate open/close)
      double dealPrice = HistoryDealGetDouble(ticket, DEAL_PRICE);
      
      // Filter by magic if specified
      if(InpGUMagicNumbers != "0" && InpGUMagicNumbers != "")
      {
         if(!MagicNumberMatches(magic, InpGUMagicNumbers)) continue;
      }
      
      // Determine direction
      ENUM_POSITION_TYPE dir = (dealType == DEAL_TYPE_BUY) ? POSITION_TYPE_SELL : POSITION_TYPE_BUY;
      
      // Calculate ATR at close time
      double atrPoints = GetATRAtTime(symbol, closeTime);
      
      // Create recovery basket
      // Note: For a losing position, the dealPrice is where SL hit (close price equivalent)
      // We need the original open price from position history
      double originalOpenPrice = GetOriginalOpenPrice(ticket, symbol);
      if(originalOpenPrice == 0) originalOpenPrice = dealPrice; // Fallback
      CreateBasket(ticket, symbol, dir, originalOpenPrice, dealPrice, closeTime, magic, comment, atrPoints);
      
      Print("New recovery basket created for ticket #", ticket, 
            " | Dir: ", (dir == POSITION_TYPE_BUY ? "BUY" : "SELL"),
            " | ATR: ", DoubleToString(atrPoints, 1), " pts");
   }
}

//+------------------------------------------------------------------+
//| Create a new recovery basket                                      |
//+------------------------------------------------------------------+
void CreateBasket(ulong ticket, string symbol, ENUM_POSITION_TYPE dir, 
                  double targetPrice, double closePrice, datetime closeTime,
                  long magic, string comment, double atrPoints)
{
   if(g_BasketCount >= 50) return; // Max baskets
   
   SRecoveryBasket basket;
   basket.Initialize();
   
   basket.OriginalTicket = ticket;
   basket.Symbol = symbol;
   basket.Direction = dir;
   basket.TargetPrice = targetPrice;
   basket.InitialClosePrice = closePrice;
   basket.SLHitTime = closeTime;
   basket.OriginalMagic = magic;
   basket.OriginalComment = comment;
   basket.ATRAtLoss = atrPoints;
   basket.IsActive = true;
   basket.FurthestPrice = closePrice;
   
   // Initialize layers
   for(int i = 0; i < InpMaxLayers; i++)
      basket.Layers[i].Initialize(i+1);
   
   // If Layer1 immediate is enabled (NOT RECOMMENDED), enter now
   // Note: This setting DESTROYS profitability per simulation results
   if(InpUseLayer1Immediate && InpMaxLayers > 0)
   {
      OpenLayer(basket, 0, closePrice);
   }
   
   g_Baskets[g_BasketCount] = basket;
   g_BasketCount++;
}

//+------------------------------------------------------------------+
//| Check for GU confirmations and open layers                        |
//+------------------------------------------------------------------+
void CheckForGUConfirmations()
{
   for(int b = 0; b < g_BasketCount; b++)
   {
      if(!g_Baskets[b].IsActive || g_Baskets[b].IsRecovered || g_Baskets[b].IsLost)
         continue;
      
      if(!g_Baskets[b].CanAddLayer()) continue;
      
      // Get required entry distance
      double entryDistance = g_Baskets[b].ATRAtLoss * InpATRMultiplier;
      
      // Check all current GU positions for confirmation
      for(int i = 0; i < PositionsTotal(); i++)
      {
         ulong posTicket = PositionGetTicket(i);
         if(posTicket == 0) continue;
         
         // Check if it's a GU position
         string comment = PositionGetString(POSITION_COMMENT);
         if(StringFind(comment, InpGUCommentFilter) == -1) continue;
         
         // Check direction matches
         ENUM_POSITION_TYPE posDir = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         if(posDir != g_Baskets[b].Direction) continue;
         
         // Get position price
         double posPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         
         // Check distance from appropriate reference
         double referencePrice;
         if(g_Baskets[b].FilledLayerCount == 0)
         {
            // First layer: distance from TargetPrice
            referencePrice = g_Baskets[b].TargetPrice;
         }
         else
         {
            // Additional layers: distance from last filled layer
            referencePrice = g_Baskets[b].Layers[g_Baskets[b].FilledLayerCount - 1].EntryPrice;
         }
         
         // Check distance
         double distance = 0;
         if(g_Baskets[b].Direction == POSITION_TYPE_BUY)
         {
            // For BUY: position must be lower (better price)
            distance = referencePrice - posPrice;
         }
         else
         {
            // For SELL: position must be higher (better price)
            distance = posPrice - referencePrice;
         }
         
         // Convert to points
         int distancePoints = (int)(distance / _Point);
         
         // Check if meets entry criteria
         if(distancePoints >= (int)entryDistance && distancePoints <= InpEntryDistanceMax)
         {
            // Open the layer
            OpenLayer(g_Baskets[b], g_Baskets[b].FilledLayerCount, posPrice);
            
            Print("Layer ", g_Baskets[b].FilledLayerCount, " opened for basket ", b,
                  " | Entry: ", DoubleToString(posPrice, 2),
                  " | Distance: ", distancePoints, " pts");
            
            // Update basket in array
            g_Baskets[b].FilledLayerCount++;
            
            // Only one layer per check
            break;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Open a recovery layer                                             |
//+------------------------------------------------------------------+
void OpenLayer(SRecoveryBasket &basket, int layerIdx, double price)
{
   if(layerIdx >= InpMaxLayers) return;
   
   // Check lot limits
   if(basket.TotalLots + InpLotSizePerLayer > InpMaxTotalLots)
   {
      Print("Max lots reached for basket, skipping layer ", layerIdx + 1);
      return;
   }
   
   // Fill layer info
   basket.Layers[layerIdx].EntryPrice = price;
   basket.Layers[layerIdx].Lots = InpLotSizePerLayer;
   basket.Layers[layerIdx].EntryTime = TimeCurrent();
   basket.Layers[layerIdx].IsFilled = true;
   
   // Calculate potential
   double targetDist = MathAbs(basket.TargetPrice - price);
   basket.Layers[layerIdx].PotentialPoints = (int)(targetDist / _Point);
   
   // Update totals
   basket.TotalLots += InpLotSizePerLayer;
   basket.TotalPotential += basket.Layers[layerIdx].PotentialPoints;
   
   // Open actual trade
   ENUM_ORDER_TYPE orderType = (basket.Direction == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = basket.Symbol;
   request.volume = InpLotSizePerLayer;
   request.type = orderType;
   request.deviation = 10;
   request.magic = 999900 + (int)basket.OriginalTicket; // Unique magic
   request.comment = "RGU_L" + IntegerToString(layerIdx+1) + "_" + basket.OriginalComment;
   
   // For market orders, set price to current
   if(orderType == ORDER_TYPE_BUY)
      request.price = SymbolInfoDouble(basket.Symbol, SYMBOL_ASK);
   else
      request.price = SymbolInfoDouble(basket.Symbol, SYMBOL_BID);
   
   if(!OrderSend(request, result))
   {
      Print("Error opening layer: ", GetLastError());
   }
   else
   {
      Print("Layer ", layerIdx+1, " opened: #", result.order, 
            " | Lots: ", InpLotSizePerLayer,
            " | Potential: ", basket.Layers[layerIdx].PotentialPoints, " pts");
   }
}

//+------------------------------------------------------------------+
//| Check basket status (target hit, SL hit, time expired)            |
//+------------------------------------------------------------------+
void CheckBasketStatus()
{
   for(int b = 0; b < g_BasketCount; b++)
   {
      if(!g_Baskets[b].IsActive || g_Baskets[b].IsRecovered || g_Baskets[b].IsLost)
         continue;
      
      // Get current price
      double bid = SymbolInfoDouble(g_Baskets[b].Symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(g_Baskets[b].Symbol, SYMBOL_ASK);
      double currentPrice = (g_Baskets[b].Direction == POSITION_TYPE_BUY) ? bid : ask;
      
      // Update furthest price (worst drawdown)
      if(g_Baskets[b].Direction == POSITION_TYPE_BUY)
      {
         if(currentPrice < g_Baskets[b].FurthestPrice)
            g_Baskets[b].FurthestPrice = currentPrice;
      }
      else
      {
         if(currentPrice > g_Baskets[b].FurthestPrice)
            g_Baskets[b].FurthestPrice = currentPrice;
      }
      
      // Calculate MAE for each layer
      for(int l = 0; l < g_Baskets[b].FilledLayerCount; l++)
      {
         int mae = 0;
         if(g_Baskets[b].Direction == POSITION_TYPE_BUY)
            mae = (int)((g_Baskets[b].Layers[l].EntryPrice - g_Baskets[b].FurthestPrice) / _Point);
         else
            mae = (int)((g_Baskets[b].FurthestPrice - g_Baskets[b].Layers[l].EntryPrice) / _Point);
         
         if(mae > g_Baskets[b].MaxMAE)
            g_Baskets[b].MaxMAE = mae;
      }
      
      // Check if target hit
      bool targetHit = false;
      if(g_Baskets[b].Direction == POSITION_TYPE_BUY)
         targetHit = (bid >= g_Baskets[b].TargetPrice);
      else
         targetHit = (ask <= g_Baskets[b].TargetPrice);
      
      if(targetHit && g_Baskets[b].FilledLayerCount > 0)
      {
         CloseBasket(b, true, "TARGET_HIT");
         continue;
      }
      
      // Check emergency SL
      bool slHit = false;
      for(int l = 0; l < g_Baskets[b].FilledLayerCount; l++)
      {
         double entry = g_Baskets[b].Layers[l].EntryPrice;
         double slPrice;
         if(g_Baskets[b].Direction == POSITION_TYPE_BUY)
            slPrice = entry - (InpEmergencySLPoints * _Point);
         else
            slPrice = entry + (InpEmergencySLPoints * _Point);
         
         if(g_Baskets[b].Direction == POSITION_TYPE_BUY && bid <= slPrice)
            slHit = true;
         if(g_Baskets[b].Direction == POSITION_TYPE_SELL && ask >= slPrice)
            slHit = true;
      }
      
      if(slHit)
      {
         CloseBasket(b, false, "EMERGENCY_SL");
         continue;
      }
      
      // Check time expiration
      datetime expiry = g_Baskets[b].SLHitTime + (InpRecoveryWindowMin * 60);
      if(TimeCurrent() >= expiry && g_Baskets[b].FilledLayerCount > 0)
      {
         CloseBasket(b, false, "TIME_EXPIRED");
         continue;
      }
   }
}

//+------------------------------------------------------------------+
//| Close a recovery basket                                           |
//+------------------------------------------------------------------+
void CloseBasket(int basketIdx, bool recovered, string reason)
{
   // MQL5 doesn't support C++ style references with & in variable declaration
   // Use array index directly or pointer
   SRecoveryBasket basket = g_Baskets[basketIdx];
   
   basket.IsRecovered = recovered;
   basket.IsLost = !recovered;
   basket.CloseTime = TimeCurrent();
   basket.IsActive = false;
   
   // Close all RGU positions for this basket
   for(int i = 0; i < basket.FilledLayerCount; i++)
   {
      CloseRGUPositions(basket.OriginalTicket, i+1);
   }
   
   // Log result
   string result = recovered ? "RECOVERED" : "LOST";
   int totalPotential = basket.TotalPotential;
   
   Print("Basket ", basketIdx, " ", result, " | Reason: ", reason,
         " | Layers: ", basket.FilledLayerCount,
         " | TotalPotential: ", totalPotential,
         " | MaxMAE: ", basket.MaxMAE);
   
   // Write to CSV (pass by reference to the array element)
   WriteBasketToCSV(g_Baskets[basketIdx], result);
}

//+------------------------------------------------------------------+
//| Close RGU positions by original ticket and layer                  |
//+------------------------------------------------------------------+
void CloseRGUPositions(ulong originalTicket, int layerNum)
{
   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      
      // Check if it's our RGU position
      long magic = PositionGetInteger(POSITION_MAGIC);
      if(magic != 999900 + (int)originalTicket) continue;
      
      string comment = PositionGetString(POSITION_COMMENT);
      string layerStr = "RGU_L" + IntegerToString(layerNum);
      if(StringFind(comment, layerStr) == -1) continue;
      
      // Close position
      string symbol = PositionGetString(POSITION_SYMBOL);
      ENUM_POSITION_TYPE dir = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double volume = PositionGetDouble(POSITION_VOLUME);
      
      MqlTradeRequest request;
      MqlTradeResult result;
      ZeroMemory(request);
      ZeroMemory(result);
      
      request.action = TRADE_ACTION_DEAL;
      request.position = ticket;
      request.symbol = symbol;
      request.volume = volume;
      request.type = (dir == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      request.deviation = 10;
      
      if(dir == POSITION_TYPE_BUY)
         request.price = SymbolInfoDouble(symbol, SYMBOL_BID);
      else
         request.price = SymbolInfoDouble(symbol, SYMBOL_ASK);
      
      if(!OrderSend(request, result))
      {
         Print("ERROR: Failed to close RGU position. Error: ", GetLastError());
      }
   }
}

//+------------------------------------------------------------------+
//| Helper: Get original position open price from history
//+------------------------------------------------------------------+
double GetOriginalOpenPrice(ulong dealTicket, string symbol)
{
   // The deal ticket corresponds to the position close deal
   // We need to find the position's entry deal (inout deal)
   HistorySelect(0, TimeCurrent());
   
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0) continue;
      
      // Check if this is the same position
      ulong posID = HistoryDealGetInteger(ticket, DEAL_POSITION_ID);
      ulong closePosID = HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID);
      
      if(posID == closePosID)
      {
         // Check if this is the entry deal (in/out direction)
         ENUM_DEAL_ENTRY entryType = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY);
         if(entryType == DEAL_ENTRY_IN || entryType == DEAL_ENTRY_INOUT)
         {
            return HistoryDealGetDouble(ticket, DEAL_PRICE);
         }
      }
   }
   
   return 0; // Not found
}

//+------------------------------------------------------------------+
//| Helper: Check if basket already exists                            |
//+------------------------------------------------------------------+
bool IsBasketExists(ulong originalTicket)
{
   for(int i = 0; i < g_BasketCount; i++)
   {
      if(g_Baskets[i].OriginalTicket == originalTicket)
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Helper: Check magic number matches filter                         |
//+------------------------------------------------------------------+
bool MagicNumberMatches(long magic, string filter)
{
   string magics[];
   int count = StringSplit(filter, ',', magics);
   for(int i = 0; i < count; i++)
   {
      if(StringToInteger(magics[i]) == magic)
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Helper: Get ATR at specific time                                  |
//+------------------------------------------------------------------+
double GetATRAtTime(string symbol, datetime time)
{
   // Get 60 candles before the time
   datetime from = time - 3600; // 1 hour before
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   
   int copied = CopyRates(symbol, PERIOD_M1, from, time, rates);
   if(copied < 10) return 200; // Default 200 points
   
   // Calculate ATR
   double trSum = 0;
   int count = MathMin(copied - 1, 60);
   
   for(int i = 0; i < count; i++)
   {
      double high = rates[i].high;
      double low = rates[i].low;
      double close = rates[i].close;
      double prevClose = (i < copied - 1) ? rates[i+1].close : close;
      
      double tr = MathMax(high - low, MathMax(MathAbs(high - prevClose), MathAbs(low - prevClose)));
      trSum += tr;
   }
   
   double atr = trSum / count;
   return atr / _Point; // Return in points
}

//+------------------------------------------------------------------+
//| Dashboard Functions                                               |
//+------------------------------------------------------------------+
void CreateDashboard()
{
   int x = InpDashboardX;
   int y = InpDashboardY;
   int width = 600;
   int height = 25;
   
   // Background
   CreateRectangle(g_DashPrefix + "BG", x, y, width, 400, InpBgColor);
   
   // Header
   CreateLabel(g_DashPrefix + "Title", x + 10, y + 5, "RGU Recovery Manager v3.0", 10, clrWhite);
   CreateLabel(g_DashPrefix + "Settings", x + 10, y + 22, 
               "MaxLayers:" + IntegerToString(InpMaxLayers) + 
               " | Mult:" + DoubleToString(InpATRMultiplier, 1) +
               " | L1:" + (InpUseLayer1Immediate ? "IMMEDIATE(!)" : "WAIT"), 
               8, clrYellow);
   
   // Column headers
   y += 45;
   int colX = x + 10;
   CreateLabel(g_DashPrefix + "H1", colX, y, "#", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H2", colX + 25, y, "Dir", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H3", colX + 60, y, "Target", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H4", colX + 120, y, "Layers", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H5", colX + 170, y, "Potential", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H6", colX + 240, y, "RemTime", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H7", colX + 310, y, "Status", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H8", colX + 380, y, "L1@", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H9", colX + 440, y, "L2@", 9, clrWhite);
   CreateLabel(g_DashPrefix + "H10", colX + 500, y, "L3@", 9, clrWhite);
}

void UpdateDashboard()
{
   int x = InpDashboardX;
   int y = InpDashboardY + 60;
   int colX = x + 10;
   
   // Count active baskets
   int activeCount = 0;
   for(int i = 0; i < g_BasketCount; i++)
   {
      if(g_Baskets[i].IsActive && !g_Baskets[i].IsRecovered && !g_Baskets[i].IsLost)
         activeCount++;
   }
   
   // Update active count
   ObjectSetString(0, g_DashPrefix + "Title", OBJPROP_TEXT, 
                   "RGU Recovery Manager v3.0 | Active: " + IntegerToString(activeCount));
   
   // Update rows (max 15 visible)
   for(int row = 0; row < 15; row++)
   {
      string suffix = "_" + IntegerToString(row);
      int rowY = y + (row * InpRowHeight);
      
      if(row < g_BasketCount)
      {
         SRecoveryBasket b = g_Baskets[row];
         
         // Color based on direction
         color dirColor = (b.Direction == POSITION_TYPE_BUY) ? InpBuyColor : InpSellColor;
         
         // Status color
         color statusColor = InpActiveColor;
         string status = b.GetStatusString();
         if(status == "CRITICAL") statusColor = InpCriticalColor;
         else if(status == "WARN") statusColor = InpWarnColor;
         else if(b.IsRecovered) statusColor = clrGreen;
         else if(b.IsLost) statusColor = clrGray;
         
         // Remaining time
         int remMin = b.GetRemainingMinutes();
         string remTime = (b.IsActive && !b.IsRecovered && !b.IsLost) ? 
                          IntegerToString(remMin) + "m" : "--";
         
         // Layer prices
         string l1 = b.Layers[0].IsFilled ? DoubleToString(b.Layers[0].EntryPrice, 1) : "--";
         string l2 = b.Layers[1].IsFilled ? DoubleToString(b.Layers[1].EntryPrice, 1) : "--";
         string l3 = b.Layers[2].IsFilled ? DoubleToString(b.Layers[2].EntryPrice, 1) : "--";
         
         UpdateLabel(g_DashPrefix + "R1" + suffix, colX, rowY, IntegerToString(row+1), 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R2" + suffix, colX + 25, rowY, 
                     (b.Direction == POSITION_TYPE_BUY ? "BUY" : "SELL"), 8, dirColor);
         UpdateLabel(g_DashPrefix + "R3" + suffix, colX + 60, rowY, 
                     DoubleToString(b.TargetPrice, 1), 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R4" + suffix, colX + 170, rowY, 
                     IntegerToString(b.FilledLayerCount) + "/" + IntegerToString(InpMaxLayers), 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R5" + suffix, colX + 240, rowY, 
                     IntegerToString(b.TotalPotential), 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R6" + suffix, colX + 310, rowY, remTime, 8, 
                     (remMin < 5) ? InpCriticalColor : (remMin < 30) ? InpWarnColor : clrWhite);
         UpdateLabel(g_DashPrefix + "R7" + suffix, colX + 380, rowY, status, 8, statusColor);
         UpdateLabel(g_DashPrefix + "R8" + suffix, colX + 440, rowY, l1, 8, 
                     b.Layers[0].IsFilled ? clrLime : clrGray);
         UpdateLabel(g_DashPrefix + "R9" + suffix, colX + 500, rowY, l2, 8, 
                     b.Layers[1].IsFilled ? clrLime : clrGray);
         UpdateLabel(g_DashPrefix + "R10" + suffix, colX + 560, rowY, l3, 8, 
                     b.Layers[2].IsFilled ? clrLime : clrGray);
      }
      else
      {
         // Clear unused rows
         UpdateLabel(g_DashPrefix + "R1" + suffix, colX, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R2" + suffix, colX + 25, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R3" + suffix, colX + 60, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R4" + suffix, colX + 170, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R5" + suffix, colX + 240, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R6" + suffix, colX + 310, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R7" + suffix, colX + 380, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R8" + suffix, colX + 440, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R9" + suffix, colX + 500, rowY, "", 8, clrWhite);
         UpdateLabel(g_DashPrefix + "R10" + suffix, colX + 560, rowY, "", 8, clrWhite);
      }
   }
}

void CreateLabel(string name, int x, int y, string text, int fontSize, color clr)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetString(0, name, OBJPROP_FONT, "Arial");
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

void UpdateLabel(string name, int x, int y, string text, int fontSize, color clr)
{
   CreateLabel(name, x, y, text, fontSize, clr);
}

void CreateRectangle(string name, int x, int y, int width, int height, color clr)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, width);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, height);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
}

void ClearDashboard()
{
   ObjectsDeleteAll(0, g_DashPrefix);
}

//+------------------------------------------------------------------+
