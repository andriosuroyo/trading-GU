//+------------------------------------------------------------------+
//|                                            GUM_Structures.mqh    |
//|                                      Data structures for GUM     |
//+------------------------------------------------------------------+
#ifndef GUM_STRUCTURES_MQH
#define GUM_STRUCTURES_MQH

//+------------------------------------------------------------------+
//| Status ENUM                                                       |
//+------------------------------------------------------------------+
enum ENUM_GUM_STATUS
{
   GUM_STATUS_OPEN,      // Position is within cutoff window, not yet CLEAR
   GUM_STATUS_CLEAR,     // Position hit TrailStart (or TP) - successful
   GUM_STATUS_RECOVERY,  // Position closed by time cutoff or SL - monitoring for recovery
   GUM_STATUS_RECOVERED, // Price returned to/beyond PriceOpen - recovered
   GUM_STATUS_LOST       // Recovery position exceeded time limit
};

//+------------------------------------------------------------------+
//| Filter Method ENUM                                                |
//+------------------------------------------------------------------+
enum ENUM_GUM_FILTER_METHOD
{
   GUM_FILTER_MAGIC,   // Filter by magic number(s)
   GUM_FILTER_COMMENT, // Filter by comment text
   GUM_FILTER_SYMBOL   // Filter by symbol(s)
};

//+------------------------------------------------------------------+
//| Duration Type ENUM                                                |
//+------------------------------------------------------------------+
enum ENUM_GUM_DURATION_TYPE
{
   GUM_DURATION_SECONDS,
   GUM_DURATION_MINUTES,
   GUM_DURATION_HOURS
};

//+------------------------------------------------------------------+
//| Session ENUM (for per-session settings)                           |
//+------------------------------------------------------------------+
enum ENUM_GUM_SESSION
{
   GUM_SESSION_ASIA,
   GUM_SESSION_LONDON,
   GUM_SESSION_NY,
   GUM_SESSION_FULL,
   GUM_SESSION_UNKNOWN
};

//+------------------------------------------------------------------+
//| Recovery Hours Structure                                          |
//+------------------------------------------------------------------+
struct SRecoveryHours
{
   int Asia;
   int London;
   int NY;
   int Full;
};

//+------------------------------------------------------------------+
//| Position Record Structure                                         |
//+------------------------------------------------------------------+
struct SPositionRecord
{
   // Identification
   ulong             Ticket;
   string            Symbol;
   ENUM_POSITION_TYPE Type;  // POSITION_TYPE_BUY or POSITION_TYPE_SELL
   string            Comment;
   long              MagicNumber;
   
   // Session classification
   ENUM_GUM_SESSION  Session;
   
   // Open details
   datetime          TimeOpen;
   double            PriceOpen;
   double            LotSize;
   double            LotSizeNormalized; // Normalized to 0.01
   
   // Status
   ENUM_GUM_STATUS   Status;
   datetime          StatusChangedTime;
   
   // Close details (when applicable)
   datetime          TimeClose;
   double            PriceClose;
   double            Profit;
   
   // Recovery tracking
   datetime          TimeRecovered;     // When status changed to RECOVERED
   
   // TCM tracking
   datetime          CutoffTime;        // When time cutoff will/ did occur
   bool              IsTrailing;        // Currently in trailing mode
   double            MaxProfitPrice;    // For trailing stop calculation (in price terms)
   
   // Methods
   void Initialize()
   {
      Ticket = 0;
      Symbol = "";
      Type = POSITION_TYPE_BUY;
      Comment = "";
      MagicNumber = 0;
      Session = GUM_SESSION_UNKNOWN;
      TimeOpen = 0;
      PriceOpen = 0;
      LotSize = 0;
      LotSizeNormalized = 0;
      Status = GUM_STATUS_OPEN;
      StatusChangedTime = 0;
      TimeClose = 0;
      PriceClose = 0;
      Profit = 0;
      TimeRecovered = 0;
      CutoffTime = 0;
      IsTrailing = false;
      MaxProfitPrice = 0;
   }
   
   // Get session from magic number or comment
   void DetectSession()
   {
      // Session detection from magic number
      // Format: First digit = strategy, Second digit = session
      // 1x = MH, 2x = HR10, 3x = HR05
      // x0 = Full, x1 = Asia, x2 = London, x3 = NY
      
      int secondDigit = (int)(MagicNumber % 10);
      
      switch(secondDigit)
      {
         case 1: Session = GUM_SESSION_ASIA; break;
         case 2: Session = GUM_SESSION_LONDON; break;
         case 3: Session = GUM_SESSION_NY; break;
         case 0: Session = GUM_SESSION_FULL; break;
         default: Session = GUM_SESSION_UNKNOWN;
      }
      
      // If still unknown, try comment detection
      if(Session == GUM_SESSION_UNKNOWN)
      {
         string upperComment = Comment;
         StringToUpper(upperComment);
         
         if(StringFind(upperComment, "ASIA") != -1)
            Session = GUM_SESSION_ASIA;
         else if(StringFind(upperComment, "LONDON") != -1)
            Session = GUM_SESSION_LONDON;
         else if(StringFind(upperComment, "NEWYORK") != -1 || StringFind(upperComment, "NY") != -1)
            Session = GUM_SESSION_NY;
         else if(StringFind(upperComment, "FULL") != -1)
            Session = GUM_SESSION_FULL;
      }
   }
   
   // Calculate normalized lot size (to 0.01)
   double CalculateNormalizedLots()
   {
      if(LotSize <= 0) return 0;
      return LotSize / 0.01;
   }
   
   // Determine if closed position should be CLEAR or RECOVERY
   // Called when position is detected as closed (moved from Trade to History tab)
   // 
   // CLEAR = Profit OR small loss (< $0.50 per 0.01 lot)
   //         Small losses are typically due to slippage on trades that 
   //         hit TrailStart but closed slightly negative
   //
   // RECOVERY = Loss >= $0.50 per 0.01 lot
   //            Genuine loss - position did not hit TrailStart before closing
   //
   // The $0.50 threshold is based on typical TrailStart settings:
   // - Asia: TrailStart ~$0.30 per 0.01
   // - London/NY: TrailStart ~$0.50-$0.80 per 0.01
   bool ShouldBeClear()
   {
      // Normalize P&L to 0.01 lot equivalent
      double normalizedPnL = Profit / LotSize * 0.01;
      
      // CLEAR if profit OR small loss (< $0.50)
      // RECOVERY if loss >= $0.50
      return (normalizedPnL >= -0.50);
   }
   
   // Get status as string
   string GetStatusString()
   {
      switch(Status)
      {
         case GUM_STATUS_OPEN:      return "OPEN";
         case GUM_STATUS_CLEAR:     return "CLEAR";
         case GUM_STATUS_RECOVERY:  return "RECOVERY";
         case GUM_STATUS_RECOVERED: return "RECOVERED";
         case GUM_STATUS_LOST:      return "LOST";
         default:                   return "UNKNOWN";
      }
   }
   
   // Get session as string
   string GetSessionString()
   {
      switch(Session)
      {
         case GUM_SESSION_ASIA:   return "ASIA";
         case GUM_SESSION_LONDON: return "LONDON";
         case GUM_SESSION_NY:     return "NY";
         case GUM_SESSION_FULL:   return "FULL";
         default:                 return "UNKNOWN";
      }
   }
   
   // Get type as string
   string GetTypeString()
   {
      return (Type == POSITION_TYPE_BUY) ? "BUY" : "SELL";
   }
   
   // Check if this position matches filter criteria
   bool MatchesFilter(ENUM_GUM_FILTER_METHOD method, string filterValue)
   {
      switch(method)
      {
         case GUM_FILTER_MAGIC:
         {
            // Check if magic number is in comma-separated list
            // "0" means all positions
            if(filterValue == "0" || filterValue == "") return true;
            
            string magics[];
            int count = StringSplit(filterValue, ',', magics);
            for(int i = 0; i < count; i++)
            {
               if(StringToInteger(magics[i]) == MagicNumber)
                  return true;
            }
            return false;
         }
         
         case GUM_FILTER_COMMENT:
         {
            if(filterValue == "") return true;
            return (StringFind(Comment, filterValue) != -1);
         }
         
         case GUM_FILTER_SYMBOL:
         {
            if(filterValue == "") return true;
            
            string symbols[];
            int count = StringSplit(filterValue, ',', symbols);
            for(int i = 0; i < count; i++)
            {
               if(symbols[i] == Symbol)
                  return true;
            }
            return false;
         }
      }
      return false;
   }
};

//+------------------------------------------------------------------+
//| Helper function to convert duration to seconds                    |
//+------------------------------------------------------------------+
int DurationToSeconds(ENUM_GUM_DURATION_TYPE type, int value)
{
   switch(type)
   {
      case GUM_DURATION_SECONDS: return value;
      case GUM_DURATION_MINUTES: return value * 60;
      case GUM_DURATION_HOURS:   return value * 3600;
      default: return value * 60;
   }
}

//+------------------------------------------------------------------+
//| Helper function to get recovery hours for session                 |
//+------------------------------------------------------------------+
int GetRecoveryHoursForSession(ENUM_GUM_SESSION session, SRecoveryHours &hours)
{
   switch(session)
   {
      case GUM_SESSION_ASIA:   return hours.Asia;
      case GUM_SESSION_LONDON: return hours.London;
      case GUM_SESSION_NY:     return hours.NY;
      case GUM_SESSION_FULL:   return hours.Full;
      default:                 return hours.Full;
   }
}

//+------------------------------------------------------------------+
//| Helper function to format time duration                           |
//+------------------------------------------------------------------+
string FormatDuration(int seconds)
{
   if(seconds < 0) return "0s";
   
   int hours = seconds / 3600;
   int mins = (seconds % 3600) / 60;
   int secs = seconds % 60;
   
   if(hours > 0)
      return StringFormat("%dh %dm", hours, mins);
   else if(mins > 0)
      return StringFormat("%dm %ds", mins, secs);
   else
      return StringFormat("%ds", secs);
}

#endif // GUM_STRUCTURES_MQH
//+------------------------------------------------------------------+
