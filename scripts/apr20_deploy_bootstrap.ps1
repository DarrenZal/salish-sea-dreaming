# apr20_deploy_bootstrap.ps1 -- one-command Apr 20 post-tunnel-restart deploy.
# Usage on the 3090 after SSH tunnel is restored:
#
#   iex (iwr https://salishseadreaming.art/graph-assets/deploy/apr20/apr20_deploy_bootstrap.ps1).Content
#
# What it does, idempotently:
#   1. Creates C:\Users\user\heartbeats\ directory
#   2. Downloads + installs resolume_watchdog.ps1 (upgraded with heartbeat + backoff)
#   3. Registers SSD-Resolume-Watchdog-v2 scheduled task (via XML)
#   4. Downloads heartbeat_manifest.json
#   5. Downloads windows_update_block.ps1 (but does NOT run it -- operator runs explicitly)
#   6. Runs a sanity test: Stop-Process Arena, verify restart within 3 min
#   7. Reports success/failure of each step
#
# Requires: SSH tunnel already restored, admin PowerShell, outbound HTTPS to salishseadreaming.art.

$ErrorActionPreference = "Continue"
$Base = "https://salishseadreaming.art/graph-assets/deploy/apr20"
$LogFile = "C:\Users\user\Desktop\apr20_deploy.log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$ts  $msg"
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
    Write-Host $line
}

function Download($url, $dest) {
    Log "download: $url -> $dest"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -TimeoutSec 30
        $size = (Get-Item $dest).Length
        Log "  OK ($size bytes)"
        return $true
    } catch {
        Log "  FAIL: $($_.Exception.Message)"
        return $false
    }
}

Log "=== apr20 deploy bootstrap start ==="

# 1. heartbeats/ dir
if (-not (Test-Path "C:\Users\user\heartbeats")) {
    New-Item -ItemType Directory -Path "C:\Users\user\heartbeats" -Force | Out-Null
    Log "created C:\Users\user\heartbeats\"
} else {
    Log "heartbeats dir already exists"
}

# 2. Resolume watchdog script (upgraded)
$ok1 = Download "$Base/resolume_watchdog.ps1" "C:\Users\user\resolume_watchdog.ps1"
if (-not $ok1) { Log "ABORTING: watchdog script download failed"; exit 1 }

# 3. Task XML + registration
$ok2 = Download "$Base/SSD-Resolume-Watchdog-v2.xml" "C:\Users\user\SSD-Resolume-Watchdog-v2.xml"
if ($ok2) {
    Log "registering SSD-Resolume-Watchdog-v2 task"
    $reg = schtasks /create /tn "SSD-Resolume-Watchdog-v2" /xml C:\Users\user\SSD-Resolume-Watchdog-v2.xml /f 2>&1
    Log "  $reg"
    schtasks /run /tn "SSD-Resolume-Watchdog-v2" 2>&1 | Out-Null
    Log "  triggered task"
} else {
    Log "WARN: task XML download failed; skipping registration"
}

# 4. Heartbeat manifest
Download "$Base/heartbeat_manifest.json" "C:\Users\user\heartbeat_manifest.json" | Out-Null

# 5. Windows Update block (download only; operator runs explicitly)
Download "$Base/windows_update_block.ps1" "C:\Users\user\windows_update_block.ps1" | Out-Null
Log "windows_update_block.ps1 downloaded. To execute: powershell -ExecutionPolicy Bypass -File C:\Users\user\windows_update_block.ps1"

# 6. Wait 60s for watchdog to write its first heartbeat, then verify
Log "waiting 60s for watchdog heartbeat..."
Start-Sleep -Seconds 60
$hb = "C:\Users\user\heartbeats\resolume_watchdog.hb"
if (Test-Path $hb) {
    $age = [int]((Get-Date) - (Get-Item $hb).LastWriteTime).TotalSeconds
    if ($age -lt 180) {
        Log "PASS: watchdog heartbeat fresh ($age s old)"
    } else {
        Log "WARN: watchdog heartbeat exists but is $age s old"
    }
} else {
    Log "FAIL: no heartbeat file yet -- check watchdog is running: Get-WmiObject Win32_Process -Filter \"Name='powershell.exe'\" | Where CommandLine -like '*resolume_watchdog*'"
}

# 7. Sanity test: kill Arena, watch for restart
Log "=== synthetic test: kill Arena, expect restart within 3 min ==="
$arenaBefore = Get-Process Arena -ErrorAction SilentlyContinue
if (-not $arenaBefore) {
    Log "Arena not running before test -- skipping synthetic test (start Arena first)"
} else {
    $pidBefore = $arenaBefore.Id
    Log "Arena PID before: $pidBefore. Killing..."
    Stop-Process -Id $pidBefore -Force
    Start-Sleep -Seconds 10

    $maxWait = 180
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 15
        $waited += 15
        $arenaNow = Get-Process Arena -ErrorAction SilentlyContinue
        if ($arenaNow -and $arenaNow.Id -ne $pidBefore) {
            Log "PASS: Arena restarted by watchdog after ${waited}s. New PID: $($arenaNow.Id)"
            break
        }
        Log "  still waiting... ${waited}s"
    }
    if ($waited -ge $maxWait) {
        Log "FAIL: Arena not restarted within ${maxWait}s. Check watchdog log: C:\Users\user\Desktop\ssd_resolume_watchdog.log"
    }
}

Log "=== apr20 deploy bootstrap complete ==="
Log "next steps:"
Log "  - review this log: $LogFile"
Log "  - review watchdog log: C:\Users\user\Desktop\ssd_resolume_watchdog.log"
Log "  - optionally run windows_update_block.ps1 when ready"
