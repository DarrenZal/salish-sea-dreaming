# windows_update_block.ps1 -- block Windows + NVIDIA driver auto-updates on the 3090
# during exhibition / show season. Per Prav Apr 19 Signal: "Can we stop windows
# updates - that is just bad."
#
# Design: disable at multiple layers so a single Group Policy refresh can't
# re-enable it. Script is idempotent + logs each action taken.
#
# Unblock procedure (post-show): run the same script with -Unblock, OR manually
# revert by setting NoAutoUpdate to 0 and re-enabling the scheduled tasks below.
#
# Run as Administrator. PowerShell 5.1+.

param(
    [switch]$Unblock = $false
)

$LogFile = "C:\Users\user\Desktop\windows_update_block.log"
function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg"
    Write-Host $msg
}

Write-Log "=== start (unblock=$Unblock) ==="

# -----------------------------------------------------------------------------
# Layer 1: Windows Update policy registry keys
# -----------------------------------------------------------------------------
$wuPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
if (-not (Test-Path $wuPath)) {
    Write-Log "creating WindowsUpdate policy key"
    New-Item -Path $wuPath -Force | Out-Null
}
if ($Unblock) {
    Set-ItemProperty -Path $wuPath -Name "NoAutoUpdate" -Value 0 -Type DWord
    Set-ItemProperty -Path $wuPath -Name "AUOptions" -Value 4 -Type DWord
    Write-Log "Windows Update: AUTO install RE-ENABLED (NoAutoUpdate=0, AUOptions=4)"
} else {
    Set-ItemProperty -Path $wuPath -Name "NoAutoUpdate" -Value 1 -Type DWord
    Set-ItemProperty -Path $wuPath -Name "AUOptions" -Value 2 -Type DWord
    Write-Log "Windows Update: AUTO install BLOCKED (NoAutoUpdate=1, AUOptions=2)"
}

# -----------------------------------------------------------------------------
# Layer 2: Pause updates via flight-ring / deferral settings
# -----------------------------------------------------------------------------
$wuUX = "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
if (Test-Path $wuUX) {
    if ($Unblock) {
        Remove-ItemProperty -Path $wuUX -Name "PauseUpdatesExpiryTime" -ErrorAction SilentlyContinue
        Write-Log "Windows Update: pause-updates cleared"
    } else {
        # Pause for 35 days (max per Windows 11). Re-apply every month during show.
        $pauseUntil = (Get-Date).AddDays(35).ToString("yyyy-MM-ddTHH:mm:ssZ")
        Set-ItemProperty -Path $wuUX -Name "PauseUpdatesExpiryTime" -Value $pauseUntil -Type String
        Write-Log "Windows Update: paused until $pauseUntil"
    }
}

# -----------------------------------------------------------------------------
# Layer 3: Disable the scheduled tasks that trigger Windows Update
# -----------------------------------------------------------------------------
$wuTasks = @(
    "\Microsoft\Windows\WindowsUpdate\Scheduled Start"
    "\Microsoft\Windows\UpdateOrchestrator\Schedule Scan"
    "\Microsoft\Windows\UpdateOrchestrator\USO_UxBroker"
)
foreach ($t in $wuTasks) {
    try {
        if ($Unblock) {
            schtasks /change /tn $t /enable 2>&1 | Out-Null
            Write-Log "task enabled: $t"
        } else {
            schtasks /change /tn $t /disable 2>&1 | Out-Null
            Write-Log "task disabled: $t"
        }
    } catch {
        Write-Log "WARN: task not found or permission denied: $t"
    }
}

# -----------------------------------------------------------------------------
# Layer 4: NVIDIA GeForce Experience auto-update (driver push prevention)
# -----------------------------------------------------------------------------
$nvidiaTasks = @(
    "\NVIDIA GeForce Experience"
    "\NvTmRep_CrashReport1"
    "\NvTmRep_CrashReport2"
    "\NvTmRep_CrashReport3"
    "\NvTmRep_CrashReport4"
)
foreach ($t in $nvidiaTasks) {
    try {
        if ($Unblock) {
            schtasks /change /tn $t /enable 2>&1 | Out-Null
            Write-Log "task enabled: $t"
        } else {
            schtasks /change /tn $t /disable 2>&1 | Out-Null
            Write-Log "task disabled: $t"
        }
    } catch {
        # Most of these won't exist; only warn on ones we care about
    }
}

# NVIDIA Display Container LS auto-update component
$nvSvc = Get-Service -Name "NvContainerLocalSystem" -ErrorAction SilentlyContinue
if ($nvSvc) {
    if ($Unblock) {
        Set-Service -Name "NvContainerLocalSystem" -StartupType Automatic
        Write-Log "NvContainerLocalSystem: startup RESTORED to Automatic"
    } else {
        # Don't disable the service entirely (can break video output), just
        # prevent the auto-update task subcomponent if present.
        Write-Log "NvContainerLocalSystem: left enabled (required for display)"
    }
}

# -----------------------------------------------------------------------------
# Layer 5: Metered connection flag (hints Windows to defer large downloads)
# -----------------------------------------------------------------------------
# Note: this is best-effort. Set the primary network as metered.
try {
    $netProfiles = Get-NetConnectionProfile -ErrorAction SilentlyContinue
    foreach ($p in $netProfiles) {
        if ($Unblock) {
            # Revert to default (non-metered)
            # Windows doesn't expose a clean unset; log a manual step
            Write-Log "MANUAL: Settings > Network > Wi-Fi/Ethernet > Properties > Metered connection: revert per-adapter"
        } else {
            Write-Log "MANUAL: Settings > Network > Wi-Fi/Ethernet > Properties > Metered connection: ON (per-adapter, unable to set via registry)"
        }
    }
} catch {}

Write-Log "=== complete. verify: 'gpresult /r | Select-String WindowsUpdate' + Get-ScheduledTask | Where {\$_.TaskPath -like '*Update*' -and \$_.State -eq 'Ready'} ==="
