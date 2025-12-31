@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Synth Mind - CLI + Dashboard
echo ============================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [NOTE] Virtual environment not found.
    echo        Running setup_and_run.bat first...
    call setup_and_run.bat
    exit /b
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Load .env if exists
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)

echo [OK] Starting Synth Mind with Dashboard...
echo.
echo Dashboard will open at: http://localhost:8080
echo.

:: Run with dashboard
python run_synth_with_dashboard.py

call venv\Scripts\deactivate.bat 2>nul
pause
