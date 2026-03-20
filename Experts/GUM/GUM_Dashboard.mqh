//+------------------------------------------------------------------+
//|                                              GUM_Dashboard.mqh   |
//|                                       Visual dashboard for GUM   |
//+------------------------------------------------------------------+
#ifndef GUM_DASHBOARD_MQH
#define GUM_DASHBOARD_MQH

#include "GUM_Structures.mqh"

//+------------------------------------------------------------------+
//| Dashboard Class                                                   |
//+------------------------------------------------------------------+
class CGUM_Dashboard
{
private:
   // Settings
   int    m_x, m_y;
   int    m_rowHeight;
   color  m_bgColor, m_normalColor, m_warningColor, m_criticalColor;
   color  m_profitColor, m_lossColor, m_recoveryColor, m_recoveredColor, m_lostColor, m_clearColor;
   
   // Object names prefix
   string m_prefix;
   int    m_objectCount;
   
   // Dimensions
   int    m_panelWidth;
   int    m_headerHeight;
   int    m_rowCount;
   
public:
   // Constructor
   CGUM_Dashboard()
   {
      m_x = 10; m_y = 30;
      m_rowHeight = 20;
      m_bgColor = C'30,30,30';
      m_normalColor = clrWhite;
      m_warningColor = clrYellow;
      m_criticalColor = clrRed;
      m_profitColor = clrLime;
      m_lossColor = clrSalmon;
      m_recoveryColor = clrOrange;
      m_recoveredColor = clrGreen;
      m_lostColor = clrGray;
      m_clearColor = clrAqua;
      m_prefix = "GUM_";
      m_objectCount = 0;
      m_panelWidth = 700;
      m_headerHeight = 60;
      m_rowCount = 0;
   }
   
   // Initialize
   void Initialize(
      int x, int y, int rowHeight,
      color bg, color normal, color warning, color critical,
      color profit, color loss, color recovery, color recovered, color lost, color clear
   )
   {
      m_x = x; m_y = y;
      m_rowHeight = rowHeight;
      m_bgColor = bg;
      m_normalColor = normal;
      m_warningColor = warning;
      m_criticalColor = critical;
      m_profitColor = profit;
      m_lossColor = loss;
      m_recoveryColor = recovery;
      m_recoveredColor = recovered;
      m_lostColor = lost;
      m_clearColor = clear;
   }
   
   // Create dashboard
   void Create()
   {
      Destroy(); // Clean up first
      
      // Main background panel
      CreateRectangle("Panel", m_x, m_y, m_panelWidth, m_headerHeight, m_bgColor, BORDER_FLAT);
      
      // Title
      CreateLabel("Title", m_x + 10, m_y + 5, "GU MANAGER (GUM)", m_normalColor, 12, true);
      
      // Column headers for active positions
      int colY = m_y + 35;
      CreateLabel("H_Ticket", m_x + 10, colY, "Ticket", m_normalColor, 9);
      CreateLabel("H_Symbol", m_x + 70, colY, "Symbol", m_normalColor, 9);
      CreateLabel("H_Type", m_x + 130, colY, "Type", m_normalColor, 9);
      CreateLabel("H_Lots", m_x + 180, colY, "Lots", m_normalColor, 9);
      CreateLabel("H_PnL", m_x + 230, colY, "P&L", m_normalColor, 9);
      CreateLabel("H_Countdown", m_x + 300, colY, "Time/Cutoff", m_normalColor, 9);
      CreateLabel("H_Status", m_x + 400, colY, "Status", m_normalColor, 9);
      CreateLabel("H_Session", m_x + 480, colY, "Session", m_normalColor, 9);
      
      m_objectCount = 10; // Base objects
   }
   
   // Destroy all objects
   void Destroy()
   {
      ObjectsDeleteAll(0, m_prefix);
      m_objectCount = 0;
   }
   
   // Update dashboard
   void Update(SPositionRecord &activePositions[], SPositionRecord &recoveryPositions[], int warningSeconds)
   {
      datetime now = TimeCurrent();
      
      // Clear previous rows
      for(int i = m_objectCount; i < 200; i++)
      {
         string objName = m_prefix + "Row_" + IntegerToString(i);
         if(ObjectFind(0, objName) >= 0)
            ObjectDelete(0, objName);
      }
      
      int currentObj = m_objectCount;
      int rowY = m_y + m_headerHeight;
      
      // Update panel size
      int totalRows = ArraySize(activePositions) + (ArraySize(recoveryPositions) > 0 ? ArraySize(recoveryPositions) + 1 : 0);
      int panelHeight = m_headerHeight + (totalRows * m_rowHeight) + 10;
      ObjectSetInteger(0, m_prefix + "Panel", OBJPROP_YSIZE, panelHeight);
      
      // === ACTIVE POSITIONS SECTION ===
      int activeCount = ArraySize(activePositions);
      for(int i = 0; i < activeCount; i++)
      {
         SPositionRecord rec = activePositions[i];
         
         // Background for row
         color rowColor = m_bgColor;
         if(rec.Status == GUM_STATUS_CLEAR)
            rowColor = C'20,40,40'; // Slightly tinted for CLEAR
         CreateRectangle("Row_" + IntegerToString(currentObj++), m_x + 5, rowY, m_panelWidth - 10, m_rowHeight - 2, rowColor, BORDER_FLAT);
         
         // Determine colors
         color pnlColor = (rec.Profit >= 0) ? m_profitColor : m_lossColor;
         color statusColor = GetStatusColor(rec.Status);
         
         // Countdown/cutoff text
         string timeText;
         color timeColor = m_normalColor;
         
         if(rec.Status == GUM_STATUS_CLEAR)
         {
            timeText = "CLEAR";
            timeColor = m_clearColor;
         }
         else
         {
            int secondsToCutoff = (int)(rec.CutoffTime - now);
            if(secondsToCutoff > 0)
            {
               timeText = FormatDuration(secondsToCutoff);
               if(secondsToCutoff <= 5)
                  timeColor = m_criticalColor;
               else if(secondsToCutoff <= warningSeconds)
                  timeColor = m_warningColor;
            }
            else if(rec.IsTrailing)
            {
               timeText = "TRAILING";
               timeColor = m_clearColor;
            }
            else
            {
               timeText = "CUTOFF";
               timeColor = m_criticalColor;
            }
         }
         
         // Row data
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 10, rowY + 2, 
                    IntegerToString((int)rec.Ticket), m_normalColor, 9);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 70, rowY + 2, 
                    rec.Symbol, m_normalColor, 9);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 130, rowY + 2, 
                    rec.GetTypeString(), m_normalColor, 9);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 180, rowY + 2, 
                    StringFormat("%.2f", rec.LotSize), m_normalColor, 9);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 230, rowY + 2, 
                    StringFormat("$%.2f", rec.Profit), pnlColor, 9);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 300, rowY + 2, 
                    timeText, timeColor, 9);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 400, rowY + 2, 
                    rec.GetStatusString(), statusColor, 9);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 480, rowY + 2, 
                    rec.GetSessionString(), m_normalColor, 9);
         
         rowY += m_rowHeight;
      }
      
      // === RECOVERY MONITOR SECTION ===
      int recoveryCount = ArraySize(recoveryPositions);
      if(recoveryCount > 0)
      {
         // Separator
         rowY += 5;
         CreateRectangle("Row_" + IntegerToString(currentObj++), m_x + 5, rowY, m_panelWidth - 10, 2, C'100,100,100', BORDER_FLAT);
         rowY += 5;
         
         // Section header
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 10, rowY, 
                    "RECOVERY MONITOR (" + IntegerToString(recoveryCount) + ")", m_recoveryColor, 10, true);
         rowY += m_rowHeight;
         
         // Recovery column headers
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 10, rowY, "Ticket", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 70, rowY, "Symbol", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 130, rowY, "Type", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 180, rowY, "OpenPrice", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 260, rowY, "ClosePrice", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 340, rowY, "Elapsed", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 420, rowY, "Remaining", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 510, rowY, "Current", m_normalColor, 8);
         CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 580, rowY, "Status", m_normalColor, 8);
         rowY += m_rowHeight;
         
         // Recovery rows
         for(int i = 0; i < recoveryCount; i++)
         {
            SPositionRecord rec = recoveryPositions[i];
            
            // Calculate elapsed and remaining time
            int elapsedSeconds = (int)(now - rec.TimeClose);
            int recoveryHours = GetRecoveryHoursForSessionStatic(rec.Session);
            int recoverySeconds = recoveryHours * 3600;
            int remainingSeconds = recoverySeconds - elapsedSeconds;
            
            color elapsedColor = (remainingSeconds < 3600) ? m_warningColor : m_normalColor;
            if(remainingSeconds < 0) elapsedColor = m_criticalColor;
            
            // Current price vs PriceOpen
            double currentPrice = (rec.Type == POSITION_TYPE_BUY) ?
                                 SymbolInfoDouble(rec.Symbol, SYMBOL_BID) :
                                 SymbolInfoDouble(rec.Symbol, SYMBOL_ASK);
            double distance = (rec.Type == POSITION_TYPE_BUY) ? 
                             (currentPrice - rec.PriceOpen) : 
                             (rec.PriceOpen - currentPrice);
            color priceColor = (distance >= 0) ? m_profitColor : m_lossColor;
            
            CreateRectangle("Row_" + IntegerToString(currentObj++), m_x + 5, rowY, m_panelWidth - 10, m_rowHeight - 2, C'40,30,20', BORDER_FLAT);
            
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 10, rowY + 2, 
                       IntegerToString((int)rec.Ticket), m_normalColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 70, rowY + 2, 
                       rec.Symbol, m_normalColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 130, rowY + 2, 
                       rec.GetTypeString(), m_normalColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 180, rowY + 2, 
                       StringFormat("%.2f", rec.PriceOpen), m_normalColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 260, rowY + 2, 
                       StringFormat("%.2f", rec.PriceClose), m_lossColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 340, rowY + 2, 
                       FormatDuration(elapsedSeconds), elapsedColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 420, rowY + 2, 
                       FormatDuration(remainingSeconds), elapsedColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 510, rowY + 2, 
                       StringFormat("%.2f", currentPrice), priceColor, 8);
            CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 580, rowY + 2, 
                       "MONITORING", m_recoveryColor, 8);
            
            rowY += m_rowHeight;
         }
      }
      
      // === STATISTICS FOOTER ===
      rowY += 10;
      CreateRectangle("Row_" + IntegerToString(currentObj++), m_x + 5, rowY, m_panelWidth - 10, m_rowHeight, C'20,20,20', BORDER_FLAT);
      
      string statsText = StringFormat("Active: %d | Recovery: %d", activeCount, recoveryCount);
      CreateLabel("Row_" + IntegerToString(currentObj++), m_x + 10, rowY + 2, statsText, m_normalColor, 9);
   }
   
   // Helper: Create rectangle
   void CreateRectangle(string name, int x, int y, int width, int height, color clr, ENUM_BORDER_TYPE border)
   {
      string fullName = m_prefix + name;
      if(ObjectCreate(0, fullName, OBJ_RECTANGLE_LABEL, 0, 0, 0))
      {
         ObjectSetInteger(0, fullName, OBJPROP_XDISTANCE, x);
         ObjectSetInteger(0, fullName, OBJPROP_YDISTANCE, y);
         ObjectSetInteger(0, fullName, OBJPROP_XSIZE, width);
         ObjectSetInteger(0, fullName, OBJPROP_YSIZE, height);
         ObjectSetInteger(0, fullName, OBJPROP_BGCOLOR, clr);
         ObjectSetInteger(0, fullName, OBJPROP_BORDER_TYPE, border);
         ObjectSetInteger(0, fullName, OBJPROP_COLOR, clr);
         ObjectSetInteger(0, fullName, OBJPROP_BACK, false);
      }
   }
   
   // Helper: Create label
   void CreateLabel(string name, int x, int y, string text, color clr, int fontSize, bool bold = false)
   {
      string fullName = m_prefix + name;
      if(ObjectCreate(0, fullName, OBJ_LABEL, 0, 0, 0))
      {
         ObjectSetInteger(0, fullName, OBJPROP_XDISTANCE, x);
         ObjectSetInteger(0, fullName, OBJPROP_YDISTANCE, y);
         ObjectSetString(0, fullName, OBJPROP_TEXT, text);
         ObjectSetInteger(0, fullName, OBJPROP_COLOR, clr);
         ObjectSetInteger(0, fullName, OBJPROP_FONTSIZE, fontSize);
         ObjectSetString(0, fullName, OBJPROP_FONT, bold ? "Arial Bold" : "Arial");
         ObjectSetInteger(0, fullName, OBJPROP_BACK, false);
      }
   }
   
   // Helper: Get color for status
   color GetStatusColor(ENUM_GUM_STATUS status)
   {
      switch(status)
      {
         case GUM_STATUS_OPEN:      return m_normalColor;
         case GUM_STATUS_CLEAR:     return m_clearColor;
         case GUM_STATUS_RECOVERY:  return m_recoveryColor;
         case GUM_STATUS_RECOVERED: return m_recoveredColor;
         case GUM_STATUS_LOST:      return m_lostColor;
         default:                   return m_normalColor;
      }
   }
   
   // Static helper for recovery hours
   static int GetRecoveryHoursForSessionStatic(ENUM_GUM_SESSION session)
   {
      // Default to 4 hours - in real implementation would access settings
      return 4;
   }
};

#endif // GUM_DASHBOARD_MQH
//+------------------------------------------------------------------+
