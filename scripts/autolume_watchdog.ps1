# autolume_watchdog.ps1 — Restart Autolume if it stops running.
# Mirrors the SSD-TD-Watchdog pattern.
#
# Check interval: 2 minutes.
# After detecting Autolume is gone, waits 120s grace period before checking again
# so it can fully load (GPU init + model load) before the next watchdog tick.

$LogFile = "C:\Users\user\Desktop\ssd_autolume_watchdog.log"
$ProcessNames = @("Autolume", "python")  # Autolume.exe or python.exe running autolume

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg"
}

function Test-AutolumeRunning {
    # Autolume can appear as either Autolume.exe (PyInstaller bundle) OR as
    # python.exe running autolume_autostart.py. Check both.
    $autolumeExe = Get-Process -Name "Autolume" -ErrorAction SilentlyContinue
    if ($autolumeExe) { return $true }

    $py = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue
    foreach ($p in $py) {
        if ($p.CommandLine -match "autolume") { return $true }
    }
    return $false
}

Write-Log "Autolume watchdog started (PID $PID)"

while ($true) {
    Start-Sleep -Seconds 120

    if (-not (Test-AutolumeRunning)) {
        Write-Log "Autolume not running - restarting via SSD-Autolume task"
        & schtasks.exe /run /tn "SSD-Autolume"
        Write-Log "Triggered SSD-Autolume task"
        # Grace period for GPU init + model load.
        Start-Sleep -Seconds 120
    }
}
