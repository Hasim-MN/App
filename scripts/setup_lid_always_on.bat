@echo off
title MediaFlow - 24/7 Always-On & Lid Closed Setup
echo ========================================================
echo  MediaFlow Downloader - 24/7 Always-On Setup
echo ========================================================
echo.
echo  Configuring Windows so your laptop stays running 24/7
echo  with the screen/lid CLOSED, allowing your phone to
echo  access and download media anytime!
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges to apply power settings...
    powershell -Command "Start-Process cmd -ArgumentList '/c call \"%~dp0setup_lid_always_on.bat\"' -Verb RunAs"
    exit /b
)

echo [1/4] Setting lid close action to "Do Nothing" (Plugged In / AC)...
powercfg /setacvalueindex SCHEME_CURRENT 4f971e89-eebd-4455-a8de-9e59040e7347 5ca83367-6e45-459f-a27b-476b1d01c936 0

echo [2/4] Disabling sleep timeout when plugged into power...
powercfg /change standby-timeout-ac 0

echo [3/4] Setting screen to turn off after 5 minutes (saves power & display life)...
powercfg /change monitor-timeout-ac 5

echo [4/4] Making "Lid close action" visible in Windows Control Panel...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\4f971e89-eebd-4455-a8de-9e59040e7347\5ca83367-6e45-459f-a27b-476b1d01c936" /v Attributes /t REG_DWORD /d 2 /f >nul 2>&1

:: Activate the power scheme immediately
powercfg /setactive SCHEME_CURRENT

echo.
echo ========================================================
echo  SUCCESS! Your laptop is now set for 24/7 Always-On!
echo ========================================================
echo.
echo  1. Keep your laptop plugged into its charger.
echo  2. You can now close the laptop lid anytime!
echo  3. The laptop screen turns off, but the server and Wi-Fi
echo     will stay 100%% active and responsive to your phone.
echo.
pause
