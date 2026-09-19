@echo off
title MediaFlow - Cloudflare Tunnel (Remote 5G / Any Wi-Fi)
echo ========================================================
echo  MediaFlow Cloudflare Tunnel
echo  Enables 5G Mobile Data and Remote Access (Anywhere)
echo ========================================================
echo.
echo Starting secure tunnel to your PC backend (http://localhost:8000)...
echo Look for the "https://....trycloudflare.com" URL below!
echo.
echo ========================================================
echo.

"%~dp0cloudflared.exe" tunnel --url http://localhost:8000
pause
