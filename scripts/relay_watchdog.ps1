# relay_watchdog.ps1 — PowerShell watchdog for td_relay.py
# Restarts the relay whenever it exits. Run this if not using NSSM.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\relay_watchdog.ps1
#
# To run at login: add to Task Scheduler (trigger: At log on, action: this script)

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$REPO_DIR   = Split-Path -Parent $SCRIPT_DIR
$RELAY      = "$SCRIPT_DIR\td_relay.py"
$LOG        = "$REPO_DIR\logs\relay.log"

# Create logs dir if needed
New-Item -ItemType Directory -Force -Path "$REPO_DIR\logs" | Out-Null

Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [watchdog] Starting td_relay watchdog"
Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [watchdog] Relay: $RELAY"
Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [watchdog] Log:   $LOG"

while ($true) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "$ts [watchdog] Launching relay..."
    Add-Content -Path $LOG -Value "$ts [watchdog] --- relay (re)started ---"

    # Run relay, capturing output to log file
    $proc = Start-Process python `
        -ArgumentList $RELAY `
        -RedirectStandardOutput $LOG `
        -RedirectStandardError  $LOG `
        -NoNewWindow `
        -PassThru

    # Wait for it to exit
    $proc.WaitForExit()
    $exit = $proc.ExitCode

    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "$ts [watchdog] Relay exited (code $exit). Restarting in 5s..."
    Add-Content -Path $LOG -Value "$ts [watchdog] relay exited (code $exit), restarting in 5s"
    Start-Sleep -Seconds 5
}
