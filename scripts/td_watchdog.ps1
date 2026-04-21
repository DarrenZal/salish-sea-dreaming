# td_watchdog.ps1 v2 -- Restart TouchDesigner if it stops running.
# Template-copy of resolume_watchdog.ps1 v2 (Apr 19 resilience-architecture plan),
# adapted for the TouchDesigner process + SSD-TouchDesigner launcher task.
# Same heartbeat / backoff / crash-loop / single-instance logic.
#
# Why replace the old td_watchdog.ps1 (Apr 7):
#   The original version had no heartbeat, no crash-loop guard, and no
#   single-instance protection. It silently stopped restarting TD
#   somewhere between Apr 16 and Apr 20 (same zombie pattern as the old
#   resolume_watchdog). With the meta-watchdog that reads
#   heartbeat_manifest.json coming online this week, we need this
#   script to write its own .hb file so the meta-watchdog can detect
#   if IT goes zombie.
#
# Check interval: 2 minutes.
# Heartbeat:      C:\Users\user\heartbeats\td_watchdog.hb
# State:          C:\Users\user\td_watchdog_state.json
# Log:            C:\Users\user\Desktop\ssd_td_watchdog.log
#
# Revert path: `git checkout <pre-v2-sha> -- scripts/td_watchdog.ps1`
# to restore the April 7 version; delete state file.

# SingleInstance guard -- kill older instances before proceeding.
$myPid = $PID
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.CommandLine -like "*td_watchdog.ps1*" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

$LogFile       = "C:\Users\user\Desktop\ssd_td_watchdog.log"
$HeartbeatDir  = "C:\Users\user\heartbeats"
$HeartbeatFile = Join-Path $HeartbeatDir "td_watchdog.hb"
$StateFile     = "C:\Users\user\td_watchdog_state.json"

$MaxRestartsPerHour = 5
$BackoffSchedule    = @(60, 120, 300, 600)
$StableThresholdSec = 600

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

function Test-TDRunning {
    $td = Get-Process -Name "TouchDesigner" -ErrorAction SilentlyContinue
    return [bool]$td
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

Write-Log "td_watchdog v2 started (PID $PID) -- max $MaxRestartsPerHour restarts/hr, backoff $($BackoffSchedule -join ',') s"

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
            Write-Log "TD stable for >$StableThresholdSec s since last restart - resetting consecutive counter"
            $state.consecutive_restarts = 0
        }
    }

    if (Test-TDRunning) {
        Save-State $state
        continue
    }

    if ($state.restart_timestamps.Count -ge $MaxRestartsPerHour) {
        Write-Log "crash loop detected: $($state.restart_timestamps.Count) restarts in last hour - DISABLING further restarts"
        Send-CriticalAlert "td_watchdog_disabled" "TouchDesigner crashed $($state.restart_timestamps.Count) times in the last hour. Watchdog disabled auto-restart. Manual intervention required."
        $state.disabled_until_human = $true
        Save-State $state
        continue
    }

    $restartIdx = [Math]::Min($state.consecutive_restarts, $BackoffSchedule.Length - 1)
    $backoff = $BackoffSchedule[$restartIdx]
    Write-Log "TD not running (restart #$($state.consecutive_restarts + 1) in window; backoff $backoff s)"

    & schtasks.exe /run /tn "SSD-TouchDesigner"
    $now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    $state.restart_timestamps = @($state.restart_timestamps + $now)
    $state.consecutive_restarts = $state.consecutive_restarts + 1
    Write-Log "Triggered SSD-TouchDesigner task at unix $now"
    Save-State $state

    Start-Sleep -Seconds $backoff
}
