@echo off
REM setup_nssm.bat — Register gallery services with NSSM for unattended 16-day run
REM Run ONCE as Administrator before exhibition opens (April 9 setup day).
REM Requires: nssm.exe in PATH or same directory. Download: https://nssm.cc/download
REM
REM Services registered:
REM   ssd-server   — FastAPI gallery backend (uvicorn)
REM   ssd-relay    — SSE-to-OSC relay (td_relay.py)  ← NEW
REM   ssd-audio    — Audio monitor (gallery_audio.py)
REM   ssd-tunnel   — Cloudflare tunnel (cloudflared)

setlocal

REM --- Detect python and script paths ---
for /f "delims=" %%p in ('python -c "import sys; print(sys.executable)"') do set PYTHON=%%p
set SCRIPT_DIR=%~dp0
set REPO_DIR=%SCRIPT_DIR%..
cd /d "%REPO_DIR%"

if not exist logs mkdir logs

echo === Salish Sea Dreaming — NSSM Service Setup ===
echo Python: %PYTHON%
echo Repo:   %REPO_DIR%
echo.

REM ── ssd-server: FastAPI backend ──────────────────────────────────────────────
echo [1/4] Registering ssd-server...
nssm install ssd-server "%PYTHON%" -m uvicorn scripts.gallery_server:app --host 127.0.0.1 --port 8000 --workers 1
nssm set ssd-server AppDirectory "%REPO_DIR%"
nssm set ssd-server AppStdout    "%REPO_DIR%\logs\server.log"
nssm set ssd-server AppStderr    "%REPO_DIR%\logs\server.log"
nssm set ssd-server AppRotateFiles 1
nssm set ssd-server AppRotateBytes 10485760
nssm set ssd-server Start SERVICE_AUTO_START
nssm set ssd-server AppRestartDelay 5000
echo   ssd-server registered.

REM ── ssd-relay: SSE→OSC relay ─────────────────────────────────────────────────
echo [2/4] Registering ssd-relay...
nssm install ssd-relay "%PYTHON%" "%SCRIPT_DIR%td_relay.py"
nssm set ssd-relay AppDirectory "%REPO_DIR%"
nssm set ssd-relay AppStdout    "%REPO_DIR%\logs\relay.log"
nssm set ssd-relay AppStderr    "%REPO_DIR%\logs\relay.log"
nssm set ssd-relay AppRotateFiles 1
nssm set ssd-relay AppRotateBytes 5242880
nssm set ssd-relay Start SERVICE_AUTO_START
nssm set ssd-relay AppRestartDelay 5000
echo   ssd-relay registered.

REM ── ssd-audio: Audio monitor ──────────────────────────────────────────────────
echo [3/4] Registering ssd-audio...
nssm install ssd-audio "%PYTHON%" "%SCRIPT_DIR%gallery_audio.py"
nssm set ssd-audio AppDirectory "%REPO_DIR%"
nssm set ssd-audio AppStdout    "%REPO_DIR%\logs\audio.log"
nssm set ssd-audio AppStderr    "%REPO_DIR%\logs\audio.log"
nssm set ssd-audio AppRotateFiles 1
nssm set ssd-audio AppRotateBytes 5242880
nssm set ssd-audio Start SERVICE_AUTO_START
nssm set ssd-audio AppRestartDelay 5000
echo   ssd-audio registered.

REM ── ssd-tunnel: Cloudflare tunnel ────────────────────────────────────────────
echo [4/4] Registering ssd-tunnel...
for /f "tokens=2 delims==" %%v in ('findstr /i "TUNNEL_NAME" .env 2^>nul') do set TUNNEL_NAME=%%v
if not defined TUNNEL_NAME set TUNNEL_NAME=ssd-gallery
nssm install ssd-tunnel cloudflared tunnel run %TUNNEL_NAME%
nssm set ssd-tunnel AppStdout "%REPO_DIR%\logs\tunnel.log"
nssm set ssd-tunnel AppStderr "%REPO_DIR%\logs\tunnel.log"
nssm set ssd-tunnel Start SERVICE_AUTO_START
nssm set ssd-tunnel AppRestartDelay 5000
echo   ssd-tunnel registered.

echo.
echo === Starting all services ===
nssm start ssd-server
nssm start ssd-relay
nssm start ssd-audio
nssm start ssd-tunnel

echo.
echo === Status ===
nssm status ssd-server
nssm status ssd-relay
nssm status ssd-audio
nssm status ssd-tunnel

echo.
echo Done. Services will auto-start on reboot.
echo Monitor logs in: %REPO_DIR%\logs\
echo.
echo Useful commands:
echo   nssm status ssd-relay          — check relay
echo   nssm restart ssd-relay         — manual restart
echo   type logs\relay.log            — relay log tail
echo   nssm remove ssd-relay confirm  — unregister service
