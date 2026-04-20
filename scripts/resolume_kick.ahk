#Requires AutoHotkey v2.0
#SingleInstance Force

; resolume_kick.ahk -- remote-triggerable Resolume Advanced Output kick.
;
; Sends Ctrl+Shift+A to Resolume Arena to toggle the Advanced Output panel,
; which is what causes the projectors to auto-assign after a cold restart.
;
; Replaces the older PowerShell System.Windows.Forms.SendKeys approach,
; which silently failed when fired from a hidden scheduled task (Windows
; foreground-lock protection blocks SetForegroundWindow for hidden
; background processes).
;
; AHK's WinActivate uses AttachThreadInput internally to bypass the lock,
; and Send uses SendInput (hardware-level emulation) which reaches
; graphics apps like Arena that ignore PostMessage-style synthetic input.
;
; Log: C:\Users\user\resolume_kick_ahk.log

LogPath := "C:\Users\user\resolume_kick_ahk.log"

Log(msg) {
    global LogPath
    FileAppend FormatTime(, "yyyy-MM-dd HH:mm:ss") " " msg "`n", LogPath
}

Log("[INFO] start")

if !WinExist("ahk_exe Arena.exe") {
    Log("[FAIL] Arena process/window not found")
    ExitApp 1
}

hwnd := WinExist("ahk_exe Arena.exe")
Log("[INFO] Arena hwnd=" hwnd)

WinActivate "ahk_exe Arena.exe"
if !WinWaitActive("ahk_exe Arena.exe", , 3) {
    Log("[WARN] WinWaitActive timeout; sending anyway")
}

Sleep 300
Send "^+a"
Log("[OK] Ctrl+Shift+A sent to Arena")
ExitApp 0
