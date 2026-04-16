# gallery_resolume_kick.ps1
# Brings Resolume Arena to foreground and sends Ctrl+Shift+A to toggle the
# Advanced Output panel. Used to remotely re-open the projector outputs after
# Resolume comes up idle on cold boot (Prav's manual fix every morning).
#
# How to trigger remotely (any window with SSH access):
#     ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-Kick"
#
# This MUST run via Task Scheduler in the user's interactive session, NOT
# directly over SSH -- SendKeys requires a real desktop, which a headless
# SSH session doesn't have.
#
# Logs to C:\Users\user\resolume_kick.log so we can audit when it fires.

Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
  using System;
  using System.Runtime.InteropServices;
  public class WinApi {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  }
"@

$LogPath = "C:\Users\user\resolume_kick.log"
$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log { param($msg) Add-Content -Path $LogPath -Value "[$Stamp] $msg" }

$arena = Get-Process -Name "Arena" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } | Select-Object -First 1
if (-not $arena) {
    Write-Log "[FAIL] Arena process not found or has no visible window"
    exit 1
}

$pidVal = $arena.Id
$handle = $arena.MainWindowHandle
Write-Log "[INFO] Found Arena PID=$pidVal handle=$handle"

# SW_RESTORE = 9 (un-minimize if needed)
[WinApi]::ShowWindow($handle, 9) | Out-Null
[WinApi]::SetForegroundWindow($handle) | Out-Null

Start-Sleep -Milliseconds 500

# Send Ctrl+Shift+A (Resolume Advanced Output toggle)
[System.Windows.Forms.SendKeys]::SendWait("^+a")

Write-Log "[OK] Sent Ctrl+Shift+A to Arena"
exit 0
