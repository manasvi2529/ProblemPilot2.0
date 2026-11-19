@echo off
title ProblemPilot AI - Launcher
echo ========================================================
echo    ProblemPilot AI: Launching Full-Stack Application
echo ========================================================
echo.
echo [1/2] Starting FastAPI Backend on Port 8000...
start "ProblemPilot Backend (Port 8000)" cmd /k ".\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Next.js Frontend on Port 3000...
start "ProblemPilot Next.js Frontend (Port 3000)" cmd /k "cd web && npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo Opening browser to http://localhost:3000 ...
start http://localhost:3000

echo.
echo [OK] Both servers are running in dedicated console windows.
echo - Frontend: http://localhost:3000
echo - Backend:  http://127.0.0.1:8000
echo Close those windows whenever you want to stop the servers.
pause
