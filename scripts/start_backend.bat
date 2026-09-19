@echo off
title MediaFlow Backend Server
echo ========================================================
echo  MediaFlow Downloader - FastAPI Backend
echo ========================================================
echo.

cd /d "%~dp0\.."

for /f "tokens=*" %%i in ('powershell -NoProfile -Command "(Get-NetIPConfiguration | Where-Object IPv4Address | Select-Object -ExpandProperty IPv4Address | Select-Object -First 1).IPAddress"') do set LOCAL_IP=%%i

if "%LOCAL_IP%"=="" (
    set LOCAL_IP=10.148.250.47
)

echo  Local PC:             http://localhost:8000
echo  Mobile (Permanent):   http://%COMPUTERNAME%.local:8000
echo  Mobile (Direct IP):   http://%LOCAL_IP%:8000
echo ========================================================
echo  * On your Android app, enter:
echo    http://%COMPUTERNAME%.local:8000   (recommended - never changes!)
echo    or http://%LOCAL_IP%:8000
echo  * If your phone cannot connect, run scripts\setup_firewall.bat
echo  * For 24/7 Always-On with lid closed, run scripts\setup_lid_always_on.bat
echo ========================================================
echo.

py -3.14 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
pause

