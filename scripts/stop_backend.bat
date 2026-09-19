@echo off
title Stop MediaFlow Backend & Tunnel
echo ========================================================
echo  Stopping MediaFlow Backend & Remote Tunnel...
echo ========================================================
echo.

powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped backend process with PID:' $_.OwningProcess }"

taskkill /F /IM cloudflared.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo Stopped cloudflared tunnel process.
)

echo.
echo All MediaFlow services have been stopped.
pause

