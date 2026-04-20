# gallery_resolume_kick.ps1
# Invokes resolume_kick.ahk (AutoHotkey v2) to send Ctrl+Shift+A to Arena.
#
# Replaces the original System.Windows.Forms.SendKeys implementation
# (which silently failed when fired from a hidden scheduled task because
# Windows foreground-lock protection blocks SetForegroundWindow for
# hidden background processes).
#
# AHK uses AttachThreadInput + SendInput (hardware-level) to bypass
# these restrictions. See C:\Users\user\resolume_kick.ahk.
#
# This shim stays in place so the SSD-Resolume-Kick scheduled task
# doesn't need its "Task To Run" path changed (that requires run-as
# password). Behavior migration is internal.
#
# Logs to C:\Users\user\resolume_kick.log (legacy path preserved for
# observability continuity) and C:\Users\user\resolume_kick_ahk.log
# (AHK-specific log written by the .ahk itself).

$LogPath = "C:\Users\user\resolume_kick.log"
$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
function Write-Log { param($msg) Add-Content -Path $LogPath -Value "[$Stamp] $msg" }

$AhkExe = "C:\Program Files\AutoHotkey\v2\AutoHotkey.exe"
$AhkScript = "C:\Users\user\resolume_kick.ahk"

if (-not (Test-Path $AhkExe)) {
    Write-Log "[FAIL] AutoHotkey v2 not found at $AhkExe"
    exit 1
}
if (-not (Test-Path $AhkScript)) {
    Write-Log "[FAIL] kick script not found at $AhkScript"
    exit 2
}

$proc = Start-Process -FilePath $AhkExe -ArgumentList "`"$AhkScript`"" -Wait -PassThru -WindowStyle Hidden
Write-Log "[OK] AHK invoked resolume_kick.ahk (exit=$($proc.ExitCode))"
exit $proc.ExitCode
