@echo off
title MediaFlow - Install 24/7 Auto-Start
echo ========================================================
echo  MediaFlow Downloader - Install Auto-Start on Boot
echo ========================================================
echo.
echo Installing MediaFlow into your Windows Startup folder...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_startup_shortcut.ps1"

echo.
echo ========================================================
echo  MediaFlow Auto-Start Setup Complete!
echo ========================================================
echo.
echo  Trigger:  Automatically starts every time your laptop boots or logs in.
echo  Mode:     Silent background (no console windows).
echo.
echo  To remove auto-start anytime, run:
echo  scripts\uninstall_auto_start_service.bat
echo ========================================================
echo.
pause
