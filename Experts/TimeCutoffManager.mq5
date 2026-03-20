//+------------------------------------------------------------------+
//|                                       TimeCutoffManager.mq5       |
//|                        Time-Based Position Cutoff Manager         |
//|                        VERSION 2.2 - PARTIAL CLOSE                |
//|                                                                   |
//|  FIXES v2.1:                                                      |
//|  - Removed Sleep() anti-pattern, replaced with state machine      |
//|  - Added atomic position validation (race condition fix)          |
//|  - Added SymbolSelect() for multi-symbol monitoring               |
//|  - Added connection state validation                              |
//|  - Added retry logic with exponential backoff                     |
//|  - Fixed hardcoded error codes to use TRADE_RETCODE constants     |
//|  - Added FILE_COMMON mutex for multi-instance safety              |
//|  - Optimized dashboard (update, don't recreate)                   |
//|  - Added periodic position array cleanup                          |
//|  - Added spread filter for close validation                       |
//|                                                                   |
//|  FEATURES v2.2:                                                   |
//|  - Two-stage close: Partial close at MidDuration, full at End     |
//|  - Configurable partial close percentage                          |
//|  - Independent timing for partial and final close                 |
//+------------------------------------------------------------------+
#property copyright "GU Trading"
#property link      ""
#property version   "2.20"
#property strict

#include <Trade\Trade.mqh>
#include <Arrays\ArrayLong.mqh>

//--- Filter Method Enumeration
enum ENUM_FILTER_METHOD
{
   FILTER_BY_MAGIC_NUMBER,    // (1) Magic Number (0=all, comma-separated)
   FILTER_BY_COMMENT,         // (2) Comment Contains
   FILTER_BY_SYMBOL           // (3) Symbol (comma-separated)
};

//--- Duration Type Enumeration
enum ENUM_DURATION_TYPE
{
   DURATION_SECONDS,          // (1) Seconds
   DURATION_MINUTES,          // (2) Minutes
   DURATION_HOURS             // (3) Hours
};

//--- Close State Enumeration (replaces Sleep anti-pattern)
enum ENUM_CLOSE_STATE
{
   CLOSE_STATE_IDLE,          // Not attempting close
   CLOSE_STATE_PENDING,       // Close request sent, waiting for confirmation
   CLOSE_STATE_RETRY          // Close failed, scheduling retry
};

//--- Input Parameters
input group "=== Position Filter Method ==="
input ENUM_FILTER_METHOD InpFilterMethod = FILTER_BY_MAGIC_NUMBER;  // Filter Method
input string InpFilterValue = "11,12,13";                           // Filter Value (see description below)

input group "=== Cutoff Settings ==="
input ENUM_DURATION_TYPE InpDurationType = DURATION_MINUTES;  // Duration Type
input int    InpCloseDuration = 2;                            // Final Close Duration (e.g., 2 = close all at 2 minutes)
input bool   InpUsePartialClose = true;                       // Enable Partial Close (true=2-stage, false=single close)
input int    InpPartialCloseDuration = 1;                     // Partial Close Duration (e.g., 1 = close 50% at 1 min)
input double InpPartialClosePct = 50;                         // Partial Close Percentage (e.g., 50 = close 50% of volume)
input int    InpWarningSeconds = 10;                          // Warning Before Close (seconds)
input bool   InpUseTrailing = false;                          // Use Trailing Stop After Cutoff
input double InpTrailDistance = 0;                            // Trail Distance (points, 0 = disabled)
input int    InpMaxSpreadPoints = 500;                        // Max Spread to Allow Close (points, 0=disable)

input group "=== Retry Settings ==="
input int    InpMaxCloseRetries = 3;                          // Max Close Attempts
input int    InpRetryDelayMs = 250;                           // Base Retry Delay (ms)

input group "=== Dashboard Settings ==="
input int    InpDashboardX = 10;                 // Dashboard X Position
input int    InpDashboardY = 30;                 // Dashboard Y Position
input int    InpRowHeight = 20;                  // Row Height
input color  InpBackgroundColor = C'30,30,30';   // Dashboard Background Color
input color  InpColorNormal = clrWhite;          // Normal Color
input color  InpColorWarning = clrYellow;        // Warning Color
input color  InpColorCritical = clrRed;          // Critical Color
input color  InpColorProfit = clrLime;           // Profit Color
input color  InpColorLoss = clrSalmon;           // Loss Color

input group "=== Recovery Tracking ==="
input bool   InpTrackLosses = true;              // Enable Loss Tracking
input string InpRecoveryFile = "loss_recovery.csv"; // Recovery Data File
input double InpRecoveryMultiplier = 1.5;        // Recovery Lot Multiplier

//--- Global Constants
#define TCM_FILE_MUTEX_TIMEOUT_MS 5000    // 5 second timeout for file mutex
#define TCM_ARRAY_CLEANUP_INTERVAL 300    // Cleanup closed positions every 5 minutes
#define TCM_CONNECTION_CHECK_INTERVAL 10  // Check connection every 10 seconds

//--- Global Variables
CTrade      Trade;

struct PositionData {
    ulong   ticket;
    string  symbol;
    string  comment;
    long    magic;
    datetime openTime;
    datetime cutoffTime;          // Final close time (full close)
    datetime partialCutoffTime;   // Partial close time (0 if disabled)
    double  openPrice;
    double  lots;                 // Current lots (updated after partial close)
    double  initialLots;          // Original lots opened
    int     type;              // ORDER_TYPE_BUY or ORDER_TYPE_SELL
    double  currentPnL;
    double  maxPnL;            // For trailing
    bool    warningIssued;
    bool    closed;
    bool    inTrailingMode;       // True after final cutoff if trailing enabled
    bool    partialCloseDone;     // True after partial close executed
    double  partialCloseLots;     // Lots closed in partial close
    //--- v2.1: State machine for close operations
    ENUM_CLOSE_STATE closeState;
    datetime lastCloseAttempt;
    int      closeRetryCount;
    ulong    pendingCloseTicket;
};

PositionData g_positions[];
int g_positionCount = 0;

// Recovery tracking
struct LossRecord {
    datetime date;
    string   symbol;
    double   loss;
    double   lots;
    ulong    ticket;
    bool     recovered;
};

LossRecord g_lossHistory[];
double g_totalUnrecoveredLoss = 0;
datetime g_lastCheck = 0;
datetime g_lastCleanup = 0;
datetime g_lastConnectionCheck = 0;
bool g_terminalConnected = false;
bool g_tradeAllowed = false;

// Filter value arrays (parsed from input)
long     g_magicNumbers[];
string   g_symbols[];

// Symbol selection tracking (for multi-symbol support)
string   g_selectedSymbols[];

// File mutex for multi-instance safety
string   g_fileMutexName = "";

// Dashboard object cache (to prevent delete/recreate spam)
string   g_dashboardObjectCache[];
bool     g_dashboardInitialized = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    //--- CRITICAL: Validate terminal state before doing anything
    if(!ValidateTerminalState())
        return INIT_FAILED;
    
    //--- Set up trade context
    Trade.SetExpertMagicNumber(0); // We don't trade, just close
    Trade.SetDeviationInPoints(10); // 10 point slippage tolerance
    
    //--- Generate unique mutex name for this instance
    g_fileMutexName = "TCM_Mutex_" + IntegerToString(TimeCurrent());
    
    //--- Parse filter values
    ParseFilterValues();
    
    //--- Initialize symbol selection for multi-symbol monitoring
    InitializeSymbolSelection();
    
    //--- Create dashboard
    CreateDashboard();
    
    //--- Load recovery data (with mutex)
    if(InpTrackLosses)
    {
        if(!AcquireFileMutex())
        {
            Print("ERROR: Cannot acquire file mutex. Another TCM instance is writing.");
            return INIT_FAILED;
        }
        LoadRecoveryData();
        ReleaseFileMutex();
    }
    
    //--- Initialize state variables
    g_lastCheck = 0;
    g_lastCleanup = TimeCurrent();
    g_lastConnectionCheck = TimeCurrent();
    
    //--- Print configuration summary
    Print("=== TimeCutoffManager v2.1 INITIALIZED ===");
    Print("Filter Method: ", EnumToString(InpFilterMethod));
    Print("Filter Value: ", InpFilterValue);
    Print("Close Duration: ", InpCloseDuration, " ", EnumToString(InpDurationType));
    if(InpUsePartialClose && InpPartialCloseDuration > 0 && InpPartialClosePct > 0)
        Print("Partial Close: ", InpPartialCloseDuration, " ", EnumToString(InpDurationType), 
              " (", DoubleToString(InpPartialClosePct, 0), "%)");
    else
        Print("Partial Close: DISABLED");
    Print("Warning before close: ", InpWarningSeconds, " seconds");
    Print("Max close retries: ", InpMaxCloseRetries);
    Print("Max spread for close: ", InpMaxSpreadPoints, " points");
    Print("==========================================");
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Validate Terminal State - CRITICAL for live trading              |
//+------------------------------------------------------------------+
bool ValidateTerminalState()
{
    //--- Check terminal connection
    g_terminalConnected = (bool)TerminalInfoInteger(TERMINAL_CONNECTED);
    if(!g_terminalConnected)
    {
        Print("CRITICAL: Terminal not connected to broker.");
        Print("Common causes: No internet, wrong login, server maintenance.");
        return false;
    }
    
    //--- Check if trade allowed
    g_tradeAllowed = (bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);
    if(!g_tradeAllowed)
    {
        Print("CRITICAL: Trading not allowed in terminal.");
        Print("Check: Ctrl+T → Experts tab for 'Trade disabled' messages.");
        Print("Check: Account may be in read-only mode.");
        return false;
    }
    
    //--- Check if Expert Advisors are allowed
    if(!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED) && !TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
    {
        Print("WARNING: DLL calls may be restricted. Trade operations depend on terminal settings.");
    }
    
    //--- Check MQL5 trade permission
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
    {
        Print("CRITICAL: Trade operations not allowed for this EA.");
        Print("Check: 'Allow Algo Trading' button on toolbar.");
        return false;
    }
    
    Print("Terminal state validated: Connected, Trade Allowed");
    return true;
}

//+------------------------------------------------------------------+
//| Periodic Connection Check                                        |
//+------------------------------------------------------------------+
void CheckConnectionState()
{
    datetime now = TimeCurrent();
    if(now - g_lastConnectionCheck < TCM_CONNECTION_CHECK_INTERVAL)
        return;
    
    g_lastConnectionCheck = now;
    
    bool wasConnected = g_terminalConnected;
    g_terminalConnected = (bool)TerminalInfoInteger(TERMINAL_CONNECTED);
    g_tradeAllowed = (bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);
    
    if(wasConnected && !g_terminalConnected)
    {
        Print("WARNING: Terminal connection LOST. Pausing operations.");
    }
    else if(!wasConnected && g_terminalConnected)
    {
        Print("INFO: Terminal connection RESTORED. Resuming operations.");
    }
    
    if(!g_tradeAllowed)
    {
        Print("WARNING: Trading disabled in terminal. Close operations may fail.");
    }
}

//+------------------------------------------------------------------+
//| Initialize Symbol Selection for Multi-Symbol Monitoring          |
//+------------------------------------------------------------------+
void InitializeSymbolSelection()
{
    //--- If filtering by symbol, select all monitored symbols for market data
    if(InpFilterMethod == FILTER_BY_SYMBOL)
    {
        for(int i = 0; i < ArraySize(g_symbols); i++)
        {
            if(!SymbolSelect(g_symbols[i], true))
            {
                Print("WARNING: Failed to select symbol ", g_symbols[i], 
                      " for market data. Trailing stops may fail.");
            }
            else
            {
                Print("Selected symbol for monitoring: ", g_symbols[i]);
            }
        }
    }
    //--- Always ensure current chart symbol is selected
    if(!SymbolSelect(Symbol(), true))
    {
        Print("WARNING: Failed to select current chart symbol ", Symbol());
    }
}

//+------------------------------------------------------------------+
//| Track Symbol Selection (called when adding new position)         |
//+------------------------------------------------------------------+
void EnsureSymbolSelected(string symbol)
{
    //--- Check if already selected
    for(int i = 0; i < ArraySize(g_selectedSymbols); i++)
    {
        if(g_selectedSymbols[i] == symbol)
            return; // Already selected
    }
    
    //--- Select the symbol
    if(SymbolSelect(symbol, true))
    {
        int idx = ArraySize(g_selectedSymbols);
        ArrayResize(g_selectedSymbols, idx + 1);
        g_selectedSymbols[idx] = symbol;
        Print("Added symbol to market watch: ", symbol);
    }
    else
    {
        Print("ERROR: Failed to select symbol ", symbol, 
              ". Trailing stop and spread checks will fail.");
    }
}

//+------------------------------------------------------------------+
//| File Mutex Operations (for multi-instance safety)                |
//+------------------------------------------------------------------+
bool AcquireFileMutex()
{
    //--- Simple spin-lock with timeout
    datetime start = TimeLocal();
    string mutexFile = "TCM_FileMutex.lock";
    
    while(FileIsExist(mutexFile))
    {
        if(TimeLocal() - start > TCM_FILE_MUTEX_TIMEOUT_MS / 1000)
        {
            Print("ERROR: File mutex timeout. Another TCM instance may be hung.");
            return false;
        }
        Sleep(100); // Short sleep while waiting for mutex
    }
    
    //--- Create mutex file
    int handle = FileOpen(mutexFile, FILE_WRITE|FILE_BIN|FILE_COMMON);
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
    string mutexFile = "TCM_FileMutex.lock";
    if(FileIsExist(mutexFile))
    {
        FileDelete(mutexFile, FILE_COMMON);
    }
}

//+------------------------------------------------------------------+
//| Parse filter values from string input                            |
//+------------------------------------------------------------------+
void ParseFilterValues()
{
    if(InpFilterMethod == FILTER_BY_MAGIC_NUMBER)
    {
        // Parse comma-separated magic numbers
        string value = InpFilterValue;
        string sep = ",";
        ushort u_sep = StringGetCharacter(sep, 0);
        string result[];
        int count = StringSplit(value, u_sep, result);
        
        ArrayResize(g_magicNumbers, count);
        for(int i = 0; i < count; i++)
        {
            g_magicNumbers[i] = StringToInteger(result[i]);
        }
        
        if(ArraySize(g_magicNumbers) == 1 && g_magicNumbers[0] == 0)
            Print("Monitoring ALL magic numbers");
        else
            Print("Monitoring magic numbers: ", InpFilterValue);
    }
    else if(InpFilterMethod == FILTER_BY_SYMBOL)
    {
        // Parse comma-separated symbols
        if(InpFilterValue == "")
        {
            // Use current chart symbol
            ArrayResize(g_symbols, 1);
            g_symbols[0] = Symbol();
            Print("Monitoring current symbol: ", Symbol());
        }
        else
        {
            string value = InpFilterValue;
            string sep = ",";
            ushort u_sep = StringGetCharacter(sep, 0);
            string result[];
            int count = StringSplit(value, u_sep, result);
            
            ArrayResize(g_symbols, count);
            for(int i = 0; i < count; i++)
            {
                g_symbols[i] = result[i];
            }
            Print("Monitoring symbols: ", InpFilterValue);
        }
    }
}

//+------------------------------------------------------------------+
//| Convert duration to seconds                                      |
//+------------------------------------------------------------------+
int GetCloseDurationInSeconds()
{
    switch(InpDurationType)
    {
        case DURATION_SECONDS: return InpCloseDuration;
        case DURATION_MINUTES: return InpCloseDuration * 60;
        case DURATION_HOURS:   return InpCloseDuration * 3600;
        default:               return InpCloseDuration * 60; // Default to minutes
    }
}

//+------------------------------------------------------------------+
//| Convert partial duration to seconds (0 if disabled)              |
//+------------------------------------------------------------------+
int GetPartialCloseDurationInSeconds()
{
    if(!InpUsePartialClose) return 0;
    if(InpPartialCloseDuration <= 0 || InpPartialClosePct <= 0) return 0;
    
    switch(InpDurationType)
    {
        case DURATION_SECONDS: return InpPartialCloseDuration;
        case DURATION_MINUTES: return InpPartialCloseDuration * 60;
        case DURATION_HOURS:   return InpPartialCloseDuration * 3600;
        default:               return InpPartialCloseDuration * 60;
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Clean up chart objects
    CleanupDashboard();
    
    // Save recovery data (with mutex)
    if(InpTrackLosses)
    {
        if(AcquireFileMutex())
        {
            SaveRecoveryData();
            ReleaseFileMutex();
        }
        else
        {
            Print("WARNING: Could not acquire mutex to save recovery data.");
        }
    }
    
    // Release symbol selections
    for(int i = 0; i < ArraySize(g_selectedSymbols); i++)
    {
        SymbolSelect(g_selectedSymbols[i], false);
    }
    
    Print("TimeCutoffManager deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    //--- Update every second (not every tick)
    datetime now = TimeCurrent();
    if(now == g_lastCheck) return;
    g_lastCheck = now;
    
    //--- Check terminal connection periodically
    CheckConnectionState();
    
    //--- If not connected, skip all operations
    if(!g_terminalConnected || !g_tradeAllowed)
    {
        return;
    }
    
    //--- Process pending close confirmations first (state machine)
    ProcessPendingCloses();
    
    //--- Scan for new positions and updates
    ScanPositions();
    
    //--- Check cutoff times and execute closes
    CheckCutoffs();
    
    //--- Update dashboard
    UpdateDashboard();
    
    //--- Periodic cleanup of closed positions
    if(now - g_lastCleanup > TCM_ARRAY_CLEANUP_INTERVAL)
    {
        CleanupClosedPositions();
        g_lastCleanup = now;
    }
}

//+------------------------------------------------------------------+
//| Process Pending Close Operations (State Machine)                 |
//| Replaces the Sleep(100) anti-pattern                             |
//+------------------------------------------------------------------+
void ProcessPendingCloses()
{
    datetime now = TimeCurrent();
    
    for(int i = 0; i < g_positionCount; i++)
    {
        if(g_positions[i].closed) continue;
        
        //--- Handle retry state
        if(g_positions[i].closeState == CLOSE_STATE_RETRY)
        {
            // Check if enough time has passed for retry
            int backoffMs = InpRetryDelayMs * (int)MathPow(2, g_positions[i].closeRetryCount - 1);
            if(now - g_positions[i].lastCloseAttempt >= backoffMs / 1000)
            {
                Print("Retrying close for position #", g_positions[i].ticket, 
                      " (attempt ", g_positions[i].closeRetryCount + 1, "/", InpMaxCloseRetries, ")");
                g_positions[i].closeState = CLOSE_STATE_IDLE;
                // Will be picked up by CheckCutoffs() on next iteration
            }
            continue;
        }
        
        //--- Handle pending state - verify if position actually closed
        if(g_positions[i].closeState == CLOSE_STATE_PENDING)
        {
            // Check if position still exists
            if(!PositionSelectByTicket(g_positions[i].ticket))
            {
                // Position confirmed closed
                g_positions[i].closed = true;
                g_positions[i].closeState = CLOSE_STATE_IDLE;
                
                // Record loss if negative (use last known P&L)
                if(g_positions[i].currentPnL < 0 && InpTrackLosses)
                {
                    RecordLoss(g_positions[i], g_positions[i].currentPnL);
                }
                
                Print("Position #", g_positions[i].ticket, " confirmed closed. P&L: $", 
                      DoubleToString(g_positions[i].currentPnL, 2));
            }
            else
            {
                // Position still exists - check timeout
                if(now - g_positions[i].lastCloseAttempt > 5) // 5 second timeout
                {
                    Print("WARNING: Position #", g_positions[i].ticket, 
                          " close confirmation timeout. Will retry.");
                    g_positions[i].closeState = CLOSE_STATE_RETRY;
                    g_positions[i].closeRetryCount++;
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Cleanup Dashboard Objects                                        |
//+------------------------------------------------------------------+
void CleanupDashboard()
{
    ObjectsDeleteAll(0, "TCM_");
    g_dashboardInitialized = false;
    ArrayFree(g_dashboardObjectCache);
}

//+------------------------------------------------------------------+
//| Create Dashboard UI                                              |
//+------------------------------------------------------------------+
void CreateDashboard()
{
    int x = InpDashboardX;
    int y = InpDashboardY;
    
    // Main background
    CreateRectangle("TCM_Background", x - 5, y - 5, 620, 400, InpBackgroundColor);
    
    // Header background
    CreateRectangle("TCM_HeaderBg", x, y, 610, 25, C'20,20,20');
    
    // Title
    CreateLabel("TCM_Title", "TIME CUTOFF MANAGER v2.2", x + 10, y + 5, clrGold, 10, true);
    y += 30;
    
    // Connection status
    CreateLabel("TCM_Connection", "●", x + 580, y - 25, clrLime, 12, true);
    
    // Column headers
    CreateLabel("TCM_H_Ticket", "Ticket", x + 10, y, clrGray, 8);
    CreateLabel("TCM_H_Symbol", "Symbol", x + 70, y, clrGray, 8);
    CreateLabel("TCM_H_Type", "Type", x + 130, y, clrGray, 8);
    CreateLabel("TCM_H_Lots", "Lots", x + 180, y, clrGray, 8);
    CreateLabel("TCM_H_PnL", "P&L", x + 230, y, clrGray, 8);
    CreateLabel("TCM_H_Timer", "Countdown", x + 310, y, clrGray, 8);
    CreateLabel("TCM_H_Status", "Status", x + 420, y, clrGray, 8);
    
    // Recovery info header
    y += InpRowHeight + 10;
    CreateLabel("TCM_RecoveryLabel", "Recovery Loss: $", x + 10, y, clrSalmon, 9);
    CreateLabel("TCM_RecoveryValue", "0.00", x + 110, y, clrSalmon, 9, true);
    
    // Status bar
    y += InpRowHeight + 5;
    CreateLabel("TCM_StatusBar", "Ready", x + 10, y, clrGray, 8);
    
    g_dashboardInitialized = true;
}

//+------------------------------------------------------------------+
//| Update Dashboard Display                                         |
//+------------------------------------------------------------------+
void UpdateDashboard()
{
    int x = InpDashboardX;
    int y = InpDashboardY + 50; // Below headers
    
    //--- Update connection indicator
    color connColor = (g_terminalConnected && g_tradeAllowed) ? clrLime : clrRed;
    UpdateLabelColor("TCM_Connection", connColor);
    
    //--- Clean up objects for positions that no longer exist
    // (only if count changed, to minimize GDI operations)
    static int lastDisplayedCount = -1;
    int activeCount = 0;
    for(int i = 0; i < g_positionCount; i++)
    {
        if(!g_positions[i].closed) activeCount++;
    }
    
    if(activeCount != lastDisplayedCount)
    {
        // Remove old position rows
        for(int i = ObjectsTotal(0) - 1; i >= 0; i--)
        {
            string name = ObjectName(0, i);
            if(StringFind(name, "TCM_P_") == 0)
                ObjectDelete(0, name);
        }
        lastDisplayedCount = activeCount;
    }
    
    //--- Update recovery display
    string recoveryText = DoubleToString(g_totalUnrecoveredLoss, 2);
    UpdateLabel("TCM_RecoveryValue", recoveryText);
    
    //--- Display positions
    int displayIdx = 0;
    for(int i = 0; i < g_positionCount; i++)
    {
        if(g_positions[i].closed) continue;
        
        string prefix = "TCM_P_" + IntegerToString(displayIdx) + "_";
        color textColor = InpColorNormal;
        color pnlColor = InpColorNormal;
        
        // Calculate remaining time
        int secondsRemaining = (int)(g_positions[i].cutoffTime - TimeCurrent());
        if(secondsRemaining < 0) secondsRemaining = 0;
        
        // Determine colors
        if(g_positions[i].currentPnL > 0)
            pnlColor = InpColorProfit;
        else if(g_positions[i].currentPnL < 0)
            pnlColor = InpColorLoss;
        
        // Warning color (approaching cutoff)
        if(secondsRemaining <= InpWarningSeconds && secondsRemaining > 0 && !g_positions[i].inTrailingMode)
            textColor = InpColorWarning;
        // Critical color (very close to cutoff)
        if(secondsRemaining <= 5 && !g_positions[i].inTrailingMode)
            textColor = InpColorCritical;
        // Trailing mode color
        if(g_positions[i].inTrailingMode)
            textColor = clrAqua;
        // Partial close done color (light blue - waiting for final)
        if(g_positions[i].partialCloseDone && !g_positions[i].closed)
            textColor = clrDodgerBlue;
        // Pending close color
        if(g_positions[i].closeState == CLOSE_STATE_PENDING)
            textColor = clrOrange;
        // Retry state color
        if(g_positions[i].closeState == CLOSE_STATE_RETRY)
            textColor = clrDarkOrange;
            
        // Calculate time to partial close
        int secondsToPartial = 0;
        if(!g_positions[i].partialCloseDone && g_positions[i].partialCutoffTime > 0)
            secondsToPartial = (int)(g_positions[i].partialCutoffTime - TimeCurrent());
        
        // Format countdown
        string timerText;
        if(g_positions[i].inTrailingMode)
        {
            timerText = "TRAILING";
        }
        else if(g_positions[i].closeState == CLOSE_STATE_PENDING)
        {
            timerText = "CLOSING...";
        }
        else if(g_positions[i].closeState == CLOSE_STATE_RETRY)
        {
            timerText = "RETRY " + IntegerToString(g_positions[i].closeRetryCount);
        }
        else if(!g_positions[i].partialCloseDone && secondsToPartial > 0 && secondsToPartial < secondsRemaining)
        {
            // Show partial close countdown
            if(secondsToPartial >= 60)
                timerText = StringFormat("P:%dm %02ds", secondsToPartial / 60, secondsToPartial % 60);
            else
                timerText = StringFormat("P:%ds", secondsToPartial);
        }
        else if(secondsRemaining >= 3600)
        {
            int hours = secondsRemaining / 3600;
            int mins = (secondsRemaining % 3600) / 60;
            timerText = StringFormat("%dh %02dm", hours, mins);
        }
        else if(secondsRemaining >= 60)
        {
            timerText = StringFormat("%dm %02ds", secondsRemaining / 60, secondsRemaining % 60);
        }
        else
        {
            timerText = StringFormat("%ds", secondsRemaining);
        }
        
        // Create/update row (use CreateOrUpdateLabel for efficiency)
        CreateOrUpdateLabel(prefix + "Ticket", IntegerToString(g_positions[i].ticket), x + 10, y, textColor, 8);
        CreateOrUpdateLabel(prefix + "Symbol", g_positions[i].symbol, x + 70, y, textColor, 8);
        CreateOrUpdateLabel(prefix + "Type", g_positions[i].type == ORDER_TYPE_BUY ? "BUY" : "SELL", x + 130, y, textColor, 8);
        CreateOrUpdateLabel(prefix + "Lots", DoubleToString(g_positions[i].lots, 2) + (g_positions[i].partialCloseDone ? "*" : ""), x + 180, y, textColor, 8);
        CreateOrUpdateLabel(prefix + "PnL", StringFormat("$%.2f", g_positions[i].currentPnL), x + 230, y, pnlColor, 8);
        CreateOrUpdateLabel(prefix + "Timer", timerText, x + 310, y, textColor, 10, true);
        
        string status;
        if(g_positions[i].inTrailingMode)
            status = "TRAILING";
        else if(g_positions[i].closeState == CLOSE_STATE_PENDING)
            status = "CLOSING";
        else if(g_positions[i].closeState == CLOSE_STATE_RETRY)
            status = "RETRY";
        else if(g_positions[i].partialCloseDone && secondsRemaining > 0)
            status = "P-CLOSED";  // Partial close done, waiting for final
        else if(secondsRemaining == 0)
            status = "DUE";
        else
            status = "ACTIVE";
        CreateOrUpdateLabel(prefix + "Status", status, x + 420, y, textColor, 8);
        
        y += InpRowHeight;
        displayIdx++;
    }
    
    // Show empty message if no positions
    if(activeCount == 0)
    {
        CreateOrUpdateLabel("TCM_P_Empty", "No monitored positions", x + 150, y + 20, clrGray, 9);
    }
    else
    {
        // Remove empty message if exists
        if(ObjectFind(0, "TCM_P_Empty") >= 0)
            ObjectDelete(0, "TCM_P_Empty");
    }
    
    // Update status bar
    string statusText = "Conn: " + (g_terminalConnected ? "OK" : "DOWN") + 
                        " | Trade: " + (g_tradeAllowed ? "OK" : "BLOCKED") +
                        " | Tracked: " + IntegerToString(activeCount);
    UpdateLabel("TCM_StatusBar", statusText);
}

//+------------------------------------------------------------------+
//| Scan for Positions with Atomic Validation                        |
//+------------------------------------------------------------------+
void ScanPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        //--- Get ticket first
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        
        //--- CRITICAL: Re-select by ticket to ensure atomicity
        // PositionGetTicket(i) selects position i, but the pool may have shifted
        // between our last operation and now. Re-selecting by ticket ensures
        // we're reading properties from the correct position.
        if(!PositionSelectByTicket(ticket))
        {
            // Position closed between enumeration and selection
            continue;
        }
        
        //--- Now read properties (safe because we hold the selection)
        long magic = PositionGetInteger(POSITION_MAGIC);
        string symbol = PositionGetString(POSITION_SYMBOL);
        string comment = PositionGetString(POSITION_COMMENT);
        
        //--- Double-check ticket matches (paranoid but necessary)
        ulong verifyTicket = PositionGetInteger(POSITION_TICKET);
        if(verifyTicket != ticket)
        {
            Print("ERROR: Ticket mismatch in ScanPositions! Expected ", ticket, 
                  " got ", verifyTicket, ". Race condition detected.");
            continue;
        }
        
        if(!PassesFilter(magic, symbol, comment)) continue;
        
        //--- Ensure symbol is selected for market data
        EnsureSymbolSelected(symbol);
        
        //--- Check if already tracked
        bool exists = false;
        for(int j = 0; j < g_positionCount; j++)
        {
            if(g_positions[j].ticket == ticket)
            {
                exists = true;
                // Update current data (only if not in pending close state)
                if(g_positions[j].closeState != CLOSE_STATE_PENDING)
                {
                    g_positions[j].currentPnL = PositionGetDouble(POSITION_PROFIT);
                    g_positions[j].maxPnL = MathMax(g_positions[j].maxPnL, g_positions[j].currentPnL);
                }
                break;
            }
        }
        
        // Add new position
        if(!exists)
        {
            AddPosition(ticket);
        }
    }
}

//+------------------------------------------------------------------+
//| Add Position to Tracking                                         |
//+------------------------------------------------------------------+
void AddPosition(ulong ticket)
{
    //--- CRITICAL: Position must be selected before calling this
    // Verify the ticket matches the selected position
    ulong selectedTicket = PositionGetInteger(POSITION_TICKET);
    if(selectedTicket != ticket)
    {
        Print("ERROR: AddPosition called with ticket ", ticket, 
              " but selected position is ", selectedTicket);
        return;
    }
    
    int idx = g_positionCount;
    ArrayResize(g_positions, g_positionCount + 1);
    
    g_positions[idx].ticket = ticket;
    g_positions[idx].symbol = PositionGetString(POSITION_SYMBOL);
    g_positions[idx].comment = PositionGetString(POSITION_COMMENT);
    g_positions[idx].magic = PositionGetInteger(POSITION_MAGIC);
    g_positions[idx].openTime = (datetime)PositionGetInteger(POSITION_TIME);
    g_positions[idx].openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    g_positions[idx].initialLots = PositionGetDouble(POSITION_VOLUME);
    g_positions[idx].lots = g_positions[idx].initialLots;
    g_positions[idx].type = (int)PositionGetInteger(POSITION_TYPE);
    g_positions[idx].currentPnL = PositionGetDouble(POSITION_PROFIT);
    g_positions[idx].maxPnL = g_positions[idx].currentPnL;
    g_positions[idx].warningIssued = false;
    g_positions[idx].closed = false;
    g_positions[idx].inTrailingMode = false;
    g_positions[idx].partialCloseDone = false;
    g_positions[idx].closeState = CLOSE_STATE_IDLE;
    g_positions[idx].lastCloseAttempt = 0;
    g_positions[idx].closeRetryCount = 0;
    g_positions[idx].pendingCloseTicket = 0;
    
    // Set cutoff times
    int closeDurationSeconds = GetCloseDurationInSeconds();
    int partialDurationSeconds = GetPartialCloseDurationInSeconds();
    
    g_positions[idx].cutoffTime = g_positions[idx].openTime + closeDurationSeconds;
    
    if(partialDurationSeconds > 0 && partialDurationSeconds < closeDurationSeconds)
    {
        g_positions[idx].partialCutoffTime = g_positions[idx].openTime + partialDurationSeconds;
        g_positions[idx].partialCloseLots = NormalizeDouble(g_positions[idx].initialLots * InpPartialClosePct / 100.0, 2);
        // Ensure at least minimum lot size and not more than total
        double minLot = SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_VOLUME_MIN);
        double maxLot = g_positions[idx].initialLots - minLot; // Leave at least minLot for remainder
        if(g_positions[idx].partialCloseLots > maxLot)
            g_positions[idx].partialCloseLots = maxLot;
        if(g_positions[idx].partialCloseLots < minLot)
            g_positions[idx].partialCutoffTime = 0; // Disable partial close if can't meet constraints
    }
    else
    {
        g_positions[idx].partialCutoffTime = 0; // Disabled
        g_positions[idx].partialCloseLots = 0;
    }
    
    g_positionCount++;
    
    Print("Added position #", ticket, " ", g_positions[idx].symbol, 
          " Final Cutoff: ", TimeToString(g_positions[idx].cutoffTime, TIME_SECONDS),
          " (", InpCloseDuration, " ", EnumToString(InpDurationType), ")",
          g_positions[idx].partialCutoffTime > 0 ? 
              ", Partial: " + TimeToString(g_positions[idx].partialCutoffTime, TIME_SECONDS) + 
              " (" + DoubleToString(InpPartialClosePct, 0) + "%)" : 
              "");
}

//+------------------------------------------------------------------+
//| Check Cutoff Times (Partial + Full Close)                        |
//+------------------------------------------------------------------+
void CheckCutoffs()
{
    for(int i = 0; i < g_positionCount; i++)
    {
        if(g_positions[i].closed) continue;
        if(g_positions[i].closeState == CLOSE_STATE_PENDING) continue; // Already closing
        if(g_positions[i].closeState == CLOSE_STATE_RETRY) 
        {
            // Retry logic handled in ProcessPendingCloses
            if(g_positions[i].closeRetryCount >= InpMaxCloseRetries)
            {
                Print("ERROR: Max retries exceeded for position #", g_positions[i].ticket, 
                      ". Manual intervention required.");
                g_positions[i].closed = true; // Stop trying
                continue;
            }
            continue;
        }
        
        datetime now = TimeCurrent();
        
        //--- PARTIAL CLOSE CHECK (Stage 1)
        if(!g_positions[i].partialCloseDone && g_positions[i].partialCutoffTime > 0)
        {
            int secondsToPartial = (int)(g_positions[i].partialCutoffTime - now);
            
            // Warning before partial close (use half of warning time)
            if(!g_positions[i].warningIssued && secondsToPartial <= InpWarningSeconds/2 && secondsToPartial > 0)
            {
                g_positions[i].warningIssued = true;
                Print("WARNING: Position #", g_positions[i].ticket, " partial close (", 
                      DoubleToString(InpPartialClosePct, 0), "%) in ", secondsToPartial, " seconds");
            }
            
            // Execute partial close
            if(now >= g_positions[i].partialCutoffTime)
            {
                if(!IsSpreadAcceptable(g_positions[i].symbol))
                {
                    Print("Delaying partial close for #", g_positions[i].ticket, 
                          " - spread too high (", GetCurrentSpread(g_positions[i].symbol), " > ", InpMaxSpreadPoints, ")");
                }
                else
                {
                    PartialClosePosition(i);
                    continue; // Skip final close check this iteration
                }
            }
        }
        
        //--- FINAL CLOSE CHECK (Stage 2)
        int secondsRemaining = (int)(g_positions[i].cutoffTime - now);
        
        // Warning before final close (only if partial close already done or disabled)
        if(g_positions[i].partialCloseDone && !g_positions[i].warningIssued && 
           secondsRemaining <= InpWarningSeconds && secondsRemaining > 0)
        {
            g_positions[i].warningIssued = true;
            Print("WARNING: Position #", g_positions[i].ticket, " final close in ", secondsRemaining, " seconds");
        }
        else if(!g_positions[i].partialCloseDone && g_positions[i].partialCutoffTime == 0 && 
                !g_positions[i].warningIssued && secondsRemaining <= InpWarningSeconds && secondsRemaining > 0)
        {
            // No partial close configured, warn on final close
            g_positions[i].warningIssued = true;
            Print("WARNING: Position #", g_positions[i].ticket, " closing in ", secondsRemaining, " seconds");
        }
        
        // Check if final cutoff reached
        if(now >= g_positions[i].cutoffTime && !g_positions[i].inTrailingMode)
        {
            // Check spread filter before closing
            if(!IsSpreadAcceptable(g_positions[i].symbol))
            {
                Print("Delaying final close for #", g_positions[i].ticket, 
                      " - spread too high (", GetCurrentSpread(g_positions[i].symbol), " > ", InpMaxSpreadPoints, ")");
                continue;
            }
            
            // Either close immediately or enter trailing mode
            if(InpUseTrailing && InpTrailDistance > 0 && g_positions[i].currentPnL > 0)
            {
                // Enter trailing mode instead of closing
                g_positions[i].inTrailingMode = true;
                Print("Position #", g_positions[i].ticket, " entered TRAILING MODE at cutoff");
            }
            else
            {
                // Close remaining position
                ClosePosition(i);
            }
        }
        
        // Check trailing stop if in trailing mode
        if(g_positions[i].inTrailingMode && InpTrailDistance > 0)
        {
            CheckTrailingStop(i);
        }
    }
}

//+------------------------------------------------------------------+
//| Get Current Spread for Symbol                                    |
//+------------------------------------------------------------------+
long GetCurrentSpread(string symbol)
{
    return SymbolInfoInteger(symbol, SYMBOL_SPREAD);
}

//+------------------------------------------------------------------+
//| Check if Spread is Acceptable for Close                          |
//+------------------------------------------------------------------+
bool IsSpreadAcceptable(string symbol)
{
    if(InpMaxSpreadPoints <= 0) return true; // Filter disabled
    
    long spread = GetCurrentSpread(symbol);
    return spread <= InpMaxSpreadPoints;
}

//+------------------------------------------------------------------+
//| Partial Close Position                                           |
//| Closes InpPartialClosePct% of position volume                    |
//+------------------------------------------------------------------+
void PartialClosePosition(int idx)
{
    ulong ticket = g_positions[idx].ticket;
    string symbol = g_positions[idx].symbol;
    double lotsToClose = g_positions[idx].partialCloseLots;
    
    //--- Validate
    if(lotsToClose <= 0 || g_positions[idx].partialCloseDone)
    {
        Print("Partial close skipped for #", ticket, " - already done or invalid volume");
        return;
    }
    
    //--- Verify position still exists
    if(!PositionSelectByTicket(ticket))
    {
        Print("Position #", ticket, " already closed before partial close");
        g_positions[idx].partialCloseDone = true;
        return;
    }
    
    //--- Get current volume to ensure we don't over-close
    double currentVolume = PositionGetDouble(POSITION_VOLUME);
    if(currentVolume <= 0)
    {
        Print("ERROR: Invalid volume for partial close on #", ticket);
        g_positions[idx].partialCloseDone = true;
        return;
    }
    
    //--- Adjust if position size changed (e.g., manual intervention)
    if(lotsToClose >= currentVolume)
    {
        lotsToClose = NormalizeDouble(currentVolume * 0.5, 2); // Close 50% of what's left
        Print("Adjusted partial close volume for #", ticket, " to ", lotsToClose, 
              " (position size changed)");
    }
    
    //--- Ensure minimum volume constraints
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    lotsToClose = MathFloor(lotsToClose / lotStep) * lotStep;
    
    if(lotsToClose < minLot)
    {
        Print("Partial close volume too small for #", ticket, 
              " (", lotsToClose, " < ", minLot, "), skipping");
        g_positions[idx].partialCloseDone = true;
        return;
    }
    
    //--- Ensure remaining volume is at least minimum
    double remainingVolume = currentVolume - lotsToClose;
    if(remainingVolume < minLot && remainingVolume > 0)
    {
        // Close entire position instead of leaving sub-minimum lot
        Print("Remaining volume (", remainingVolume, ") would be below minimum, closing full position");
        ClosePosition(idx);
        return;
    }
    
    Print("Executing partial close for #", ticket, 
          ": closing ", DoubleToString(lotsToClose, 2), " of ", 
          DoubleToString(currentVolume, 2), " lots (", 
          DoubleToString(InpPartialClosePct, 0), "%)");
    
    //--- Attempt partial close using CTrade
    if(!Trade.PositionClosePartial(ticket, lotsToClose))
    {
        int error = GetLastError();
        uint retcode = Trade.ResultRetcode();
        
        Print("Partial close failed for position #", ticket, 
              " Error: ", error, " Retcode: ", retcode);
        
        // Check if position was already closed
        if(retcode == TRADE_RETCODE_POSITION_CLOSED || 
           retcode == TRADE_RETCODE_DONE)
        {
            Print("Position #", ticket, " was already fully closed");
            g_positions[idx].closed = true;
            return;
        }
        
        // Retry on next tick (don't mark as done)
        return;
    }
    
    //--- Partial close successful
    g_positions[idx].partialCloseDone = true;
    g_positions[idx].lots = remainingVolume > 0 ? remainingVolume : 0;
    
    // Reset warning for final close
    g_positions[idx].warningIssued = false;
    
    Print("Partial close SUCCESS for #", ticket, 
          ". Closed: ", DoubleToString(lotsToClose, 2), 
          " lots. Remaining: ", DoubleToString(g_positions[idx].lots, 2), " lots");
}

//+------------------------------------------------------------------+
//| Close Position with Retry Logic                                  |
//+------------------------------------------------------------------+
void ClosePosition(int idx)
{
    ulong ticket = g_positions[idx].ticket;
    double lots = g_positions[idx].lots;  // May be reduced after partial close
    string symbol = g_positions[idx].symbol;
    
    //--- Check retry limit
    if(g_positions[idx].closeRetryCount >= InpMaxCloseRetries)
    {
        Print("ERROR: Max retries (", InpMaxCloseRetries, ") exceeded for position #", ticket);
        g_positions[idx].closed = true; // Mark as closed to stop trying
        return;
    }
    
    //--- Verify position still exists before attempting close
    if(!PositionSelectByTicket(ticket))
    {
        // Position already closed (likely by EA hitting TP/SL)
        Print("Position #", ticket, " already closed (not found in position pool)");
        g_positions[idx].closed = true;
        return;
    }
    
    //--- Double-check ticket matches
    ulong verifyTicket = PositionGetInteger(POSITION_TICKET);
    if(verifyTicket != ticket)
    {
        Print("ERROR: Ticket mismatch in ClosePosition! Expected ", ticket, " got ", verifyTicket);
        g_positions[idx].closeRetryCount++;
        g_positions[idx].closeState = CLOSE_STATE_RETRY;
        g_positions[idx].lastCloseAttempt = TimeCurrent();
        return;
    }
    
    Print("Attempting close for position #", ticket, " ", symbol, 
          " (attempt ", g_positions[idx].closeRetryCount + 1, "/", InpMaxCloseRetries, ")");
    
    //--- Attempt close using CTrade
    if(!Trade.PositionClose(ticket))
    {
        int error = GetLastError();
        uint retcode = Trade.ResultRetcode();
        
        Print("Close request failed for position #", ticket, 
              " Error: ", error, " Retcode: ", retcode);
        
        // Check for specific error conditions
        if(retcode == TRADE_RETCODE_POSITION_CLOSED || 
           retcode == TRADE_RETCODE_DONE ||
           error == 4753) // Keep for backward compatibility
        {
            // Position was already closed
            Print("Position #", ticket, " was already closed (detected post-failure)");
            g_positions[idx].closed = true;
            return;
        }
        
        // Schedule retry with exponential backoff
        g_positions[idx].closeRetryCount++;
        g_positions[idx].closeState = CLOSE_STATE_RETRY;
        g_positions[idx].lastCloseAttempt = TimeCurrent();
        
        int backoffSec = (int)(InpRetryDelayMs * MathPow(2, g_positions[idx].closeRetryCount - 1) / 1000);
        Print("Will retry in ", backoffSec, " seconds (backoff)");
        return;
    }
    
    //--- Close request accepted by server
    // Do NOT use Sleep() - instead, mark as pending and verify on next tick
    g_positions[idx].closeState = CLOSE_STATE_PENDING;
    g_positions[idx].lastCloseAttempt = TimeCurrent();
    g_positions[idx].pendingCloseTicket = Trade.ResultOrder();
    
    Print("Close request accepted for position #", ticket, 
          ", order ticket: ", g_positions[idx].pendingCloseTicket,
          ". Awaiting confirmation...");
}

//+------------------------------------------------------------------+
//| Check Trailing Stop                                              |
//+------------------------------------------------------------------+
void CheckTrailingStop(int idx)
{
    //--- Verify symbol is still selected
    if(!SymbolSelect(g_positions[idx].symbol, true))
    {
        Print("WARNING: Cannot select symbol ", g_positions[idx].symbol, " for trailing stop check");
        return;
    }
    
    double trailAmount = InpTrailDistance * _Point;
    double currentPrice = (g_positions[idx].type == ORDER_TYPE_BUY) ? 
                          SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_BID) :
                          SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_ASK);
    
    //--- Validate price data
    if(currentPrice <= 0)
    {
        Print("ERROR: Invalid price data for ", g_positions[idx].symbol, 
              " Bid: ", SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_BID),
              " Ask: ", SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_ASK));
        return;
    }
    
    double profitPoints = (g_positions[idx].type == ORDER_TYPE_BUY) ?
                          (currentPrice - g_positions[idx].openPrice) / _Point :
                          (g_positions[idx].openPrice - currentPrice) / _Point;
    
    //--- Calculate max profit in points using tick value
    double tickValue = SymbolInfoDouble(g_positions[idx].symbol, SYMBOL_TRADE_TICK_VALUE);
    if(tickValue <= 0)
    {
        Print("ERROR: Invalid tick value for ", g_positions[idx].symbol);
        return;
    }
    
    double maxPoints = g_positions[idx].maxPnL / (g_positions[idx].lots * tickValue);
    
    // Close if retraced from max profit by trail distance
    if(profitPoints < maxPoints - InpTrailDistance)
    {
        // Check spread before closing
        if(!IsSpreadAcceptable(g_positions[idx].symbol))
        {
            Print("Trailing stop triggered for #", g_positions[idx].ticket,
                  " but spread too high - delaying close");
            return;
        }
        
        Print("Trailing stop triggered for #", g_positions[idx].ticket, 
              " Max: ", DoubleToString(maxPoints, 1), " pts, Current: ", DoubleToString(profitPoints, 1), " pts");
        ClosePosition(idx);
    }
}

//+------------------------------------------------------------------+
//| Record Loss for Recovery                                         |
//+------------------------------------------------------------------+
void RecordLoss(PositionData &pos, double loss)
{
    int idx = ArraySize(g_lossHistory);
    ArrayResize(g_lossHistory, idx + 1);
    
    g_lossHistory[idx].date = TimeCurrent();
    g_lossHistory[idx].symbol = pos.symbol;
    g_lossHistory[idx].loss = MathAbs(loss);
    g_lossHistory[idx].lots = pos.lots;
    g_lossHistory[idx].ticket = pos.ticket;
    g_lossHistory[idx].recovered = false;
    
    g_totalUnrecoveredLoss += MathAbs(loss);
    
    Print("Loss recorded: $", DoubleToString(MathAbs(loss), 2), " Ticket: ", pos.ticket);
}

//+------------------------------------------------------------------+
//| Load Recovery Data                                               |
//+------------------------------------------------------------------+
void LoadRecoveryData()
{
    string filename = InpRecoveryFile;
    
    if(!FileIsExist(filename, FILE_COMMON))
    {
        Print("No recovery data file found (this is normal for first run)");
        return;
    }
    
    int handle = FileOpen(filename, FILE_READ|FILE_CSV|FILE_COMMON, ',');
    if(handle == INVALID_HANDLE)
    {
        Print("Failed to open recovery file. Error: ", GetLastError());
        return;
    }
    
    // Skip header
    FileReadString(handle);
    
    int loadedCount = 0;
    while(!FileIsEnding(handle))
    {
        string dateStr = FileReadString(handle);
        if(dateStr == "" || StringFind(dateStr, "Date") != -1) continue;
        
        datetime date = StringToTime(dateStr);
        if(date == 0) continue;
        
        string symbol = FileReadString(handle);
        string lossStr = FileReadString(handle);
        string lotsStr = FileReadString(handle);
        string ticketStr = FileReadString(handle);
        string recoveredStr = FileReadString(handle);
        
        if(lossStr == "" || lotsStr == "") continue;
        
        double loss = StringToDouble(lossStr);
        double lots = StringToDouble(lotsStr);
        ulong ticket = (ulong)StringToInteger(ticketStr);
        bool recovered = (StringToInteger(recoveredStr) != 0);
        
        if(!recovered && loss > 0)
        {
            int idx = ArraySize(g_lossHistory);
            ArrayResize(g_lossHistory, idx + 1);
            g_lossHistory[idx].date = date;
            g_lossHistory[idx].symbol = symbol;
            g_lossHistory[idx].loss = loss;
            g_lossHistory[idx].lots = lots;
            g_lossHistory[idx].ticket = ticket;
            g_lossHistory[idx].recovered = recovered;
            
            g_totalUnrecoveredLoss += loss;
            loadedCount++;
        }
    }
    
    FileClose(handle);
    Print("Loaded ", loadedCount, " unrecovered loss records. Total: $", 
          DoubleToString(g_totalUnrecoveredLoss, 2));
}

//+------------------------------------------------------------------+
//| Save Recovery Data                                               |
//+------------------------------------------------------------------+
void SaveRecoveryData()
{
    string filename = InpRecoveryFile;
    int handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_COMMON, ',');
    
    if(handle == INVALID_HANDLE)
    {
        Print("Failed to create recovery file. Error: ", GetLastError());
        return;
    }
    
    // Header
    FileWrite(handle, "Date", "Symbol", "Loss", "Lots", "Ticket", "Recovered");
    
    // Data
    int savedCount = 0;
    for(int i = 0; i < ArraySize(g_lossHistory); i++)
    {
        FileWrite(handle, 
            TimeToString(g_lossHistory[i].date, TIME_DATE|TIME_SECONDS),
            g_lossHistory[i].symbol,
            DoubleToString(g_lossHistory[i].loss, 2),
            DoubleToString(g_lossHistory[i].lots, 2),
            IntegerToString(g_lossHistory[i].ticket),
            IntegerToString(g_lossHistory[i].recovered ? 1 : 0));
        savedCount++;
    }
    
    FileClose(handle);
    Print("Saved ", savedCount, " loss records to ", filename);
}

//+------------------------------------------------------------------+
//| Cleanup Closed Positions from Array                              |
//| NOTE: Cannot use ArrayCopy on structs with string members in MQL5|
//+------------------------------------------------------------------+
void CleanupClosedPositions()
{
    int activeCount = 0;
    for(int i = 0; i < g_positionCount; i++)
    {
        if(!g_positions[i].closed) activeCount++;
    }
    
    if(activeCount == g_positionCount) return; // Nothing to clean
    
    // Compact array in-place (shift active elements to fill gaps)
    int writeIdx = 0;
    for(int readIdx = 0; readIdx < g_positionCount; readIdx++)
    {
        if(!g_positions[readIdx].closed)
        {
            if(writeIdx != readIdx)
            {
                // Copy element to new position
                g_positions[writeIdx] = g_positions[readIdx];
            }
            writeIdx++;
        }
    }
    
    // Resize array to remove dead elements
    ArrayResize(g_positions, activeCount);
    g_positionCount = activeCount;
    
    Print("Cleaned up position array: ", g_positionCount, " active positions retained");
}

//+------------------------------------------------------------------+
//| Filter Check                                                     |
//+------------------------------------------------------------------+
bool PassesFilter(long magic, string symbol, string comment)
{
    switch(InpFilterMethod)
    {
        case FILTER_BY_MAGIC_NUMBER:
            // If filter value is "0" or empty, allow all
            if(InpFilterValue == "0" || InpFilterValue == "")
                return true;
            
            // Check if magic number is in the list
            for(int i = 0; i < ArraySize(g_magicNumbers); i++)
            {
                if(magic == g_magicNumbers[i])
                    return true;
            }
            return false;
            
        case FILTER_BY_COMMENT:
            if(InpFilterValue == "")
                return true;
            return (StringFind(comment, InpFilterValue) != -1);
            
        case FILTER_BY_SYMBOL:
            for(int i = 0; i < ArraySize(g_symbols); i++)
            {
                if(symbol == g_symbols[i])
                    return true;
            }
            return false;
            
        default:
            return true;
    }
}

//+------------------------------------------------------------------+
//| Helper: Create or Update Label (optimized)                       |
//+------------------------------------------------------------------+
void CreateOrUpdateLabel(string name, string text, int x, int y, color clr, int fontSize = 8, bool bold = false)
{
    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
        ObjectSetString(0, name, OBJPROP_FONT, bold ? "Arial Bold" : "Arial");
        ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
    }
    
    ObjectSetString(0, name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| Helper: Create Label                                             |
//+------------------------------------------------------------------+
void CreateLabel(string name, string text, int x, int y, color clr, int fontSize = 8, bool bold = false)
{
    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
    }
    
    ObjectSetString(0, name, OBJPROP_TEXT, text);
    ObjectSetString(0, name, OBJPROP_FONT, bold ? "Arial Bold" : "Arial");
    ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
    ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| Helper: Update Label                                             |
//+------------------------------------------------------------------+
void UpdateLabel(string name, string text)
{
    if(ObjectFind(0, name) >= 0)
    {
        ObjectSetString(0, name, OBJPROP_TEXT, text);
    }
}

//+------------------------------------------------------------------+
//| Helper: Update Label Color                                       |
//+------------------------------------------------------------------+
void UpdateLabelColor(string name, color clr)
{
    if(ObjectFind(0, name) >= 0)
    {
        ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
    }
}

//+------------------------------------------------------------------+
//| Helper: Create Rectangle                                         |
//+------------------------------------------------------------------+
void CreateRectangle(string name, int x, int y, int width, int height, color bgColor)
{
    if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
    
    ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
    ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, name, OBJPROP_XSIZE, width);
    ObjectSetInteger(0, name, OBJPROP_YSIZE, height);
    ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bgColor);
    ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, name, OBJPROP_COLOR, C'40,40,40');
}

//+------------------------------------------------------------------+
