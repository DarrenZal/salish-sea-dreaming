# resolume_watchdog.ps1 — Restart Resolume Arena if it stops running.
# Modeled on td_watchdog.ps1.
# Check interval: 2 minutes.
# After detecting Resolume is gone, restarts via SSD-Resolume task,
# then waits 120s grace period before next check.

$LogFile = "C:\Users\user\Desktop\ssd_resolume_watchdog.log"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg"
}

Write-Log "Resolume watchdog started (PID $PID)"

while ($true) {
    Start-Sleep -Seconds 120

    $proc = Get-Process -Name "Arena" -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Log "Resolume Arena not running - restarting via SSD-Resolume task"
        & schtasks.exe /run /tn "SSD-Resolume"
        Write-Log "Triggered SSD-Resolume task"
        # Grace period - let Resolume load before next check
        Start-Sleep -Seconds 120
    }
}
