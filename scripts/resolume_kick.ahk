#Requires AutoHotkey v2.0
#SingleInstance Force

; resolume_kick.ahk v2 -- defensive multi-path Arena recovery kick.
;
; Purpose: after Arena auto-restart, bring Advanced Output up and get
; projectors re-assigned -- WITHOUT any human watching or intervening.
;
; Why defensive multi-path: we can't verify tonight which of the known-
; working manual gestures actually lands via SendInput from a hidden
; scheduled task. So we try them all, in order, checking for observable
; side effects after each. If any one works, projectors come up. If none
; work, we log which attempts fired so we know what to fix Tuesday AM.
;
; Manual gestures we KNOW work (per Prav 2026-04-20):
;   Ctrl+Shift+A -> opens Advanced Output panel (primary)
;   Ctrl+Shift+D -> closes Advanced Output (Prav used this one too)
;   Enter        -> dismisses any modal (startup "open composition?" prompt)
;
; Observable side effects we can check without visual:
;   1. Count of Arena child windows (Advanced Output = new top-level window)
;   2. LastWriteTime of AdvancedOutput.xml in Preferences\ (sometimes updates)
;   3. Arena log mtime advances (generic aliveness)
;
; Strategy: try primary (Ctrl+Shift+A). If no visible effect after 2s,
; try secondary (Ctrl+Shift+D). If still nothing, try Enter (in case a
; modal is blocking focus). Log every attempt + outcome so Tuesday's
; review tells us which path works.
;
; Replaces resolume_kick.ahk v1 deployed earlier tonight.

LogPath := "C:\Users\user\resolume_kick_ahk.log"

Log(msg) {
    global LogPath
    FileAppend FormatTime(, "yyyy-MM-dd HH:mm:ss") " " msg "`n", LogPath
}

CountArenaWindows() {
    try {
        return WinGetList("ahk_exe Arena.exe").Length
    } catch {
        return -1
    }
}

TryShortcut(key, label) {
    before := CountArenaWindows()
    Log("[" label "] sending " key " (arena windows before: " before ")")
    try {
        WinActivate "ahk_exe Arena.exe"
        WinWaitActive("ahk_exe Arena.exe", , 2)
    } catch {
        Log("[" label "]   WARN: WinActivate failed; sending anyway")
    }
    Sleep 250
    Send key
    Sleep 1500   ; let Arena actually process the keystroke
    after := CountArenaWindows()
    delta := after - before
    Log("[" label "]   arena windows after: " after " (delta: " delta ")")
    return delta
}

Log("=== kick v2 start ===")

if !WinExist("ahk_exe Arena.exe") {
    Log("[FAIL] Arena process/window not found")
    ExitApp 1
}

; ATTEMPT 1: primary (Ctrl+Shift+A -> open Advanced Output)
delta1 := TryShortcut("^+a", "A1")

if (delta1 > 0) {
    Log("[OK] Ctrl+Shift+A opened a new Arena window (delta=+" delta1 ")")
    ExitApp 0
}

; ATTEMPT 2: secondary (Ctrl+Shift+D -> Prav confirmed this works too)
delta2 := TryShortcut("^+d", "A2")

if (delta2 > 0) {
    Log("[OK] Ctrl+Shift+D opened a new Arena window (delta=+" delta2 ")")
    ExitApp 0
}

; ATTEMPT 3: Enter (in case a modal dialog has focus)
delta3 := TryShortcut("{Enter}", "A3")

if (delta3 != 0) {
    Log("[INFO] Enter changed window count by " delta3 " (may indicate a modal was dismissed)")
} else {
    Log("[WARN] No shortcut produced an observable window change")
}

; ATTEMPT 4: if modal was dismissed by Enter, retry Ctrl+Shift+A
if (delta3 < 0) {
    Log("[INFO] Modal likely dismissed; retrying Ctrl+Shift+A")
    delta4 := TryShortcut("^+a", "A4")
    if (delta4 > 0) {
        Log("[OK] Ctrl+Shift+A after Enter: opened new window (delta=+" delta4 ")")
        ExitApp 0
    }
}

Log("[END] all shortcuts attempted, no definitive success detected via window count")
Log("    Manual Prav check required Tuesday AM: look at Arena screen, see if Advanced Output opened after the 09:49 watchdog restart cycle.")
ExitApp 0
