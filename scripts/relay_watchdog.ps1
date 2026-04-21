# relay_watchdog.ps1 v2 -- Restart td_relay.py if it stops running.
#
# WHY: td_relay.py died silently tonight around 23:43 PDT (both Apr 17
# instances disappeared). health_probe.ps1 alerted but nothing auto-
# restarted it -- so visitor prompts would have stopped routing to TD
# until someone noticed. This closes that gap.
#
# Template-copy of the resolume_watchdog v2 pattern (heartbeat +
# exponential backoff + crash-loop guard + SingleInstance).
#
# Detection: Test-RelayRunning looks for python.exe processes whose
# CommandLine contains "td_relay.py". Matches both the streamdiffusion-
# env python AND Program Files Python310 (both of which were previously
# running in parallel).
#
# Check interval: 2 minutes.
# Heartbeat:      C:\Users\user\heartbeats\relay_watchdog.hb
# State:          C:\Users\user\relay_watchdog_state.json
# Log:            C:\Users\user\Desktop\ssd_relay_watchdog.log
#
# Revert: unregister SSD-Relay-Watchdog task; delete this file + state.
# td_relay.py itself is unaffected.

# SingleInstance guard
$myPid = $PID
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.CommandLine -like "*relay_watchdog.ps1*" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

$LogFile       = "C:\Users\user\Desktop\ssd_relay_watchdog.log"
$HeartbeatDir  = "C:\Users\user\heartbeats"
$HeartbeatFile = Join-Path $HeartbeatDir "relay_watchdog.hb"
$StateFile     = "C:\Users\user\relay_watchdog_state.json"

$MaxRestartsPerHour  = 5
$BackoffSchedule     = @(60, 120, 300, 600)
$StableThresholdSec  = 600
$RestartAfterFails   = 2   # consecutive failed detections before restart
                            # (Get-CimInstance can flake; require confirmation)

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

function Test-RelayRunning {
    try {
        $p = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*td_relay.py*" }
        return [bool]$p
    } catch {
        return $false
    }
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
    return @{ restart_timestamps = @(); consecutive_restarts = 0; disabled_until_human = $false; consecutive_fails = 0 }
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

Write-Log "relay_watchdog v2 started (PID $PID) -- max $MaxRestartsPerHour restarts/hr, backoff $($BackoffSchedule -join ',') s"

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
            Write-Log "relay stable for >$StableThresholdSec s since last restart - resetting consecutive counter"
            $state.consecutive_restarts = 0
        }
    }

    if (Test-RelayRunning) {
        if ($state.consecutive_fails -gt 0) {
            Write-Log "relay re-detected as running after $($state.consecutive_fails) transient fail(s); clearing fail counter"
            $state.consecutive_fails = 0
        }
        Save-State $state
        continue
    }

    # Not running: increment fail counter, require N consecutive before restart
    $state.consecutive_fails = $state.consecutive_fails + 1
    Write-Log "td_relay not detected (consecutive_fails=$($state.consecutive_fails), threshold=$RestartAfterFails)"
    if ($state.consecutive_fails -lt $RestartAfterFails) {
        Save-State $state
        continue
    }
    $state.consecutive_fails = 0

    if ($state.restart_timestamps.Count -ge $MaxRestartsPerHour) {
        Write-Log "crash loop detected: $($state.restart_timestamps.Count) restarts in last hour - DISABLING further restarts"
        Send-CriticalAlert "relay_watchdog_disabled" "td_relay.py crashed $($state.restart_timestamps.Count) times in the last hour. Watchdog disabled auto-restart. Manual intervention required."
        $state.disabled_until_human = $true
        Save-State $state
        continue
    }

    $restartIdx = [Math]::Min($state.consecutive_restarts, $BackoffSchedule.Length - 1)
    $backoff = $BackoffSchedule[$restartIdx]
    Write-Log "td_relay not running (restart #$($state.consecutive_restarts + 1) in window; backoff $backoff s)"

    & schtasks.exe /run /tn "SSD-Relay"
    $now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    $state.restart_timestamps = @($state.restart_timestamps + $now)
    $state.consecutive_restarts = $state.consecutive_restarts + 1
    Write-Log "Triggered SSD-Relay task at unix $now"
    Save-State $state

    Start-Sleep -Seconds $backoff
}
