@echo off
REM Daily Analysis Runner - Execute all three QA daily analyses
REM Usage: run-analysis [YYYY-MM-DD]
REM If no date provided, defaults to yesterday

echo ========================================
echo Daily Analysis Runner
echo ========================================
setlocal enabledelayedexpansion

REM Get date parameter or use default (yesterday)
set "TARGET_DATE=%~1"

if "%~1"=="" (
    echo No date provided - using yesterday (default)
    set "DATE_ARG="
) else (
    echo Target date: %~1
    set "DATE_ARG=--date %~1"
)

echo.
echo Starting analysis run at %date% %time%
echo ========================================

REM 1. Recovery Analysis
echo.
echo [1/3] Running RecoveryAnalysis...
python qa_daily_recovery.py !DATE_ARG!
if !errorlevel! neq 0 (
    echo [ERROR] RecoveryAnalysis failed with code !errorlevel!
    exit /b 1
)
echo [1/3] RecoveryAnalysis complete

REM 2. Time Analysis
echo.
echo [2/3] Running TimeAnalysis...
python qa_daily_time.py !DATE_ARG!
if !errorlevel! neq 0 (
    echo [ERROR] TimeAnalysis failed with code !errorlevel!
    exit /b 1
)
echo [2/3] TimeAnalysis complete

REM 3. MAE Analysis
echo.
echo [3/3] Running MAEAnalysis...
python qa_daily_mae.py !DATE_ARG!
if !errorlevel! neq 0 (
    echo [ERROR] MAEAnalysis failed with code !errorlevel!
    exit /b 1
)
echo [3/3] MAEAnalysis complete

echo.
echo ========================================
echo All analyses complete at %date% %time%
echo ========================================
echo.
echo Output files:
if "%~1"=="" (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (
        set yesterday=%%c%%a%%b
    )
    set /a day=!date:~7,2!-1
    echo   dataﾟYYYYMMDD_RecoveryAnalysis.xlsx
    echo   dataﾟYYYYMMDD_TimeAnalysis.xlsx
    echo   dataﾟYYYYMMDD_MAEAnalysis.xlsx
) else (
    set "file_date=%~1"
    set "file_date=!file_date:-=!"
    echo   dataﾟ!file_date!_RecoveryAnalysis.xlsx
    echo   dataﾟ!file_date!_TimeAnalysis.xlsx
    echo   dataﾟ!file_date!_MAEAnalysis.xlsx
)
echo.

endlocal
