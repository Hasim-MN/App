@echo off
title MediaFlow - Connection URLs and Status
echo ========================================================
echo  MediaFlow Downloader - Server Connection Info
echo ========================================================
echo.

for /f "tokens=*" %%i in ('powershell -NoProfile -Command "(Get-NetIPConfiguration | Where-Object IPv4Address | Select-Object -ExpandProperty IPv4Address | Select-Object -First 1).IPAddress"') do set LOCAL_IP=%%i
if "%LOCAL_IP%"=="" set LOCAL_IP=10.148.250.47

echo  Local PC Browser:         http://localhost:8000
echo.
echo  --- CONNECT FROM PHONE (HOME WI-FI) ---
echo  Recommended (Permanent):  http://%COMPUTERNAME%.local:8000
echo  Direct IP:                http://%LOCAL_IP%:8000
echo.
echo  --- CONNECT FROM PHONE (5G / REMOTE WI-FI) ---
set TUNNEL_FOUND=0
if exist "%~dp0tunnel.log" (
    for /f "tokens=*" %%a in ('powershell -NoProfile -Command "$content = Get-Content -Path '%~dp0tunnel.log' -Raw -ErrorAction SilentlyContinue; if ($content) { $m = [regex]::Matches($content, 'https://[a-zA-Z0-9-]+\.trycloudflare\.com'); if ($m.Count -gt 0) { $m[$m.Count - 1].Value } }"') do (
        echo  Active 5G Public Link:    %%a
        set TUNNEL_FOUND=1
    )
)
if %TUNNEL_FOUND% equ 0 (
    echo  (5G Tunnel is not currently active. Run scripts\start_all_5g.bat to enable it)
)

echo.
echo ========================================================
echo  BACKEND STATUS CHECK:
echo ========================================================
powershell -NoProfile -Command "$running = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue; if ($running) { Write-Host ' [OK] MediaFlow Backend is ACTIVE on port 8000!' -ForegroundColor Green } else { Write-Host ' [STOPPED] MediaFlow Backend is NOT running.' -ForegroundColor Yellow; Write-Host ' Start it with: scripts\start_always_on_background.vbs' }"

echo.
pause
