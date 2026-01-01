@echo off
setlocal enabledelayedexpansion

echo ============================================
echo     Synth Mind - Starting with Dashboard
echo ============================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

:: Check if dashboard script exists
if not exist "dashboard\run_synth_with_dashboard.py" (
    echo [ERROR] Dashboard script not found.
    echo         Please run this script from the synth-mind directory.
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Load .env if exists
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)

:: Set default port if not specified
if not defined PORT set "PORT=8080"

:: Check LLM configuration
set "HAS_LLM=0"
if defined ANTHROPIC_API_KEY set "HAS_LLM=1"
if defined OPENAI_API_KEY set "HAS_LLM=1"
if defined OLLAMA_MODEL set "HAS_LLM=1"

if "%HAS_LLM%"=="0" (
    echo [WARNING] No LLM provider configured.
    echo           Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or OLLAMA_MODEL
    echo.
)

echo [OK] Starting Synth Mind with Dashboard...
echo.
echo ============================================
echo   Dashboard: http://localhost:%PORT%
echo   Timeline:  http://localhost:%PORT%/timeline
echo   Metrics:   http://localhost:%PORT%/metrics
echo   Health:    http://localhost:%PORT%/health
echo ============================================
echo.
echo   CLI Commands:
echo     /state    - View internal state
echo     /project  - Manage projects
echo     /quit     - Save and exit
echo ============================================
echo.

:: Run with dashboard
python dashboard\run_synth_with_dashboard.py

:: Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat 2>nul

echo.
echo Synth Mind has exited.
pause
