@echo off
REM autolume_wild30s.bat — render one ~30sec wild_psi120 clip.
REM Reads variants from autolume_wild30s_variants.json. 42s record + 6s settle
REM → ~30s captured output at 73% capture rate observed in v2 sweep.

set PRESET_DIR=C:\Users\user\Documents\presets\0
set MODEL_PKL=C:\Users\user\Documents\models\network-snapshot-000120.pkl
set SWEEP_SCRIPT=C:\Users\user\autolume_sweep.py
set VARIANTS_FILE=C:\Users\user\autolume_wild30s_variants.json
set AUTOLUME_DIR=C:\Users\user\autolume

for /f "delims=" %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set STAMP=%%i
set OUTPUT_DIR=C:\Users\user\autolume_sweep\wild30s-%STAMP%
mkdir "%OUTPUT_DIR%" 2>nul

call C:\Users\user\miniconda3\Scripts\activate.bat
call conda activate autolume

cd /d %AUTOLUME_DIR%

echo [autolume_wild30s] starting at %DATE% %TIME% > "C:\Users\user\autolume_wild30s_run.log"
echo [autolume_wild30s] output dir: %OUTPUT_DIR% >> "C:\Users\user\autolume_wild30s_run.log"

python %SWEEP_SCRIPT% ^
  --pkl "%MODEL_PKL%" ^
  --preset "%PRESET_DIR%" ^
  --output-dir "%OUTPUT_DIR%" ^
  --autolume-dir "%AUTOLUME_DIR%" ^
  --variants-file "%VARIANTS_FILE%" ^
  --record-seconds 42 --settle-seconds 6 >> "C:\Users\user\autolume_wild30s_run.log" 2>&1

echo [autolume_wild30s] exit code %ERRORLEVEL% at %DATE% %TIME% >> "C:\Users\user\autolume_wild30s_run.log"
echo Done. Output: %OUTPUT_DIR%
