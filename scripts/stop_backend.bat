@echo off
title Stop MediaFlow Backend
echo Stopping any running MediaFlow backend on port 8000...

powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped process with PID:' $_.OwningProcess }"

echo Done.
pause
