@echo off
REM autolume_sweep.bat — run the 5-variant Autolume sweep using preset 0.
REM
REM Mirrors launch_autolume_autostart.bat for env setup, then invokes
REM autolume_sweep.py instead of autolume_autostart.py.
REM
REM Output: C:\Users\user\autolume_sweep\<YYYYMMDD-HHMM>\NN_<name>.mp4
REM Log:    C:\Users\user\autolume_sweep_run.log

set PRESET_DIR=C:\Users\user\Documents\presets\0
set MODEL_PKL=C:\Users\user\Documents\models\network-snapshot-000120.pkl
set SWEEP_SCRIPT=C:\Users\user\autolume_sweep.py
set AUTOLUME_DIR=C:\Users\user\autolume

REM Build timestamped output dir (YYYYMMDD-HHMM). PowerShell because cmd's %date%
REM and %time% formats are locale-dependent and flaky.
for /f "delims=" %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set STAMP=%%i
set OUTPUT_DIR=C:\Users\user\autolume_sweep\%STAMP%
mkdir "%OUTPUT_DIR%" 2>nul

call C:\Users\user\miniconda3\Scripts\activate.bat
call conda activate autolume

cd /d %AUTOLUME_DIR%

echo [autolume_sweep] starting at %DATE% %TIME% > "C:\Users\user\autolume_sweep_run.log"
echo [autolume_sweep] output dir: %OUTPUT_DIR% >> "C:\Users\user\autolume_sweep_run.log"

REM Settle 6s covers Autolume's cold-start (~5s) so variant 01 doesn't get short-changed.
REM Record 20s @ 30fps target = 600 record_frames; actual capture rate is ~75%
REM so output clips run ~15s playback. Adjust if Pravin wants longer/shorter.
python %SWEEP_SCRIPT% ^
  --pkl "%MODEL_PKL%" ^
  --preset "%PRESET_DIR%" ^
  --output-dir "%OUTPUT_DIR%" ^
  --autolume-dir "%AUTOLUME_DIR%" ^
  --record-seconds 20 --settle-seconds 6 >> "C:\Users\user\autolume_sweep_run.log" 2>&1

echo [autolume_sweep] exit code %ERRORLEVEL% at %DATE% %TIME% >> "C:\Users\user\autolume_sweep_run.log"
echo Done. Output: %OUTPUT_DIR%
