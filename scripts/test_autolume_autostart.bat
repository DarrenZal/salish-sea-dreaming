@echo off
REM test_autolume_autostart.bat — interactive test of the autostart wrapper.
REM
REM Runs the autostart launcher in a visible console window so we can watch
REM stdout (model load, preset load, any errors). Use this BEFORE enabling
REM SSD-Autolume to validate the path + preset work as expected.
REM
REM Usage (from cmd, as the gallery user):
REM     scripts\test_autolume_autostart.bat
REM
REM To test with a different preset, temporarily edit PRESET_DIR here or
REM pass it in the last line.

set PRESET_DIR=C:\Users\user\Documents\presets\0
set MODEL_PKL=C:\Users\user\Documents\models\network-snapshot-000120.pkl
set AUTOSTART_SCRIPT=C:\Users\user\autolume_autostart.py
set AUTOLUME_DIR=C:\Users\user\autolume

echo === SSD Autolume Autostart — Test Mode ===
echo Preset: %PRESET_DIR%
echo Model:  %MODEL_PKL%
echo.

call C:\Users\user\miniconda3\Scripts\activate.bat
call conda activate autolume

cd /d %AUTOLUME_DIR%

python %AUTOSTART_SCRIPT% --pkl "%MODEL_PKL%" --preset "%PRESET_DIR%" --autolume-dir "%AUTOLUME_DIR%"

echo.
echo === Autolume exited ===
pause
