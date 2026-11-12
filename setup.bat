@echo off
setlocal enabledelayedexpansion
title PC Gallery - Complete Auto Setup

echo ======================================================================
echo           PC GALLERY - LOCAL AI PHOTO GALLERY SETUP
echo ======================================================================
echo.
echo This script will check all prerequisites, install all required
echo Python packages, frontend dependencies, AI models, and build the app.
echo.

cd /d "%~dp0"

:: ------------------------------------------------------------------------
:: 1. Check Python
:: ------------------------------------------------------------------------
echo [1/6] Checking Python installation...

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
    echo.
    echo [ERROR] Python is not installed or not found in PATH!
    echo Please install Python 3.10 or newer from https://www.python.org/downloads/
    echo IMPORTANT: Make sure to check the box "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('%PY_CMD% --version 2^>^&1') do set PY_VER=%%i
echo   Found: %PY_VER% using command: %PY_CMD%

:: ------------------------------------------------------------------------
:: 2. Check Node.js and NPM
:: ------------------------------------------------------------------------
echo.
echo [2/6] Checking Node.js and NPM...

where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Node.js / NPM is not installed or not found in PATH!
    echo Please install Node.js (LTS version) from https://nodejs.org/
    echo After installing Node.js, re-run this setup script.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('cmd /c "npm --version"') do set NPM_VER=%%i
echo   Found NPM version: %NPM_VER%

:: ------------------------------------------------------------------------
:: 3. Prepare Folder Structure
:: ------------------------------------------------------------------------
echo.
echo [3/6] Preparing database and cache directories...
if not exist "backend\data" mkdir "backend\data"
if not exist "backend\data\.gallery_cache\thumbnails" mkdir "backend\data\.gallery_cache\thumbnails"
if not exist "backend\data\.gallery_cache\people" mkdir "backend\data\.gallery_cache\people"
if not exist "backend\data\models" mkdir "backend\data\models"
echo   Directories ready.

:: ------------------------------------------------------------------------
:: 4. Install Python Backend Dependencies
:: ------------------------------------------------------------------------
echo.
echo [4/6] Installing Python backend dependencies...
echo   (FastAPI, Uvicorn, SQLAlchemy, Pillow, OpenCV, NumPy...)
echo.
%PY_CMD% -m pip install -r backend\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to install Python dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo.
echo   Python dependencies installed successfully!

:: ------------------------------------------------------------------------
:: 5. Download AI Facial Recognition Models
:: ------------------------------------------------------------------------
echo.
echo [5/6] Verifying AI facial detection & clustering models...
%PY_CMD% backend\app\download_models.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to download AI models.
    pause
    exit /b 1
)

:: ------------------------------------------------------------------------
:: 6. Install Frontend Dependencies & Build Production UI
:: ------------------------------------------------------------------------
echo.
echo [6/6] Installing frontend packages and building desktop UI...
cd frontend
echo   Installing NPM packages...
call cmd /c "npm install"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Frontend npm install failed.
    cd ..
    pause
    exit /b 1
)

echo   Building production web application...
call cmd /c "npm run build"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Frontend build failed.
    cd ..
    pause
    exit /b 1
)
cd ..

:: ------------------------------------------------------------------------
:: 7. Initialize Database Tables
:: ------------------------------------------------------------------------
echo.
echo Initializing SQLite database...
%PY_CMD% -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()"
echo   Database initialized.

echo.
echo ======================================================================
echo              SETUP COMPLETED SUCCESSFULLY! 🎉
echo ======================================================================
echo.
echo You are ready to run the Local AI Photo Gallery!
echo You can double-click 'run.bat' anytime to launch the application.
echo.
set /p LAUNCH_NOW="Do you want to launch the gallery right now? (Y/N): "
if /i "%LAUNCH_NOW%"=="Y" (
    call run.bat
) else (
    echo.
    echo Exiting setup. Run 'run.bat' whenever you are ready!
    pause
)
