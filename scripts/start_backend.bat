@echo off
title MediaFlow Backend Server
echo ========================================================
echo  MediaFlow Downloader - FastAPI Backend
echo  Listening on: http://0.0.0.0:8000
echo  (Accessible from Localhost and Mobile on same Wi-Fi)
echo ========================================================
echo.

cd /d "%~dp0\.."
py -3.14 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
pause
