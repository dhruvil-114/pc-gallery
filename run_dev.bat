@echo off
title Local AI Photo Gallery (Dev Mode)
echo ========================================================
echo       Launching Local AI Photo Gallery - Dev Mode
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=backend

echo Starting FastAPI backend on http://localhost:8000 ...
start "Backend (FastAPI)" cmd /k "set PYTHONPATH=backend && py -m uvicorn app.main:app --reload --port 8000"

echo Starting Vite frontend on http://localhost:5173 ...
start "Frontend (Vite)" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul
start http://localhost:5173
