@echo off
REM launch_autolume_autostart.bat — used by the SSD-Autolume Task Scheduler task.
REM
REM Activates the autolume conda env and runs our autostart wrapper, which
REM boots Autolume directly into live render mode with the production model
REM and preset loaded.
REM
REM To change which preset loads, edit PRESET_DIR below.

set PRESET_DIR=C:\Users\user\Documents\presets\0
set MODEL_PKL=C:\Users\user\Documents\models\network-snapshot-000120.pkl
set AUTOSTART_SCRIPT=C:\Users\user\autolume_autostart.py
set AUTOLUME_DIR=C:\Users\user\autolume

REM Give the logon session a few seconds for audio/display to settle.
ping -n 16 127.0.0.1 > nul

call C:\Users\user\miniconda3\Scripts\activate.bat
call conda activate autolume

cd /d %AUTOLUME_DIR%

python %AUTOSTART_SCRIPT% --pkl "%MODEL_PKL%" --preset "%PRESET_DIR%" --autolume-dir "%AUTOLUME_DIR%"
