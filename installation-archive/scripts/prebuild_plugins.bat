@echo off
call C:\Users\user\miniconda3\Scripts\activate.bat
call conda activate autolume
cd /d C:\Users\user\autolume

REM kill stuck cache
rmdir /s /q "C:\Users\user\AppData\Local\torch_extensions\torch_extensions\Cache\py310_cu128\bias_act_plugin" 2>/dev/null

REM Pre-build ONE plugin, single-process, verbose output
python -u -c "import sys, time; sys.path.insert(0,'C:/Users/user/autolume'); print('[prebuild] importing bias_act', flush=True); from torch_utils.ops import bias_act; t0=time.time(); print('[prebuild] calling _init()', flush=True); ok=bias_act._init(); print('[prebuild] _init() returned', ok, 'in', round(time.time()-t0,1), 's', flush=True); print('[prebuild] plugin obj:', bias_act._plugin, flush=True)"
