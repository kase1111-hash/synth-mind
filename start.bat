@echo off
setlocal enabledelayedexpansion

echo ============================================
echo          Synth Mind - Starting
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

:: Check if run_synth.py exists
if not exist "run_synth.py" (
    echo [ERROR] run_synth.py not found.
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

echo [OK] Starting Synth Mind...
echo.
echo ============================================
echo   Commands:
echo     /state    - View internal state
echo     /dream    - Show dream buffer
echo     /reflect  - Force meta-reflection
echo     /project  - Start/manage projects
echo     /help     - Show all commands
echo     /quit     - Save and exit
echo ============================================
echo.

:: Run the application
python run_synth.py

:: Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat 2>nul

echo.
echo Synth Mind has exited.
pause
