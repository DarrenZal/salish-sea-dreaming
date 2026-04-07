@echo off
REM launch_td.bat — Auto-launch TouchDesigner with the SSD .toe file on Windows logon.
REM Registered via setup_resilience.bat as a Task Scheduler task (SSD-TouchDesigner).
REM
REM IMPORTANT: Update TOE_FILE path below if the .toe moves.
REM            Run setup_resilience.bat as Administrator to (re)register the task.

setlocal

set TD_EXE=C:\Program Files\Derivative\TouchDesigner\TouchDesigner.exe
set TOE_FILE=C:\Users\user\Desktop\SalishSeaDreaming.toe

REM Wait 30s for NSSM services (gallery server, relay, tunnel) to fully start first
echo [%date% %time%] Waiting 30s for services to settle...
timeout /t 30 /nobreak

if not exist "%TD_EXE%" (
    echo [%date% %time%] ERROR: TouchDesigner not found at: %TD_EXE%
    echo Check installation and update TD_EXE path in this script.
    exit /b 1
)

if not exist "%TOE_FILE%" (
    echo [%date% %time%] WARNING: .toe file not found at: %TOE_FILE%
    echo Check path and update TOE_FILE in this script.
    REM Still launch TD without a file — manual recovery possible
    start "" "%TD_EXE%"
    exit /b 0
)

echo [%date% %time%] Launching TouchDesigner with %TOE_FILE%...
start "" "%TD_EXE%" "%TOE_FILE%"
