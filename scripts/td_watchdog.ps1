# td_watchdog.ps1 — Restart TouchDesigner if it stops running.
# Registered via setup_resilience.bat as a Task Scheduler task (SSD-TD-Watchdog).
# Runs silently in background; logs to Desktop\ssd_watchdog.log.
#
# Check interval: 2 minutes.
# After detecting TD is gone, waits 60s grace period before checking again
# (allows TD to fully load before the next check would re-trigger).

$TdExe  = "C:\Program Files\Derivative\TouchDesigner\TouchDesigner.exe"
$ToeFile = "C:\Users\user\Desktop\SalishSeaDreaming.toe"
$LogFile = "C:\Users\user\Desktop\ssd_watchdog.log"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg"
}

Write-Log "Watchdog started (PID $PID)"

while ($true) {
    Start-Sleep -Seconds 120

    $proc = Get-Process -Name "TouchDesigner" -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Log "TouchDesigner not running — restarting"
        if (Test-Path $ToeFile) {
            Start-Process $TdExe -ArgumentList "`"$ToeFile`""
            Write-Log "Launched: $TdExe `"$ToeFile`""
        } else {
            Start-Process $TdExe
            Write-Log "WARNING: .toe not found; launched TD without project file"
        }
        # Grace period — let TD load before next watchdog check
        Start-Sleep -Seconds 60
    }
}
