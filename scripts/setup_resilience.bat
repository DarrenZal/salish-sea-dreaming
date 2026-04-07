@echo off
REM setup_resilience.bat — Register TouchDesigner auto-launch + watchdog for the 16-day exhibition.
REM Run ONCE as Administrator on April 9 setup day, AFTER setup_nssm.bat.
REM
REM Creates two Task Scheduler tasks:
REM   SSD-TouchDesigner  — launches TouchDesigner .toe on logon (30s delay)
REM   SSD-TD-Watchdog    — PowerShell watchdog; restarts TD if it crashes (checks every 2 min)
REM
REM IMPORTANT: Update TOE_FILE and PS_SCRIPT paths below if the files move.
REM            Both tasks run with highest privileges so TD can write logs etc.

setlocal

set SCRIPT_DIR=%~dp0
set TOE_FILE=C:\Users\user\Desktop\SalishSeaDreaming.toe
set LAUNCH_BAT=%SCRIPT_DIR%launch_td.bat
set PS_SCRIPT=%SCRIPT_DIR%td_watchdog.ps1

echo === SSD Resilience Setup ===
echo Script dir: %SCRIPT_DIR%
echo .toe file:  %TOE_FILE%
echo.

REM ── Check prerequisites ────────────────────────────────────────────────────
if not exist "%LAUNCH_BAT%" (
    echo ERROR: launch_td.bat not found at %LAUNCH_BAT%
    echo Make sure you are running from the scripts\ directory.
    pause & exit /b 1
)
if not exist "%PS_SCRIPT%" (
    echo ERROR: td_watchdog.ps1 not found at %PS_SCRIPT%
    echo Make sure you are running from the scripts\ directory.
    pause & exit /b 1
)

REM ── SSD-TouchDesigner: auto-launch TD on logon ────────────────────────────
echo [1/2] Registering SSD-TouchDesigner task...
schtasks /delete /tn "SSD-TouchDesigner" /f >nul 2>&1
schtasks /create ^
  /tn "SSD-TouchDesigner" ^
  /tr "\"%LAUNCH_BAT%\"" ^
  /sc onlogon ^
  /rl highest ^
  /f
if errorlevel 1 (
    echo   FAILED to register SSD-TouchDesigner. Are you running as Administrator?
) else (
    echo   SSD-TouchDesigner registered.
)

REM ── SSD-TD-Watchdog: PowerShell crash watchdog ────────────────────────────
echo [2/2] Registering SSD-TD-Watchdog task...
schtasks /delete /tn "SSD-TD-Watchdog" /f >nul 2>&1
schtasks /create ^
  /tn "SSD-TD-Watchdog" ^
  /tr "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File \"%PS_SCRIPT%\"" ^
  /sc onlogon ^
  /rl highest ^
  /f
if errorlevel 1 (
    echo   FAILED to register SSD-TD-Watchdog.
) else (
    echo   SSD-TD-Watchdog registered.
)

echo.
echo === Manual steps still required ===
echo.
echo   1. Enable Windows auto-login (no password on boot):
echo      Run: netplwiz
echo      Uncheck "Users must enter a username and password"
echo      Enter password when prompted to save it.
echo.
echo   2. Confirm AUDIO_DEVICE_INDEX in .env is correct:
echo      python scripts\gallery_audio.py --list-devices
echo      Then set AUDIO_DEVICE_INDEX=N in .env
echo.
echo   3. TEST full power-loss recovery (do this before April 10):
echo      a. With everything running, do Start > Shut Down (full shutdown)
echo      b. Power back on
echo      c. Confirm: auto-login, NSSM services start, TD opens with .toe
echo      d. Submit test prompt via web app QR
echo      e. Kill TD manually: taskkill /F /IM TouchDesigner.exe
echo      f. Wait 2-3 min, confirm watchdog restarts TD
echo.

schtasks /query /tn "SSD-TouchDesigner" /fo list 2>nul | findstr "Status"
schtasks /query /tn "SSD-TD-Watchdog"   /fo list 2>nul | findstr "Status"

echo.
echo Done.
pause
