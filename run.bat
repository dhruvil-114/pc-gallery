@echo off
setlocal enabledelayedexpansion
title Local AI Photo Gallery

echo ======================================================================
echo                  LOCAL AI PHOTO GALLERY (PC)
echo ======================================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=backend

:: Detect Python executable
set PY_CMD=
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=py
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PY_CMD=python
    )
)

if "%PY_CMD%"=="" (
    echo [ERROR] Python not found in PATH! Please run setup.bat first.
    pause
    exit /b 1
)

:: Check if frontend was built
if not exist "frontend\dist\index.html" (
    echo [WARNING] Production frontend build not found at frontend\dist!
    echo Please run 'setup.bat' first to automatically install dependencies and build the UI.
    echo.
    set /p RUN_SETUP="Would you like to run setup.bat now? (Y/N): "
    if /i "!RUN_SETUP!"=="Y" (
        call setup.bat
        exit /b 0
    ) else (
        exit /b 1
    )
)

echo Starting Photo Gallery Server on http://localhost:8000 ...
echo Backend API Docs available at http://localhost:8000/docs
echo.
echo ======================================================================
echo   Gallery is running!
echo   Keep this console window open while using the app.
echo   Press Ctrl + C in this window to stop the server anytime.
echo ======================================================================
echo.

:: Open default browser after a brief delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Start Uvicorn in the foreground so user sees logs and can Ctrl+C
%PY_CMD% -m uvicorn app.main:app --port 8000 --host 127.0.0.1

echo.
echo Gallery server has stopped.
pause
