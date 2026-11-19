@echo off
title Kill Processes on Port 8000 and 3000
echo ========================================================
echo    Stopping all processes on port 8000 and 3000
echo ========================================================
echo.

setlocal enabledelayedexpansion

echo Checking port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":8000[ ]"') do (
    if not "%%a"=="0" (
        echo Killing process PID %%a on port 8000...
        taskkill /F /PID %%a 2>nul
    )
)

echo Checking port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":3000[ ]"') do (
    if not "%%a"=="0" (
        echo Killing process PID %%a on port 3000...
        taskkill /F /PID %%a 2>nul
    )
)

echo.
echo ========================================================
echo [OK] Ports 8000 and 3000 have been freed.
echo ========================================================
pause
