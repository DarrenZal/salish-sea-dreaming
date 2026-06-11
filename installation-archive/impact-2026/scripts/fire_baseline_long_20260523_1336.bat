@echo off
set PRESET_DIR=C:\Users\user\Documents\presets\0
set MODEL_PKL=C:\Users\user\Documents\models\network-snapshot-000120.pkl
set SWEEP_SCRIPT=C:\Users\user\autolume_sweep.py
set AUTOLUME_DIR=C:\Users\user\autolume
set OUTPUT_DIR=C:\Users\user\autolume_20min\20260523_1336
set VARIANTS_FILE=C:\Users\user\variants_baseline_long.json
set LOG_FILE=C:\Users\user\autolume_20min_20260523_1336.log

mkdir "%OUTPUT_DIR%"

echo [fire_baseline_long] starting at %DATE% %TIME% > "%LOG_FILE%"
echo [fire_baseline_long] output: %OUTPUT_DIR% >> "%LOG_FILE%"
echo [fire_baseline_long] record-seconds: 1800 >> "%LOG_FILE%"

call C:\Users\user\miniconda3\Scripts\activate.bat
call conda activate autolume

cd /d %AUTOLUME_DIR%

python %SWEEP_SCRIPT% --pkl "%MODEL_PKL%" --preset "%PRESET_DIR%" --output-dir "%OUTPUT_DIR%" --autolume-dir "%AUTOLUME_DIR%" --record-seconds 1800 --settle-seconds 5 --variants-file "%VARIANTS_FILE%" >> "%LOG_FILE%" 2>&1

echo [fire_baseline_long] exit code %ERRORLEVEL% at %DATE% %TIME% >> "%LOG_FILE%"
