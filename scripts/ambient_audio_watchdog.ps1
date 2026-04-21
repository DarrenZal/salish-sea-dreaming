# ambient_audio_watchdog.ps1 -- keep the ambient-audio player running.
# Template-copy of the resolume_watchdog v2 pattern, adapted for the
# ambient_audio.ps1 process.
#
# Check interval: 2 minutes.
# Heartbeat:      C:\Users\user\heartbeats\ambient_audio_watchdog.hb
# State:          C:\Users\user\ambient_audio_watchdog_state.json
# Log:            C:\Users\user\Desktop\ssd_ambient_audio_watchdog.log
#
# What counts as "running": a powershell.exe process whose CommandLine
# contains "ambient_audio.ps1" (NOT this watchdog itself).
#
# Status: DRAFT -- deploy Wed after ambient_audio.ps1 is validated.

# SingleInstance guard
$myPid = $PID
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.CommandLine -like "*ambient_audio_watchdog.ps1*" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

$LogFile       = "C:\Users\user\Desktop\ssd_ambient_audio_watchdog.log"
$HeartbeatDir  = "C:\Users\user\heartbeats"
$HeartbeatFile = Join-Path $HeartbeatDir "ambient_audio_watchdog.hb"
$StateFile     = "C:\Users\user\ambient_audio_watchdog_state.json"

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

function Test-AmbientAudioRunning {
    try {
        $p = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*ambient_audio.ps1*" -and $_.CommandLine -notlike "*watchdog*" }
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

Write-Log "ambient_audio_watchdog started (PID $PID) -- max $MaxRestartsPerHour restarts/hr, backoff $($BackoffSchedule -join ',') s"

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
            Write-Log "ambient_audio stable for >$StableThresholdSec s since last restart - resetting consecutive counter"
            $state.consecutive_restarts = 0
        }
    }

    if (Test-AmbientAudioRunning) {
        Save-State $state
        continue
    }

    if ($state.restart_timestamps.Count -ge $MaxRestartsPerHour) {
        Write-Log "crash loop detected: $($state.restart_timestamps.Count) restarts in last hour - DISABLING further restarts"
        Send-CriticalAlert "ambient_audio_watchdog_disabled" "Ambient audio crashed $($state.restart_timestamps.Count) times in the last hour. Watchdog disabled auto-restart. Manual intervention required."
        $state.disabled_until_human = $true
        Save-State $state
        continue
    }

    $restartIdx = [Math]::Min($state.consecutive_restarts, $BackoffSchedule.Length - 1)
    $backoff = $BackoffSchedule[$restartIdx]
    Write-Log "ambient_audio not running (restart #$($state.consecutive_restarts + 1) in window; backoff $backoff s)"

    & schtasks.exe /run /tn "SSD-Ambient-Audio"
    $now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    $state.restart_timestamps = @($state.restart_timestamps + $now)
    $state.consecutive_restarts = $state.consecutive_restarts + 1
    Write-Log "Triggered SSD-Ambient-Audio task at unix $now"
    Save-State $state

    Start-Sleep -Seconds $backoff
}
