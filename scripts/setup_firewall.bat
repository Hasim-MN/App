@echo off
title MediaFlow Firewall Setup
echo ========================================================
echo  MediaFlow - Open Port 8000 in Windows Firewall
echo ========================================================
echo.
echo Requesting Administrator privileges to open port 8000...
echo (Please click YES on the Windows prompt)
echo.

powershell -Command "Start-Process cmd -ArgumentList '/c netsh advfirewall firewall delete rule name=\"MediaFlow Port 8000\" & netsh advfirewall firewall add rule name=\"MediaFlow Port 8000\" dir=in action=allow protocol=TCP localport=8000 profile=any & echo. & echo ============================================== & echo  Port 8000 successfully opened for all networks! & echo ============================================== & echo. & pause' -Verb RunAs"

echo Done. Please check the Administrator window that opened.
pause
