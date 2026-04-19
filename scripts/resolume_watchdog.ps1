# resolume_watchdog.ps1 -- Restart Resolume Arena if it stops running.
# Modeled on td_watchdog.ps1, with two additions from the Apr 19
# post-incident resilience plan:
#   1. Heartbeat file write every loop so meta-watchdog can detect this
#      script itself going zombie (the pattern that bit us with
#      SSD-TD-Watchdog dying silently since Apr 13).
#   2. Exponential backoff + max-restarts-per-hour, so Arena in a crash
#      loop can't hammer the machine forever. After 5 restarts in 1hr,
#      watchdog disables itself + fires a CRITICAL alert.
#
# Check interval: 2 minutes.
# Heartbeat:      C:\Users\user\heartbeats\resolume_watchdog.hb
# State:          C:\Users\user\resolume_watchdog_state.json (restart history)
# Log:            C:\Users\user\Desktop\ssd_resolume_watchdog.log
#
# Revert path: git shows prior simpler version; `git checkout <old-sha> --
#   scripts/resolume_watchdog.ps1` restores pre-Apr-19 version. This script's
#   additional state files are disposable; delete to reset.

$LogFile       = "C:\Users\user\Desktop\ssd_resolume_watchdog.log"
$HeartbeatDir  = "C:\Users\user\heartbeats"
$HeartbeatFile = Join-Path $HeartbeatDir "resolume_watchdog.hb"
$StateFile     = "C:\Users\user\resolume_watchdog_state.json"

$MaxRestartsPerHour = 5
$RestartWindowSec   = 3600
# Backoff (seconds) after the 1st, 2nd, 3rd, 4th+ consecutive restart.
$BackoffSchedule    = @(60, 120, 300, 600)
# How long Arena must stay up after a restart to "count as recovered" and
# reset the consecutive counter.
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

function Test-ArenaRunning {
    $arena = Get-Process -Name "Arena" -ErrorAction SilentlyContinue
    return [bool]$arena
}

function Load-State {
    if (-not (Test-Path $StateFile)) {
        return @{
            restart_timestamps   = @()
            consecutive_restarts = 0
            disabled_until_human = $false
        }
    }
    try {
        $obj = Get-Content $StateFile -Raw | ConvertFrom-Json
        return @{
            restart_timestamps   = @($obj.restart_timestamps)
            consecutive_restarts = [int]$obj.consecutive_restarts
            disabled_until_human = [bool]$obj.disabled_until_human
        }
    } catch {
        Write-Log "state file unreadable, resetting"
        return @{
            restart_timestamps   = @()
            consecutive_restarts = 0
            disabled_until_human = $false
        }
    }
}

function Save-State($state) {
    try {
        ($state | ConvertTo-Json -Compress) | Set-Content -Path $StateFile -Encoding UTF8
    } catch {
        Write-Log "failed to save state: $_"
    }
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

Write-Log "Resolume watchdog started (PID $PID) -- max $MaxRestartsPerHour restarts/hr, backoff $($BackoffSchedule -join ',') s"

while ($true) {
    Write-Heartbeat
    Start-Sleep -Seconds 120

    $state = Load-State

    # Purge restart timestamps older than 1hr.
    $cutoff = [DateTimeOffset]::Now.ToUnixTimeSeconds() - $RestartWindowSec
    $state.restart_timestamps = @($state.restart_timestamps | Where-Object { [int64]$_ -gt $cutoff })

    # If Arena has been stable for StableThresholdSec since last restart,
    # reset the consecutive counter.
    if ($state.restart_timestamps.Count -gt 0 -and $state.consecutive_restarts -gt 0) {
        $lastRestart = [int64]($state.restart_timestamps[-1])
        $now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
        if (($now - $lastRestart) -gt $StableThresholdSec -and (Test-ArenaRunning)) {
            Write-Log "Arena stable for >$StableThresholdSec s since last restart - resetting consecutive counter"
            $state.consecutive_restarts = 0
            $state.disabled_until_human = $false
        }
    }

    if ($state.disabled_until_human) {
        Write-Log "auto-restart disabled (crash-loop threshold hit) - human intervention required"
        Save-State $state
        continue
    }

    if (Test-ArenaRunning) {
        Save-State $state
        continue
    }

    # Arena is NOT running.
    if ($state.restart_timestamps.Count -ge $MaxRestartsPerHour) {
        Write-Log "crash loop detected: $($state.restart_timestamps.Count) restarts in last hour - DISABLING further restarts"
        Send-CriticalAlert "resolume_watchdog_disabled" "Resolume Arena crashed $($state.restart_timestamps.Count) times in the last hour. Watchdog disabled auto-restart. Manual intervention required."
        $state.disabled_until_human = $true
        Save-State $state
        continue
    }

    $restartIdx = [Math]::Min($state.consecutive_restarts, $BackoffSchedule.Length - 1)
    $backoff = $BackoffSchedule[$restartIdx]
    Write-Log "Arena not running (restart #$($state.consecutive_restarts + 1) in window; backoff $backoff s)"

    & schtasks.exe /run /tn "SSD-Resolume"
    $now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    $state.restart_timestamps = @($state.restart_timestamps + $now)
    $state.consecutive_restarts = $state.consecutive_restarts + 1
    Write-Log "Triggered SSD-Resolume task at unix $now"
    Save-State $state

    Start-Sleep -Seconds $backoff
}
