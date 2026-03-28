# Daily Analysis Runner - Execute all three QA daily analyses
# Usage: .\run-analysis.ps1 [YYYY-MM-DD]
# If no date provided, defaults to yesterday

param(
    [string]$Date = ""
)

# Determine target date
if ($Date -eq "") {
    $TargetDate = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
    Write-Host "No date provided - using yesterday: $TargetDate" -ForegroundColor Yellow
} else {
    $TargetDate = $Date
    Write-Host "Target date: $TargetDate" -ForegroundColor Cyan
}

# Validate date format
try {
    $null = [datetime]::ParseExact($TargetDate, "yyyy-MM-dd", $null)
} catch {
    Write-Host "[ERROR] Invalid date format. Use YYYY-MM-DD" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "="*60 -ForegroundColor Green
Write-Host "Daily Analysis Runner" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host "Target Date: $TargetDate"
Write-Host "Start Time:  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "="*60 -ForegroundColor Green

# Scripts to run
$Scripts = @(
    @{ File = "qa_daily_recovery.py"; Name = "RecoveryAnalysis" },
    @{ File = "qa_daily_time.py"; Name = "TimeAnalysis" },
    @{ File = "qa_daily_mae.py"; Name = "MAEAnalysis" }
)

$SuccessCount = 0
$TotalCount = $Scripts.Count

for ($i = 0; $i -lt $Scripts.Count; $i++) {
    $script = $Scripts[$i]
    $num = $i + 1
    
    Write-Host ""
    Write-Host "[$num/$TotalCount] Starting $($script.Name)..." -ForegroundColor Cyan
    Write-Host "-"*60 -ForegroundColor Gray
    
    $cmd = "python `"$($script.File)`" --date $TargetDate"
    
    Invoke-Expression $cmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] $($script.Name) completed" -ForegroundColor Green
        $SuccessCount++
    } else {
        Write-Host "[ERROR] $($script.Name) failed with code $LASTEXITCODE" -ForegroundColor Red
        Write-Host "[ABORT] Stopping due to failure" -ForegroundColor Red
        exit 1
    }
}

# Summary
$FileDate = $TargetDate -replace "-", ""

Write-Host ""
Write-Host "="*60 -ForegroundColor Green
Write-Host "RUN COMPLETE" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host "Completed: $SuccessCount/$TotalCount analyses"
Write-Host "End Time:  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""
Write-Host "Output Files:" -ForegroundColor Cyan
Write-Host "  data/${FileDate}_RecoveryAnalysis.xlsx"
Write-Host "  data/${FileDate}_TimeAnalysis.xlsx"
Write-Host "  data/${FileDate}_MAEAnalysis.xlsx"
Write-Host "="*60 -ForegroundColor Green

if ($SuccessCount -eq $TotalCount) {
    Write-Host ""
    Write-Host "[✓] All analyses completed successfully" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "[✗] Only $SuccessCount/$TotalCount analyses completed" -ForegroundColor Red
    exit 1
}
