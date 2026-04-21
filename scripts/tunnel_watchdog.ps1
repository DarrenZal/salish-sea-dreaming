# tunnel_watchdog.ps1 -- Verify the SSH reverse tunnel to poly is healthy
# and auto-restart SSD-SSH-Tunnel if it isn't. Addresses the Apr 19 outage
# where the tunnel stopped reconnecting at 16:50 PDT without notice.
#
# Check interval: 60 seconds.
# Heartbeat:      C:\Users\user\heartbeats\tunnel_watchdog.hb
# Log:            C:\Users\user\Desktop\ssd_tunnel_watchdog.log
#
# The tunnel is considered HEALTHY if:
#   1. ssh out to poly succeeds in <5s (network + auth)
#   2. poly reports a listening socket on 127.0.0.1:2222 (our reverse
#      tunnel's endpoint is up)
#
# On UNHEALTHY for 2 consecutive checks -> attempt auto-restart of the
# SSD-SSH-Tunnel task (kill orphan ssh.exe processes first to avoid
# zombies from blocking re-bind).
#
# On UNHEALTHY for 3+ consecutive checks -> fire CRITICAL Telegram alert
# (once, not spam). Alert clears on next healthy check.
#
# Revert path: git shows previous state (no tunnel watchdog); simply
# remove the SSD-Tunnel-Watchdog scheduled task and delete this file.
# The tunnel itself is unaffected.

# SingleInstance guard: kill any older instance of this script before proceeding.
$myPid = $PID
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.CommandLine -like "*tunnel_watchdog.ps1*" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

$LogFile        = "C:\Users\user\Desktop\ssd_tunnel_watchdog.log"
$HeartbeatDir   = "C:\Users\user\heartbeats"
$HeartbeatFile  = Join-Path $HeartbeatDir "tunnel_watchdog.hb"
$StateFile      = "C:\Users\user\tunnel_watchdog_state.json"

$SSHExe   = "C:\Windows\System32\OpenSSH\ssh.exe"
$PolyAddr = "poly@37.27.48.12"

$CheckIntervalSec       = 60
$RestartAfterFails      = 2   # consecutive failures before auto-restart
$AlertAfterFails        = 3   # consecutive failures before critical alert

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

function Load-State {
    if (Test-Path $StateFile) {
        try {
            $obj = Get-Content $StateFile -Raw | ConvertFrom-Json
            return @{
                consecutive_fails = [int]$obj.consecutive_fails
                alert_fired       = [bool]$obj.alert_fired
                last_restart      = [int64]$obj.last_restart
            }
        } catch {}
    }
    return @{ consecutive_fails = 0; alert_fired = $false; last_restart = 0 }
}

function Save-State($state) {
    try {
        ($state | ConvertTo-Json -Compress) | Set-Content -Path $StateFile -Encoding UTF8
    } catch {}
}

function Test-TunnelHealthy {
    # Run ssh to poly with a short timeout and pull the raw socket listing;
    # do the grep-for-2222 in PowerShell to avoid remote-shell quote escaping
    # issues through the SSH layer.
    try {
        $output = & $SSHExe `
            -o ConnectTimeout=5 `
            -o BatchMode=yes `
            -o StrictHostKeyChecking=no `
            -o ServerAliveInterval=5 `
            -o ServerAliveCountMax=1 `
            $PolyAddr `
            "ss -tln 2>/dev/null" `
            2>&1
        if ($LASTEXITCODE -eq 0 -and ($output | Out-String) -match ":2222\s") {
            return $true
        }
    } catch {}
    return $false
}

function Stop-OrphanTunnelSsh {
    try {
        $orphans = Get-WmiObject Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*2222:localhost:22*" -or $_.CommandLine -like "*poly@37.27.48.12*" }
        foreach ($p in $orphans) {
            try {
                Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Log "killed orphan ssh.exe PID $($p.ProcessId)"
            } catch {}
        }
    } catch {}
}

function Restart-Tunnel {
    Write-Log "restarting tunnel"
    try { & schtasks.exe /end /tn "SSD-SSH-Tunnel" 2>&1 | Out-Null } catch {}
    Start-Sleep -Seconds 2
    Stop-OrphanTunnelSsh
    Start-Sleep -Seconds 3
    try {
        & schtasks.exe /run /tn "SSD-SSH-Tunnel" 2>&1 | Out-Null
        Write-Log "triggered SSD-SSH-Tunnel task"
    } catch {
        Write-Log "failed to trigger SSD-SSH-Tunnel: $_"
    }
    Start-Sleep -Seconds 15  # let the new tunnel establish
}

function Send-CriticalAlert($message) {
    $notifier = "C:\Users\user\ssd_notify.ps1"
    if (Test-Path $notifier) {
        try {
            . $notifier
            Send-SSDAlert -Key "tunnel_watchdog" -Severity "CRITICAL" -Message $message | Out-Null
        } catch {
            Write-Log "failed to send alert: $_"
        }
    }
}

function Send-InfoAlert($message) {
    $notifier = "C:\Users\user\ssd_notify.ps1"
    if (Test-Path $notifier) {
        try {
            . $notifier
            Send-SSDAlert -Key "tunnel_watchdog_recovered" -Severity "INFO" -Message $message | Out-Null
        } catch {}
    }
}

Write-Log "tunnel_watchdog started (PID $PID) interval=$CheckIntervalSec s, restart-after=$RestartAfterFails, alert-after=$AlertAfterFails"

while ($true) {
    Write-Heartbeat
    $state = Load-State

    if (Test-TunnelHealthy) {
        if ($state.consecutive_fails -gt 0) {
            Write-Log "tunnel recovered after $($state.consecutive_fails) failed checks"
            if ($state.alert_fired) {
                Send-InfoAlert "tunnel recovered after $($state.consecutive_fails) failed checks"
                $state.alert_fired = $false
            }
        }
        $state.consecutive_fails = 0
    } else {
        $state.consecutive_fails++
        Write-Log "tunnel check FAILED (consecutive: $($state.consecutive_fails))"

        if ($state.consecutive_fails -eq $RestartAfterFails) {
            Restart-Tunnel
            $state.last_restart = [DateTimeOffset]::Now.ToUnixTimeSeconds()
        } elseif ($state.consecutive_fails -gt $RestartAfterFails -and
                  ($state.consecutive_fails - $RestartAfterFails) % 3 -eq 0) {
            # Re-attempt restart every 3 additional failures
            Restart-Tunnel
            $state.last_restart = [DateTimeOffset]::Now.ToUnixTimeSeconds()
        }

        if ($state.consecutive_fails -ge $AlertAfterFails -and -not $state.alert_fired) {
            Send-CriticalAlert "Tunnel to poly:2222 unreachable after $($state.consecutive_fails) checks. Auto-restart attempted; check logs on 3090."
            $state.alert_fired = $true
        }
    }

    Save-State $state
    Start-Sleep -Seconds $CheckIntervalSec
}
