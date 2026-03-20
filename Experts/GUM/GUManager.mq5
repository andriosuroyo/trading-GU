//+------------------------------------------------------------------+
//|                                               GUManager.mq5      |
//|                                    GU Manager (GUM) - Replaces TCM|
//|                                              Version 1.0         |
//+------------------------------------------------------------------+
#property copyright "GU Strategy"
#property version   "1.00"
#property strict

#include "GUM_Structures.mqh"
#include "GUM_CSVManager.mqh"
#include "GUM_PositionManager.mqh"
#include "GUM_Dashboard.mqh"

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+
// Filter Settings
input ENUM_GUM_FILTER_METHOD InpFilterMethod = GUM_FILTER_MAGIC;
input string                 InpFilterValue  = "11,12,13";  // Comma-separated magic numbers or comment text

// Time-Based Cutoff Settings (TCM legacy)
input ENUM_GUM_DURATION_TYPE InpDurationType   = GUM_DURATION_MINUTES;
input int                    InpDurationValue  = 5;
input int                    InpWarningSeconds = 10;
input bool                   InpUseTrailing    = false;
input double                 InpTrailDistance  = 0;  // Points

// Recovery Monitor Settings
input int    InpRecoveryHoursAsia   = 4;   // Hours before LOST status (Asia)
input int    InpRecoveryHoursLondon = 4;   // Hours before LOST status (London)
input int    InpRecoveryHoursNY     = 4;   // Hours before LOST status (NY)
input int    InpRecoveryHoursFull   = 4;   // Hours before LOST status (Full-Time)
input string InpCSVFileName         = "data\\GUM_Positions.csv";  // Use \\ for subfolders
input bool   InpNormalizeLots       = true;  // Normalize lots to 0.01 in CSV

// Dashboard Settings
input int    InpDashboardX         = 10;
input int    InpDashboardY         = 30;
input int    InpRowHeight          = 20;
input color  InpBgColor            = C'30,30,30';
input color  InpNormalColor        = clrWhite;
input color  InpWarningColor       = clrYellow;
input color  InpCriticalColor      = clrRed;
input color  InpProfitColor        = clrLime;
input color  InpLossColor          = clrSalmon;
input color  InpRecoveryColor      = clrOrange;
input color  InpRecoveredColor     = clrGreen;
input color  InpLostColor          = clrGray;
input color  InpClearColor         = clrAqua;

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+
CGUM_CSVManager      g_csvManager;
CGUM_PositionManager g_positionManager;
CGUM_Dashboard       g_dashboard;
datetime             g_lastUpdate = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("=== GU Manager (GUM) v1.0 Starting ===");
   
   // Initialize CSV manager
   if(!g_csvManager.Initialize(InpCSVFileName, InpNormalizeLots))
   {
      Print("ERROR: Failed to initialize CSV manager");
      return(INIT_FAILED);
   }
   
   // Load existing recovery positions from CSV
   g_positionManager.LoadRecoveryPositions(GetPointer(g_csvManager));
   Print("Loaded ", g_positionManager.GetRecoveryCount(), " recovery positions from CSV");
   
   // Initialize position manager with settings
   SRecoveryHours hours;
   hours.Asia   = InpRecoveryHoursAsia;
   hours.London = InpRecoveryHoursLondon;
   hours.NY     = InpRecoveryHoursNY;
   hours.Full   = InpRecoveryHoursFull;
   
   g_positionManager.Initialize(
      InpFilterMethod,
      InpFilterValue,
      InpDurationType,
      InpDurationValue,
      InpUseTrailing,
      InpTrailDistance,
      hours,
      GetPointer(g_csvManager)
   );
   
   // Initialize dashboard
   g_dashboard.Initialize(
      InpDashboardX, InpDashboardY, InpRowHeight,
      InpBgColor, InpNormalColor, InpWarningColor, InpCriticalColor,
      InpProfitColor, InpLossColor, InpRecoveryColor, InpRecoveredColor,
      InpLostColor, InpClearColor
   );
   
   // Create initial dashboard
   g_dashboard.Create();
   
   Print("=== GU Manager initialized successfully ===");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("=== GU Manager shutting down (reason: ", reason, ") ===");
   
   // Save all positions to CSV before exit
   g_positionManager.SaveAllPositions(GetPointer(g_csvManager));
   
   // Cleanup dashboard
   g_dashboard.Destroy();
   
   Print("=== GU Manager shutdown complete ===");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Update once per second to minimize CPU usage
   datetime currentTime = TimeLocal();
   if(currentTime == g_lastUpdate) return;
   g_lastUpdate = currentTime;
   
   // Process all positions (check for new, updates, closures)
   g_positionManager.ProcessPositions();
   
   // Get positions for dashboard
   SPositionRecord activePositions[];
   SPositionRecord recoveryPositions[];
   g_positionManager.GetActivePositions(activePositions);
   g_positionManager.GetRecoveryPositions(recoveryPositions);
   
   // Update dashboard
   g_dashboard.Update(activePositions, recoveryPositions, InpWarningSeconds);
}

//+------------------------------------------------------------------+
//| Trade transaction handler                                         |
//+------------------------------------------------------------------+
void OnTrade()
{
   // Immediate response to trade events
   g_positionManager.ProcessPositions();
}

//+------------------------------------------------------------------+
//| Timer handler                                                     |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Backup update every second
   OnTick();
}
//+------------------------------------------------------------------+
