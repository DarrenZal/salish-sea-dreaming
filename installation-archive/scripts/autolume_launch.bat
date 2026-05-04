@echo off
REM Launch multiple Autolume instances with unique NDI names and OSC ports.
REM
REM Autolume hardcodes NDI name and OSC ports in modules/visualizer.py,
REM so we run each instance from a separate directory with patched config.
REM
REM Usage: autolume_launch.bat [fish|whale|bird|all]
REM
REM Instance config:
REM   Fish:  NDI=Autolume-Fish,  OSC recv=1338, send=1337
REM   Whale: NDI=Autolume-Whale, OSC recv=1340, send=1339
REM   Bird:  NDI=Autolume-Bird,  OSC recv=1342, send=1341

set BASE_DIR=C:\Users\user\autolume
set MODELS_DIR=C:\Users\user\autolume\models
set CONDA_BAT=C:\Users\user\miniconda3\Scripts\activate.bat

if "%1"=="" goto usage
if "%1"=="all" goto all
if "%1"=="fish" goto fish
if "%1"=="whale" goto whale
if "%1"=="bird" goto bird
goto usage

:fish
echo Starting Autolume-Fish...
call :launch_instance fish Autolume-Fish 1338 1337 %MODELS_DIR%\fish-400kimg.pkl
goto :eof

:whale
echo Starting Autolume-Whale...
call :launch_instance whale Autolume-Whale 1340 1339 %MODELS_DIR%\whale.pkl
goto :eof

:bird
echo Starting Autolume-Bird...
call :launch_instance bird Autolume-Bird 1342 1341 %MODELS_DIR%\bird.pkl
goto :eof

:all
call :fish
call :whale
call :bird
echo All three Autolume instances started.
goto :eof

:launch_instance
REM %1=instance_name %2=ndi_name %3=osc_in_port %4=osc_out_port %5=model_pkl
set INST_DIR=C:\Users\user\autolume-%1

REM Create instance directory if needed (symlink to save disk space)
if not exist %INST_DIR% (
    echo Creating instance directory: %INST_DIR%
    xcopy /E /I /Q %BASE_DIR% %INST_DIR%
)

REM Patch visualizer.py for this instance
python C:\Users\user\autolume\patch_instance.py %INST_DIR%\modules\visualizer.py %2 %3 %4

REM Launch in new window
start "%2" cmd /k "call %CONDA_BAT% && conda activate autolume && cd %INST_DIR% && python main.py"
goto :eof

:usage
echo Usage: autolume_launch.bat [fish^|whale^|bird^|all]
echo.
echo Instances:
echo   fish  - Autolume-Fish  (NDI, OSC 1338/1337)
echo   whale - Autolume-Whale (NDI, OSC 1340/1339)
echo   bird  - Autolume-Bird  (NDI, OSC 1342/1341)
echo   all   - Launch all three
echo.
echo Each instance runs from a separate directory with patched NDI/OSC config.
echo Models should be placed in %MODELS_DIR%
