# meta_watchdog.ps1 -- watches the watchers.
#
# Reads heartbeat_manifest.json every 30s. For each component with
# enabled=true, checks whether its .hb file has been updated within
# max_age_sec. If not, the component is considered STALLED and the
# meta-watchdog fires a CRITICAL Telegram alert (once per stall event;
# no spam). When a stalled component recovers, fires an INFO alert.
#
# Closes the "watchdog died silently" gap that bit us between Apr 16
# and Apr 20 (the old v1 resolume_watchdog stopped restarting Arena
# for days without any signal that it had stopped).
#
# Check interval: 30 seconds.
# Heartbeat (self): C:\Users\user\heartbeats\meta_watchdog.hb
# State:            C:\Users\user\meta_watchdog_state.json  (per-component alert state)
# Health snapshot:  C:\Users\user\meta_watchdog_health.json (latest status of every component)
# Log:              C:\Users\user\Desktop\ssd_meta_watchdog.log
#
# Revert path: unregister SSD-Meta-Watchdog scheduled task; delete this
# file + state + health-snapshot. Other watchdogs are unaffected.

# SingleInstance guard
$myPid = $PID
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.CommandLine -like "*meta_watchdog.ps1*" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

$LogFile         = "C:\Users\user\Desktop\ssd_meta_watchdog.log"
$HeartbeatDir    = "C:\Users\user\heartbeats"
$HeartbeatFile   = Join-Path $HeartbeatDir "meta_watchdog.hb"
$StateFile       = "C:\Users\user\meta_watchdog_state.json"
$HealthFile      = "C:\Users\user\meta_watchdog_health.json"
$ManifestFile    = "C:\Users\user\heartbeat_manifest.json"

$CheckIntervalSec = 30

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

function Load-Manifest {
    try {
        return Get-Content $ManifestFile -Raw | ConvertFrom-Json
    } catch {
        Write-Log "ERROR: cannot read manifest $ManifestFile : $_"
        return $null
    }
}

function Load-State {
    if (Test-Path $StateFile) {
        try {
            $raw = Get-Content $StateFile -Raw | ConvertFrom-Json
            # Convert PSCustomObject to hashtable keyed by component name
            $h = @{}
            foreach ($p in $raw.PSObject.Properties) {
                $h[$p.Name] = @{
                    alerted = [bool]$p.Value.alerted
                    last_ok = [string]$p.Value.last_ok
                }
            }
            return $h
        } catch {}
    }
    return @{}
}

function Save-State($state) {
    try {
        ($state | ConvertTo-Json -Compress -Depth 4) | Set-Content -Path $StateFile -Encoding UTF8
    } catch {
        Write-Log "WARN: could not save state: $_"
    }
}

function Write-Health($components) {
    try {
        $snapshot = @{
            updated_at = (Get-Date -Format "o")
            components = $components
        }
        ($snapshot | ConvertTo-Json -Depth 5) | Set-Content -Path $HealthFile -Encoding UTF8
    } catch {}
}

function Send-Alert($key, $severity, $message) {
    $notifier = "C:\Users\user\ssd_notify.ps1"
    if (Test-Path $notifier) {
        try {
            . $notifier
            Send-SSDAlert -Key $key -Severity $severity -Message $message | Out-Null
        } catch {
            Write-Log "failed to send alert ($key): $_"
        }
    }
}

Write-Log "meta_watchdog started (PID $PID) interval=$CheckIntervalSec s"

while ($true) {
    Write-Heartbeat

    $manifest = Load-Manifest
    if ($manifest -eq $null) {
        Start-Sleep -Seconds $CheckIntervalSec
        continue
    }

    $state = Load-State
    $snapshot = @{}
    $now = [DateTime]::Now

    foreach ($comp in $manifest.components) {
        if (-not $comp.enabled) { continue }

        $name = $comp.name
        $hbPath = Join-Path $HeartbeatDir $comp.file
        $maxAge = [int]$comp.max_age_sec

        # Skip self-check: we just wrote our own heartbeat above, so it's
        # guaranteed fresh. No point alerting on it.
        if ($name -eq "meta_watchdog") {
            $snapshot[$name] = @{ healthy = $true; age_sec = 0; note = "self" }
            continue
        }

        $isHealthy = $false
        $ageSec = -1
        $note = ""

        if (Test-Path $hbPath) {
            try {
                $hbTime = (Get-Item $hbPath).LastWriteTime
                $ageSec = [int]($now - $hbTime).TotalSeconds
                $isHealthy = ($ageSec -le $maxAge)
                if (-not $isHealthy) { $note = "heartbeat stale ($ageSec s > $maxAge s)" }
            } catch {
                $note = "error reading heartbeat: $_"
            }
        } else {
            $note = "heartbeat file missing: $hbPath"
        }

        $snapshot[$name] = @{
            healthy  = $isHealthy
            age_sec  = $ageSec
            max_age_sec = $maxAge
            note     = $note
            hb_path  = $hbPath
        }

        # Track per-component alert state
        if (-not $state.ContainsKey($name)) {
            $state[$name] = @{ alerted = $false; last_ok = "" }
        }
        $s = $state[$name]

        if (-not $isHealthy) {
            if (-not $s.alerted) {
                Write-Log "STALL detected: $name -- $note"
                Send-Alert $comp.alert_key "CRITICAL" "Watchdog stall: $name is $note. Check C:\Users\user\Desktop\ssd_${name}.log on the 3090."
                $s.alerted = $true
            }
        } else {
            if ($s.alerted) {
                Write-Log "RECOVERY: $name healthy again (age=$ageSec s)"
                Send-Alert "$($comp.alert_key)_recovered" "INFO" "Watchdog recovered: $name is writing heartbeats again (age=$ageSec s)."
                $s.alerted = $false
            }
            $s.last_ok = (Get-Date -Format "o")
        }

        $state[$name] = $s
    }

    Save-State $state
    Write-Health $snapshot

    Start-Sleep -Seconds $CheckIntervalSec
}
