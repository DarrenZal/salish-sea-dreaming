@echo off
curl -s http://localhost:7002/mode/live
echo Switched to LIVE mode
timeout /t 2
