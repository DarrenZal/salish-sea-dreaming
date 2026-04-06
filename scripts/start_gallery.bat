@echo off
REM Salish Sea Dreaming — Gallery startup script (Windows)
REM For production: use NSSM services (see plan's operational runbook)
REM This script is for development/testing only.

setlocal

set SCRIPT_DIR=%~dp0
set REPO_DIR=%SCRIPT_DIR%..
cd /d "%REPO_DIR%"

if not exist logs mkdir logs

REM Load TUNNEL_URL from .env if set (simple grep approach)
set TUNNEL_URL=https://ssd-gallery.cfargotunnel.com
set GALLERY_SERVER_PORT=8000
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="TUNNEL_URL" set TUNNEL_URL=%%b
    if "%%a"=="GALLERY_SERVER_PORT" set GALLERY_SERVER_PORT=%%b
)

echo === Salish Sea Dreaming Gallery ===

echo Starting backend server (logs\server.log)...
start /B "" python -m uvicorn scripts.gallery_server:app --host 127.0.0.1 --port %GALLERY_SERVER_PORT% --workers 1 >> logs\server.log 2>&1

echo Starting audio monitor (logs\audio.log)...
start /B "" python scripts\gallery_audio.py >> logs\audio.log 2>&1

echo Starting SSE relay (logs\relay.log)...
start /B "" python scripts\td_relay.py >> logs\relay.log 2>&1

echo.
REM Show local IP for LAN fallback
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo Visitor URL:  %TUNNEL_URL%
echo Admin URL:    %TUNNEL_URL%/admin
echo Local (LAN):  http://%LOCAL_IP%:%GALLERY_SERVER_PORT%
echo Health check: http://localhost:%GALLERY_SERVER_PORT%/health
echo.
echo Check NSSM services: nssm status ssd-server
echo Logs: type logs\server.log
echo.
