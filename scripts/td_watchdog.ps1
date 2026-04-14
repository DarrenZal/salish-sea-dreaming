# td_watchdog.ps1 — Restart TouchDesigner if it stops running.
# Registered via setup_resilience.bat as a Task Scheduler task (SSD-TD-Watchdog).
# Runs silently in background; logs to Desktop\ssd_watchdog.log.
#
# Check interval: 2 minutes.
# After detecting TD is gone, waits 60s grace period before checking again
# (allows TD to fully load before the next check would re-trigger).

$TdExe  = "C:\Program Files\Derivative\TouchDesigner.2025.32460\bin\TouchDesigner.exe"
$ToeFile = "C:\Users\user\Desktop\SSD-exhibition.toe"
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
        Write-Log "TouchDesigner not running - restarting via SSD-TouchDesigner task"
        # Use schtasks /run instead of Start-Process so TD launches in the
        # interactive user session (session 1) rather than the watchdog's
        # background session (session 0) where the TD GUI cannot initialise.
        & schtasks.exe /run /tn "SSD-TouchDesigner"
        Write-Log "Triggered SSD-TouchDesigner task"
        # Grace period - let TD load before next watchdog check
        Start-Sleep -Seconds 120
    }
}
