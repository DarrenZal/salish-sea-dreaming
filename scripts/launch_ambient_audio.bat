@echo off
REM launch_ambient_audio.bat — Task Scheduler launcher for the ambient audio loop.
REM
REM Invokes gallery_ambient_audio.ps1 in a hidden window so it runs silently
REM in the background. Kill via Task Scheduler stop, or Stop-Process for the
REM PowerShell PID.

powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Users\user\gallery_ambient_audio.ps1
