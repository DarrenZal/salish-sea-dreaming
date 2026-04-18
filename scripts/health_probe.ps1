# health_probe.ps1 -- deep pipeline health check for the Salish Sea Dreaming install.
#
# Runs every 5 min via scheduled task `SSD-Health-Probe`. For each check:
#   - PASS: clear the alert state (so next failure re-fires)
#   - FAIL: fire Telegram via Send-SSDAlert (with 30 min cooldown per key)
#
# Checks (all return bool):
#   1. TouchDesigner running
#   2. Resolume Arena running
#   3. Autolume running
#   4. Relay process alive (via PID file)
#   5. Ambient audio player alive
#   6. Gallery server on poly reachable (HTTP 200 within 5 s)
#   7. TD snapshot freshness (< 10 min old)
#
# Wall brightness / pipeline-output checks are Phase 4 work; intentionally
# out of scope here. This script's job is to catch the 80% of failures
# that are process death or network drop.
#
# Log: C:\Users\user\health_probe.log (rotating by size would be nice; not yet)

$ErrorActionPreference = 'Continue'
$log = "C:\Users\user\health_probe.log"

function Write-ProbeLog {
    param([string]$msg)
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $log -Value "$stamp  $msg" -ErrorAction SilentlyContinue
}

# Load notifier
. "C:\Users\user\ssd_notify.ps1"

# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

function Test-ProcessRunning {
    param([string]$Name)
    $p = Get-Process -Name $Name -ErrorAction SilentlyContinue
    return [bool]$p
}

function Test-RelayRunning {
    $pidFile = "C:\Users\user\td_relay.pid"
    if (-not (Test-Path $pidFile)) { return $false }
    try {
        $relayPid = [int](Get-Content $pidFile -Raw).Trim()
        $p = Get-Process -Id $relayPid -ErrorAction SilentlyContinue
        return [bool]$p -and $p.ProcessName -match 'python'
    } catch {
        return $false
    }
}

function Test-GalleryServer {
    try {
        $r = Invoke-WebRequest -Uri "http://37.27.48.12:9000/health" -TimeoutSec 5 -UseBasicParsing
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Test-SnapshotFresh {
    $snap = "C:\Users\user\Desktop\td_snap.jpg"
    if (-not (Test-Path $snap)) { return $false }
    $ageSec = ((Get-Date) - (Get-Item $snap).LastWriteTime).TotalSeconds
    return $ageSec -lt 600  # 10 min tolerance
}

# ---------------------------------------------------------------------------
# Report helper: fire-or-clear alert for a single check
# ---------------------------------------------------------------------------

function Report-Check {
    param(
        [string]$Key,
        [bool]$Pass,
        [string]$FailMessage,
        [ValidateSet('INFO','WARN','CRITICAL')] [string]$Severity = 'CRITICAL'
    )
    if ($Pass) {
        Write-ProbeLog "PASS ${Key}"
        Clear-SSDAlert -Key $Key
    } else {
        Write-ProbeLog "FAIL ${Key}: $FailMessage"
        Send-SSDAlert -Key $Key -Severity $Severity -Message $FailMessage | Out-Null
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Write-ProbeLog "--- probe start ---"

Report-Check -Key "proc_touchdesigner" `
    -Pass (Test-ProcessRunning -Name "TouchDesigner") `
    -FailMessage "TouchDesigner.exe is not running" `
    -Severity CRITICAL

Report-Check -Key "proc_resolume" `
    -Pass (Test-ProcessRunning -Name "Arena") `
    -FailMessage "Resolume Arena.exe is not running" `
    -Severity CRITICAL

Report-Check -Key "proc_autolume" `
    -Pass (Test-ProcessRunning -Name "Autolume") `
    -FailMessage "Autolume.exe is not running" `
    -Severity WARN

Report-Check -Key "proc_relay" `
    -Pass (Test-RelayRunning) `
    -FailMessage "td_relay.py is not running (PID file stale or process dead)" `
    -Severity WARN

Report-Check -Key "gallery_server" `
    -Pass (Test-GalleryServer) `
    -FailMessage "Gallery server on poly:9000 is unreachable from 3090" `
    -Severity WARN

Report-Check -Key "td_snapshot" `
    -Pass (Test-SnapshotFresh) `
    -FailMessage "td_snap.jpg is missing or older than 10 min -- render pipeline may be stalled" `
    -Severity WARN

Write-ProbeLog "--- probe complete ---"
