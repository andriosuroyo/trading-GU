//+------------------------------------------------------------------+
//|                                              DurationExitPro.mq5 |
//|                        Copyright 2026, MetaTrader 5 Duration EA  |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| Input Parameters                                                   |
//+------------------------------------------------------------------+
//--- General Settings
input group "=== General Settings ==="
input bool   InpDeletePendingOnClose = true;    // Delete pending orders when closing
input bool   InpCloseAllSymbols = false;        // Close all symbols (false = chart symbol only)
input string InpMagicNumbers = "0";             // Magic numbers (comma-separated, 0 = all)

//--- Closing Mode
input group "=== Closing Mode ==="
enum ENUM_CLOSING_MODE
{
   MODE_TIME_ONLY,     // Time-based only
   MODE_DURATION_ONLY, // Duration-based only
   MODE_BOTH           // Both time and duration
};
input ENUM_CLOSING_MODE InpClosingMode = MODE_DURATION_ONLY;  // Closing mode selection

//--- Time-based Settings
input int    InpClosingHour = 23;               // Closing hour (0-23)
input int    InpClosingMinute = 50;             // Closing minute (0-59)

//--- Duration-based Settings
enum ENUM_DURATION_TYPE
{
   DURATION_SECONDS, // Seconds
   DURATION_MINUTES, // Minutes
   DURATION_HOURS    // Hours
};
input ENUM_DURATION_TYPE InpDurationType = DURATION_MINUTES;  // Duration type
input int    InpMaxTradeDuration = 10;          // Max trade duration

//+------------------------------------------------------------------+
//| Global Variables                                                   |
//+------------------------------------------------------------------+
CTrade       m_trade;
ulong        m_magicNumbers[];
bool         m_useAllMagics = true;
datetime     m_lastCheckTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   //--- Initialize trade object
   m_trade.SetExpertMagicNumber(0);
   
   //--- Parse magic numbers
   if(!ParseMagicNumbers(InpMagicNumbers))
   {
      Print("Failed to parse magic numbers: ", InpMagicNumbers);
      return(INIT_FAILED);
   }
   
   //--- Validate inputs
   if(InpClosingHour < 0 || InpClosingHour > 23)
   {
      Print("Invalid closing hour: ", InpClosingHour);
      return(INIT_FAILED);
   }
   if(InpClosingMinute < 0 || InpClosingMinute > 59)
   {
      Print("Invalid closing minute: ", InpClosingMinute);
      return(INIT_FAILED);
   }
   if(InpMaxTradeDuration <= 0)
   {
      Print("Invalid max trade duration: ", InpMaxTradeDuration);
      return(INIT_FAILED);
   }
   
   //--- Set timer for regular checks (every 1 second)
   EventSetTimer(1);
   
   Print("DurationExitPro initialized successfully");
   Print("Mode: ", GetClosingModeString());
   Print("Magic numbers: ", InpMagicNumbers);
   Print("Symbol scope: ", InpCloseAllSymbols ? "All symbols" : Symbol());
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("DurationExitPro deinitialized");
}

//+------------------------------------------------------------------+
//| Timer function                                                     |
//+------------------------------------------------------------------+
void OnTimer()
{
   CheckAndClosePositions();
   
   if(InpDeletePendingOnClose)
      CheckAndDeletePendingOrders();
}

//+------------------------------------------------------------------+
//| Parse magic numbers from comma-separated string                    |
//+------------------------------------------------------------------+
bool ParseMagicNumbers(const string &magicString)
{
   //--- Check for "0" or empty string = all magics
   if(magicString == "0" || magicString == "" || magicString == " ")
   {
      m_useAllMagics = true;
      ArrayResize(m_magicNumbers, 0);
      return true;
   }
   
   m_useAllMagics = false;
   
   //--- Split by comma
   string parts[];
   ushort separator = StringGetCharacter(",", 0);
   int count = StringSplit(magicString, separator, parts);
   
   if(count <= 0)
   {
      //--- Single value
      ArrayResize(m_magicNumbers, 1);
      m_magicNumbers[0] = (ulong)StringToInteger(magicString);
      return true;
   }
   
   //--- Parse each part
   ArrayResize(m_magicNumbers, count);
   for(int i = 0; i < count; i++)
   {
      string trimmed = StringLower(parts[i]);
      StringReplace(trimmed, " ", "");
      m_magicNumbers[i] = (ulong)StringToInteger(trimmed);
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Check if magic number matches filter                               |
//+------------------------------------------------------------------+
bool IsMagicNumberValid(const ulong magic)
{
   if(m_useAllMagics)
      return true;
   
   int size = ArraySize(m_magicNumbers);
   for(int i = 0; i < size; i++)
   {
      if(m_magicNumbers[i] == magic)
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Get closing mode as string                                         |
//+------------------------------------------------------------------+
string GetClosingModeString()
{
   switch(InpClosingMode)
   {
      case MODE_TIME_ONLY:
         return "Time-based only";
      case MODE_DURATION_ONLY:
         return "Duration-based only";
      case MODE_BOTH:
         return "Both time and duration";
      default:
         return "Unknown";
   }
}

//+------------------------------------------------------------------+
//| Convert duration to seconds based on type                          |
//+------------------------------------------------------------------+
int GetMaxDurationSeconds()
{
   switch(InpDurationType)
   {
      case DURATION_SECONDS:
         return InpMaxTradeDuration;
      case DURATION_MINUTES:
         return InpMaxTradeDuration * 60;
      case DURATION_HOURS:
         return InpMaxTradeDuration * 3600;
      default:
         return InpMaxTradeDuration * 60;
   }
}

//+------------------------------------------------------------------+
//| Get duration type as string                                        |
//+------------------------------------------------------------------+
string GetDurationTypeString()
{
   switch(InpDurationType)
   {
      case DURATION_SECONDS:
         return "seconds";
      case DURATION_MINUTES:
         return "minutes";
      case DURATION_HOURS:
         return "hours";
      default:
         return "unknown";
   }
}

//+------------------------------------------------------------------+
//| Check if time-based close condition is met                         |
//+------------------------------------------------------------------+
bool IsTimeCloseConditionMet()
{
   if(InpClosingMode == MODE_DURATION_ONLY)
      return false;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   return (dt.hour == InpClosingHour && dt.min == InpClosingMinute);
}

//+------------------------------------------------------------------+
//| Check if duration-based close condition is met                     |
//+------------------------------------------------------------------+
bool IsDurationCloseConditionMet(const datetime openTime)
{
   if(InpClosingMode == MODE_TIME_ONLY)
      return false;
   
   int maxSeconds = GetMaxDurationSeconds();
   int elapsedSeconds = (int)(TimeCurrent() - openTime);
   
   return (elapsedSeconds >= maxSeconds);
}

//+------------------------------------------------------------------+
//| Check and close positions based on configured conditions           |
//+------------------------------------------------------------------+
void CheckAndClosePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      //--- Get position info
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      
      //--- Check symbol filter
      string posSymbol = PositionGetString(POSITION_SYMBOL);
      if(!InpCloseAllSymbols && posSymbol != Symbol())
         continue;
      
      //--- Check magic number filter
      ulong posMagic = PositionGetInteger(POSITION_MAGIC);
      if(!IsMagicNumberValid(posMagic))
         continue;
      
      //--- Get position open time
      datetime openTime = (datetime)PositionGetInteger(POSITION_TIME);
      
      //--- Check closing conditions
      bool shouldClose = false;
      string closeReason = "";
      
      // Check time-based condition
      if(IsTimeCloseConditionMet())
      {
         shouldClose = true;
         closeReason = StringFormat("Time condition met (%02d:%02d)", InpClosingHour, InpClosingMinute);
      }
      // Check duration-based condition
      else if(IsDurationCloseConditionMet(openTime))
      {
         shouldClose = true;
         int elapsed = (int)(TimeCurrent() - openTime);
         closeReason = StringFormat("Duration exceeded (%d %s)", elapsed, GetDurationTypeString());
      }
      
      //--- Close position if conditions met
      if(shouldClose)
      {
         ClosePosition(ticket, posSymbol, closeReason);
      }
   }
}

//+------------------------------------------------------------------+
//| Close a specific position                                          |
//+------------------------------------------------------------------+
bool ClosePosition(const ulong ticket, const string symbol, const string reason)
{
   //--- Get position details for logging
   double volume = PositionGetDouble(POSITION_VOLUME);
   double profit = PositionGetDouble(POSITION_PROFIT);
   ulong magic = PositionGetInteger(POSITION_MAGIC);
   
   //--- Attempt to close
   if(!m_trade.PositionClose(ticket))
   {
      Print("Failed to close position #", ticket, " on ", symbol, 
            ". Error: ", GetLastError());
      return false;
   }
   
   Print("Closed position #", ticket, " on ", symbol, 
         " | Volume: ", volume, " | Magic: ", magic, 
         " | Profit: $", DoubleToString(profit, 2), " | Reason: ", reason);
   
   return true;
}

//+------------------------------------------------------------------+
//| Check and delete pending orders based on filters                   |
//+------------------------------------------------------------------+
void CheckAndDeletePendingOrders()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      //--- Get order info
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0)
         continue;
      
      //--- Check symbol filter
      string orderSymbol = OrderGetString(ORDER_SYMBOL);
      if(!InpCloseAllSymbols && orderSymbol != Symbol())
         continue;
      
      //--- Check magic number filter
      ulong orderMagic = OrderGetInteger(ORDER_MAGIC);
      if(!IsMagicNumberValid(orderMagic))
         continue;
      
      //--- Check if order type is pending (not market)
      ENUM_ORDER_TYPE orderType = (ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
      if(orderType == ORDER_TYPE_BUY || orderType == ORDER_TYPE_SELL)
         continue; // Market orders only handled by position close
      
      //--- Check closing conditions
      bool shouldDelete = false;
      datetime orderTime = (datetime)OrderGetInteger(ORDER_TIME_SETUP);
      
      // Check time-based condition
      if(IsTimeCloseConditionMet())
      {
         shouldDelete = true;
      }
      // Check duration-based condition
      else if(IsDurationCloseConditionMet(orderTime))
      {
         shouldDelete = true;
      }
      
      //--- Delete order if conditions met
      if(shouldDelete)
      {
         DeletePendingOrder(ticket, orderSymbol);
      }
   }
}

//+------------------------------------------------------------------+
//| Delete a pending order                                             |
//+------------------------------------------------------------------+
bool DeletePendingOrder(const ulong ticket, const string symbol)
{
   if(!m_trade.OrderDelete(ticket))
   {
      Print("Failed to delete pending order #", ticket, " on ", symbol, 
            ". Error: ", GetLastError());
      return false;
   }
   
   Print("Deleted pending order #", ticket, " on ", symbol);
   return true;
}

//+------------------------------------------------------------------+
//| String helper - convert to lowercase                               |
//+------------------------------------------------------------------+
string StringLower(string str)
{
   string result = str;
   StringToLower(result);
   return result;
}
//+------------------------------------------------------------------+
