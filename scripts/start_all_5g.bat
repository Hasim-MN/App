@echo off
title MediaFlow - Backend + 5G Remote Launcher
echo ========================================================
echo  MediaFlow - Unlimited Free Downloads Everywhere
echo  Starting Backend Server and 5G Cloudflare Tunnel...
echo ========================================================
echo.

start "MediaFlow Backend" cmd /k "call "%~dp0start_backend.bat""
timeout /t 3 /nobreak >nul
start "MediaFlow 5G Tunnel" cmd /k "call "%~dp0start_tunnel.bat""

echo.
echo Both windows have been launched:
echo 1. MediaFlow Backend (Python server on port 8000)
echo 2. Cloudflare 5G Tunnel (Generates a public https link)
echo.
echo Copy the "https://....trycloudflare.com" link from the
echo Tunnel window and paste it into your MediaFlow Android app!
echo.
pause
