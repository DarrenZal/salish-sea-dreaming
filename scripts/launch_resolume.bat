@echo off
REM launch_resolume.bat -- Arena launcher for the SSD gallery installation.
REM Called by SSD-Resolume scheduled task (triggered by SSD-Resolume-Watchdog-v2
REM when Arena isn't running, or manually via schtasks /run).
REM
REM History: the original 2-line version just started Arena with the
REM composition file arg. Cold-restart testing on 2026-04-20 revealed
REM Arena shows a modal prompt ("Do you really want to open a composition?")
REM which blocks unattended recovery -- operator must click through before
REM projectors can be assigned. This version addresses that by:
REM
REM   1. Pre-deleting any crash-recovery state file (locations speculative;
REM      extend the list as we identify more). Harmless if the files
REM      don't exist.
REM
REM   2. Passing --suppressCompositionChangeConfirmation (undocumented flag
REM      mentioned on Resolume forums to skip composition-switch prompts).
REM      If this flag is unrecognised Arena should just ignore it.
REM
REM Deploy path: C:\Users\user\launch_resolume.bat on the 3090.
REM
REM Staged for deployment after validation 2026-04-20 post-opening window
REM (must test with Prav or a moment of no-visitor coverage: kill Arena,
REM let watchdog restart via this script, confirm no modal dialog appears
REM and projectors auto-assign via the AHK kick).

REM --- Pre-launch: clear any crash-recovery state that could trigger the prompt ---
del /q "%USERPROFILE%\Documents\Resolume Arena\Preferences\*.recovery" 2>nul
del /q "%USERPROFILE%\Documents\Resolume Arena\Preferences\*.bak" 2>nul
del /q "%LOCALAPPDATA%\Resolume Arena\recovery*"              2>nul
del /q "%LOCALAPPDATA%\Resolume Arena\*.recovery"             2>nul
del /q "%APPDATA%\Resolume Arena 7\recovery*"                 2>nul
del /q "%APPDATA%\Resolume Arena\recovery*"                   2>nul

REM --- Launch Arena with composition + experimental suppression flag ---
start "" "C:\Program Files\Resolume Arena\Arena.exe" --suppressCompositionChangeConfirmation "C:\Users\user\Documents\Resolume Arena\Compositions\SSD-Exhibition V1 to Mahon Hall VF.avc"
