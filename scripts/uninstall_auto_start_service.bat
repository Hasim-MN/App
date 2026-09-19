@echo off
title MediaFlow - Remove Auto-Start
echo ========================================================
echo  MediaFlow Downloader - Remove Auto-Start
echo ========================================================
echo.

set STARTUP_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MediaFlow_AlwaysOn.lnk

if exist "%STARTUP_LNK%" (
    del /f /q "%STARTUP_LNK%"
    echo [SUCCESS] MediaFlow Auto-Start shortcut removed from Startup folder.
) else (
    echo [NOTICE] MediaFlow Auto-Start was not found in Startup folder.
)

schtasks /delete /tn "MediaFlow_AlwaysOn" /f >nul 2>&1

echo.
pause
