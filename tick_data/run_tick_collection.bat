@echo off
REM Tick Data Collection Scheduler
REM Run this every hour to collect tick data

cd /d "C:\Trading_GU"
python tick_storage_manager.py --fetch-today

REM Optional: Log execution
echo %date% %time% - Tick data fetch completed >> tick_data\collection.log
