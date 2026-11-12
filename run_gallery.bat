@echo off
title Local AI Photo Gallery
echo ========================================================
echo         Launching Local AI Photo Gallery (PC)
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=backend

echo Starting backend server on port 8000...
start /b py -m uvicorn app.main:app --port 8000 --host 127.0.0.1

timeout /t 2 /nobreak >nul

echo Opening browser at http://localhost:8000 ...
start http://localhost:8000

echo.
echo Gallery is running! Keep this window open. Press Ctrl+C to stop.
echo ========================================================
echo.
pause
