//+------------------------------------------------------------------+
//|                                              GUM_CSVManager.mqh  |
//|                                     CSV file operations for GUM  |
//+------------------------------------------------------------------+
#ifndef GUM_CSVMANAGER_MQH
#define GUM_CSVMANAGER_MQH

#include "GUM_Structures.mqh"

//+------------------------------------------------------------------+
//| CSV Manager Class                                                 |
//+------------------------------------------------------------------+
class CGUM_CSVManager
{
private:
   string   m_fileName;
   bool     m_normalizeLots;
   string   m_dataFolder;
   int      m_fileHandle;
   bool     m_fileOpen;
   
   // CSV Header
   const string CSV_HEADER;
   
public:
   // Constructor
   CGUM_CSVManager() : 
      m_fileName("GUM_Positions.csv"),
      m_normalizeLots(true),
      m_dataFolder(""),
      m_fileHandle(INVALID_HANDLE),
      m_fileOpen(false),
      CSV_HEADER("Ticket,Symbol,Type,Session,MagicNumber,Comment,TimeOpen,PriceOpen,LotSize,LotSizeNormalized,Status,TimeClose,PriceClose,Profit,TimeRecovered")
   {
   }
   
   // Destructor
   ~CGUM_CSVManager()
   {
      CloseFile();
   }
   
   // Initialize
   bool Initialize(string fileName, bool normalizeLots)
   {
      m_fileName = fileName;
      m_normalizeLots = normalizeLots;
      // Use MQL5/Files folder relative to the terminal (syncable)
      m_dataFolder = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\";
      
      Print("GUM CSV Manager: Data folder = ", m_dataFolder);
      Print("GUM CSV Manager: File = ", m_fileName);
      
      // Create subdirectories if needed (e.g., "data\" in "data\\file.csv")
      string pathParts[];
      int parts = StringSplit(m_fileName, '\\', pathParts);
      if(parts > 1)
      {
         // Build path incrementally and create folders
         string currentPath = "";
         for(int i = 0; i < parts - 1; i++)
         {
            if(i > 0) currentPath += "\\";
            currentPath += pathParts[i];
            // Folder creation would need Windows API, skipping for now
         }
      }
      
      // Create file with header if it doesn't exist
      if(!FileIsExist(m_fileName))
      {
         if(!CreateFileWithHeader())
         {
            Print("ERROR: Failed to create CSV file");
            return false;
         }
      }
      
      return true;
   }
   
   // Create new file with header
   bool CreateFileWithHeader()
   {
      // Check if path contains drive letter (e.g., G:\...)
      // If yes, don't use FILE_COMMON
      bool hasDriveLetter = (StringFind(m_fileName, ":\\") == 1);
      
      int handle;
      if(hasDriveLetter)
      {
         // Full path provided - don't use FILE_COMMON
         handle = FileOpen(m_fileName, FILE_WRITE|FILE_CSV, ',');
         Print("Using full path: ", m_fileName);
      }
      else
      {
         // Relative path - use FILE_COMMON (default)
         handle = FileOpen(m_fileName, FILE_WRITE|FILE_CSV|FILE_COMMON, ',');
      }
      
      if(handle == INVALID_HANDLE)
      {
         Print("ERROR: FileOpen failed for ", m_fileName, ", error: ", GetLastError());
         return false;
      }
      
      FileWrite(handle, CSV_HEADER);
      FileClose(handle);
      
      Print("Created new CSV file: ", m_fileName);
      return true;
   }
   
   // Open file for reading
   bool OpenForRead()
   {
      CloseFile();
      bool hasDriveLetter = (StringFind(m_fileName, ":\\") == 1);
      
      if(hasDriveLetter)
         m_fileHandle = FileOpen(m_fileName, FILE_READ|FILE_CSV, ',');
      else
         m_fileHandle = FileOpen(m_fileName, FILE_READ|FILE_CSV|FILE_COMMON, ',');
         
      if(m_fileHandle == INVALID_HANDLE)
      {
         Print("ERROR: Failed to open CSV for reading, error: ", GetLastError());
         return false;
      }
      m_fileOpen = true;
      return true;
   }
   
   // Open file for appending
   bool OpenForAppend()
   {
      CloseFile();
      bool hasDriveLetter = (StringFind(m_fileName, ":\\") == 1);
      
      if(hasDriveLetter)
         m_fileHandle = FileOpen(m_fileName, FILE_READ|FILE_WRITE|FILE_CSV, ',');
      else
         m_fileHandle = FileOpen(m_fileName, FILE_READ|FILE_WRITE|FILE_CSV|FILE_COMMON, ',');
         
      if(m_fileHandle == INVALID_HANDLE)
      {
         Print("ERROR: Failed to open CSV for append, error: ", GetLastError());
         return false;
      }
      
      // Seek to end of file
      FileSeek(m_fileHandle, 0, SEEK_END);
      m_fileOpen = true;
      return true;
   }
   
   // Close file
   void CloseFile()
   {
      if(m_fileHandle != INVALID_HANDLE)
      {
         FileClose(m_fileHandle);
         m_fileHandle = INVALID_HANDLE;
         m_fileOpen = false;
      }
   }
   
   // Read all positions from CSV
   int ReadAllPositions(SPositionRecord &positions[])
   {
      ArrayResize(positions, 0);
      
      if(!OpenForRead()) return 0;
      
      int count = 0;
      
      // Skip header
      if(!FileIsEnding(m_fileHandle))
      {
         FileReadString(m_fileHandle);
      }
      
      // Read data rows
      while(!FileIsEnding(m_fileHandle))
      {
         SPositionRecord rec;
         rec.Initialize();
         
         // Read all columns
         // Ticket,Symbol,Type,Session,MagicNumber,Comment,TimeOpen,PriceOpen,LotSize,LotSizeNormalized,Status,TimeClose,PriceClose,Profit,TimeRecovered
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.Ticket = (ulong)StringToInteger(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.Symbol = FileReadString(m_fileHandle);
         
         if(FileIsEnding(m_fileHandle)) break;
         string typeStr = FileReadString(m_fileHandle);
         rec.Type = (typeStr == "BUY") ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
         
         if(FileIsEnding(m_fileHandle)) break;
         string sessionStr = FileReadString(m_fileHandle);
         if(sessionStr == "ASIA") rec.Session = GUM_SESSION_ASIA;
         else if(sessionStr == "LONDON") rec.Session = GUM_SESSION_LONDON;
         else if(sessionStr == "NY") rec.Session = GUM_SESSION_NY;
         else if(sessionStr == "FULL") rec.Session = GUM_SESSION_FULL;
         else rec.Session = GUM_SESSION_UNKNOWN;
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.MagicNumber = StringToInteger(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.Comment = FileReadString(m_fileHandle);
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.TimeOpen = (datetime)StringToInteger(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.PriceOpen = StringToDouble(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.LotSize = StringToDouble(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.LotSizeNormalized = StringToDouble(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         string statusStr = FileReadString(m_fileHandle);
         if(statusStr == "OPEN") rec.Status = GUM_STATUS_OPEN;
         else if(statusStr == "CLEAR") rec.Status = GUM_STATUS_CLEAR;
         else if(statusStr == "RECOVERY") rec.Status = GUM_STATUS_RECOVERY;
         else if(statusStr == "RECOVERED") rec.Status = GUM_STATUS_RECOVERED;
         else if(statusStr == "LOST") rec.Status = GUM_STATUS_LOST;
         else rec.Status = GUM_STATUS_OPEN;
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.TimeClose = (datetime)StringToInteger(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.PriceClose = StringToDouble(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.Profit = StringToDouble(FileReadString(m_fileHandle));
         
         if(FileIsEnding(m_fileHandle)) break;
         rec.TimeRecovered = (datetime)StringToInteger(FileReadString(m_fileHandle));
         
         // Add to array
         int size = ArraySize(positions);
         ArrayResize(positions, size + 1);
         positions[size] = rec;
         count++;
      }
      
      CloseFile();
      return count;
   }
   
   // Write position to CSV (append)
   bool WritePosition(SPositionRecord &rec)
   {
      if(!OpenForAppend()) return false;
      
      // Ensure normalized lots
      if(m_normalizeLots && rec.LotSizeNormalized == 0)
      {
         rec.LotSizeNormalized = rec.CalculateNormalizedLots();
      }
      
      FileWrite(m_fileHandle,
         rec.Ticket,
         rec.Symbol,
         rec.GetTypeString(),
         rec.GetSessionString(),
         rec.MagicNumber,
         rec.Comment,
         (long)rec.TimeOpen,
         rec.PriceOpen,
         rec.LotSize,
         rec.LotSizeNormalized,
         rec.GetStatusString(),
         (long)rec.TimeClose,
         rec.PriceClose,
         rec.Profit,
         (long)rec.TimeRecovered
      );
      
      CloseFile();
      return true;
   }
   
   // Update existing position in CSV
   bool UpdatePosition(SPositionRecord &rec)
   {
      // Read all positions
      SPositionRecord allPositions[];
      int totalCount = ReadAllPositions(allPositions);
      
      // Find and update the position
      bool found = false;
      for(int i = 0; i < totalCount; i++)
      {
         if(allPositions[i].Ticket == rec.Ticket)
         {
            allPositions[i] = rec;
            found = true;
            break;
         }
      }
      
      // If not found, add as new
      if(!found)
      {
         int size = ArraySize(allPositions);
         ArrayResize(allPositions, size + 1);
         allPositions[size] = rec;
         totalCount++;
      }
      
      // Rewrite entire file
      return WriteAllPositions(allPositions);
   }
   
   // Write all positions to CSV (overwrite)
   bool WriteAllPositions(SPositionRecord &positions[])
   {
      // Delete existing file and recreate
      bool hasDriveLetter = (StringFind(m_fileName, ":\\") == 1);
      
      if(FileIsExist(m_fileName))
      {
         FileDelete(m_fileName);
      }
      
      // Create new file with header
      int handle;
      if(hasDriveLetter)
         handle = FileOpen(m_fileName, FILE_WRITE|FILE_CSV, ',');
      else
         handle = FileOpen(m_fileName, FILE_WRITE|FILE_CSV|FILE_COMMON, ',');
         
      if(handle == INVALID_HANDLE)
      {
         Print("ERROR: Failed to create CSV for writing, error: ", GetLastError());
         return false;
      }
      
      // Write header
      FileWrite(handle, CSV_HEADER);
      
      // Write all positions
      int count = ArraySize(positions);
      for(int i = 0; i < count; i++)
      {
         SPositionRecord rec = positions[i];
         
         // Ensure normalized lots
         if(m_normalizeLots && rec.LotSizeNormalized == 0)
         {
            rec.LotSizeNormalized = rec.CalculateNormalizedLots();
         }
         
         FileWrite(handle,
            rec.Ticket,
            rec.Symbol,
            rec.GetTypeString(),
            rec.GetSessionString(),
            rec.MagicNumber,
            rec.Comment,
            (long)rec.TimeOpen,
            rec.PriceOpen,
            rec.LotSize,
            rec.LotSizeNormalized,
            rec.GetStatusString(),
            (long)rec.TimeClose,
            rec.PriceClose,
            rec.Profit,
            (long)rec.TimeRecovered
         );
      }
      
      FileClose(handle);
      return true;
   }
   
   // Get full file path for debugging
   string GetFullPath()
   {
      return m_dataFolder + m_fileName;
   }
};

#endif // GUM_CSVMANAGER_MQH
//+------------------------------------------------------------------+
