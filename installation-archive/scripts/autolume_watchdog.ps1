# autolume_watchdog.ps1 v2 -- Restart Autolume if it stops running.
# Template-copy of resolume_watchdog.ps1 v2, adapted for Autolume.
# Autolume can appear as either Autolume.exe (PyInstaller bundle) OR as
# python.exe running autolume_autostart.py; Test-AutolumeRunning checks
# both. Same heartbeat / backoff / crash-loop / single-instance logic.
#
# Why replace the old autolume_watchdog.ps1 (Apr 12):
#   The April 12 version had no heartbeat, no crash-loop guard, and no
#   single-instance protection. Matches the zombie pattern from old
#   td_watchdog + resolume_watchdog. Bringing it to parity with the
#   v2 pattern so the meta-watchdog (Wed) can detect stalled watchdogs.
#
# Check interval: 2 minutes.
# Heartbeat:      C:\Users\user\heartbeats\autolume_watchdog.hb
# State:          C:\Users\user\autolume_watchdog_state.json
# Log:            C:\Users\user\Desktop\ssd_autolume_watchdog.log
#
# Revert: `git checkout <pre-v2-sha> -- scripts/autolume_watchdog.ps1`
# to restore April 12 version; delete state file.

# SingleInstance guard
$myPid = $PID
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.CommandLine -like "*autolume_watchdog.ps1*" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

$LogFile       = "C:\Users\user\Desktop\ssd_autolume_watchdog.log"
$HeartbeatDir  = "C:\Users\user\heartbeats"
$HeartbeatFile = Join-Path $HeartbeatDir "autolume_watchdog.hb"
$StateFile     = "C:\Users\user\autolume_watchdog_state.json"

$MaxRestartsPerHour = 5
$BackoffSchedule    = @(120, 240, 600, 1200)   # longer than TD/Resolume -- Autolume startup is slow (GPU + 347MB pkl load)
$StableThresholdSec = 900                       # 15 min stability counts as recovered

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg" -ErrorAction SilentlyContinue
}

function Write-Heartbeat {
    try {
        if (-not (Test-Path $HeartbeatDir)) {
            New-Item -ItemType Directory -Path $HeartbeatDir -Force | Out-Null
        }
        Set-Content -Path $HeartbeatFile -Value (Get-Date -Format "o") -ErrorAction SilentlyContinue
    } catch {}
}

function Test-AutolumeRunning {
    # Autolume can appear as Autolume.exe (PyInstaller bundle) OR python.exe
    # running autolume_autostart.py. Also check for autolume multiprocessing
    # workers (children of Autolume.exe).
    $autolumeExe = Get-Process -Name "Autolume" -ErrorAction SilentlyContinue
    if ($autolumeExe) { return $true }

    try {
        $py = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue
        foreach ($p in $py) {
            if ($p.CommandLine -match "autolume") { return $true }
        }
    } catch {}
    return $false
}

function Load-State {
    if (Test-Path $StateFile) {
        try {
            $obj = Get-Content $StateFile -Raw | ConvertFrom-Json
            return @{
                restart_timestamps   = @($obj.restart_timestamps)
                consecutive_restarts = [int]$obj.consecutive_restarts
                disabled_until_human = [bool]$obj.disabled_until_human
            }
        } catch {}
    }
    return @{ restart_timestamps = @(); consecutive_restarts = 0; disabled_until_human = $false }
}

function Save-State($state) {
    try {
        ($state | ConvertTo-Json -Compress) | Set-Content -Path $StateFile -Encoding UTF8
    } catch {}
}

function Send-CriticalAlert($key, $message) {
    $notifier = "C:\Users\user\ssd_notify.ps1"
    if (Test-Path $notifier) {
        try {
            . $notifier
            Send-SSDAlert -Key $key -Severity "CRITICAL" -Message $message | Out-Null
        } catch {
            Write-Log "failed to send alert: $_"
        }
    }
}

Write-Log "autolume_watchdog v2 started (PID $PID) -- max $MaxRestartsPerHour restarts/hr, backoff $($BackoffSchedule -join ',') s"

while ($true) {
    Write-Heartbeat
    Start-Sleep -Seconds 120

    $state = Load-State
    if ($state.disabled_until_human) { continue }

    $cutoff = [DateTimeOffset]::Now.ToUnixTimeSeconds() - 3600
    $state.restart_timestamps = @($state.restart_timestamps | Where-Object { [int64]$_ -gt $cutoff })

    if ($state.restart_timestamps.Count -gt 0 -and $state.consecutive_restarts -gt 0) {
        $lastRestart = [int64]($state.restart_timestamps[-1])
        if (([DateTimeOffset]::Now.ToUnixTimeSeconds() - $lastRestart) -ge $StableThresholdSec) {
            Write-Log "Autolume stable for >$StableThresholdSec s since last restart - resetting consecutive counter"
            $state.consecutive_restarts = 0
        }
    }

    if (Test-AutolumeRunning) {
        Save-State $state
        continue
    }

    if ($state.restart_timestamps.Count -ge $MaxRestartsPerHour) {
        Write-Log "crash loop detected: $($state.restart_timestamps.Count) restarts in last hour - DISABLING further restarts"
        Send-CriticalAlert "autolume_watchdog_disabled" "Autolume crashed $($state.restart_timestamps.Count) times in the last hour. Watchdog disabled auto-restart. Manual intervention required."
        $state.disabled_until_human = $true
        Save-State $state
        continue
    }

    $restartIdx = [Math]::Min($state.consecutive_restarts, $BackoffSchedule.Length - 1)
    $backoff = $BackoffSchedule[$restartIdx]
    Write-Log "Autolume not running (restart #$($state.consecutive_restarts + 1) in window; backoff $backoff s)"

    & schtasks.exe /run /tn "SSD-Autolume"
    $now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    $state.restart_timestamps = @($state.restart_timestamps + $now)
    $state.consecutive_restarts = $state.consecutive_restarts + 1
    Write-Log "Triggered SSD-Autolume task at unix $now"
    Save-State $state

    Start-Sleep -Seconds $backoff
}
