@echo off
REM autolume_walk_test.bat — quick test of walk_speed override.
REM Runs ONE variant (walk_speed=0.05) for 8 seconds to validate the dial.
REM 2026-05-25.

set PRESET_DIR=C:\Users\user\Documents\presets\0
set MODEL_PKL=C:\Users\user\Documents\models\network-snapshot-000120.pkl
set SWEEP_SCRIPT=C:\Users\user\autolume_sweep.py
set AUTOLUME_DIR=C:\Users\user\autolume
set VARIANTS_FILE=C:\Users\user\variants_baseline_no_override.json

for /f "delims=" %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set STAMP=%%i
set OUTPUT_DIR=C:\Users\user\autolume_walk_test\%STAMP%
mkdir "%OUTPUT_DIR%" 2>nul

call C:\Users\user\miniconda3\Scripts\activate.bat
call conda activate autolume

cd /d %AUTOLUME_DIR%

echo [walk_test] starting at %DATE% %TIME% > "C:\Users\user\autolume_walk_test_run.log"
echo [walk_test] output dir: %OUTPUT_DIR% >> "C:\Users\user\autolume_walk_test_run.log"

python %SWEEP_SCRIPT% ^
  --pkl "%MODEL_PKL%" ^
  --preset "%PRESET_DIR%" ^
  --output-dir "%OUTPUT_DIR%" ^
  --autolume-dir "%AUTOLUME_DIR%" ^
  --variants-file "%VARIANTS_FILE%" ^
  --record-seconds 8 --settle-seconds 4 >> "C:\Users\user\autolume_walk_test_run.log" 2>&1

echo [walk_test] exit code %ERRORLEVEL% at %DATE% %TIME% >> "C:\Users\user\autolume_walk_test_run.log"
echo Done. Output: %OUTPUT_DIR%
