@echo off
setlocal enabledelayedexpansion

echo ============================================
echo       Synth Mind - Setup / Assembly
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

:: Check if we're in the right directory
if not exist "run_synth.py" (
    echo [ERROR] run_synth.py not found.
    echo Please run this script from the synth-mind directory.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo       Virtual environment created.
) else (
    echo [1/4] Virtual environment already exists.
)
echo.

:: Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

:: Install/upgrade dependencies
echo [3/4] Installing dependencies...
echo       This may take a few minutes on first run...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo       Dependencies installed successfully.
echo.

:: LLM Provider Configuration
echo [4/4] LLM Provider Configuration
echo.

:: Check existing configuration
set "HAS_CONFIG=0"
if defined ANTHROPIC_API_KEY set "HAS_CONFIG=1"
if defined OPENAI_API_KEY set "HAS_CONFIG=1"
if defined OLLAMA_MODEL set "HAS_CONFIG=1"

if exist ".env" (
    echo       Found existing .env file.
    set "HAS_CONFIG=1"
)

if "%HAS_CONFIG%"=="1" (
    echo       LLM provider already configured.
    goto :setup_complete
)

:: Prompt user for configuration
echo.
echo No LLM provider configured. Choose an option:
echo.
echo   [1] Anthropic Claude (recommended)
echo   [2] OpenAI GPT
echo   [3] Ollama (local, no API key needed)
echo   [4] Skip - I'll configure later
echo.
set /p "CHOICE=Enter choice (1-4): "

if "%CHOICE%"=="1" (
    echo.
    set /p "API_KEY=Enter your Anthropic API key: "
    echo ANTHROPIC_API_KEY=!API_KEY!> .env
    echo ANTHROPIC_MODEL=claude-sonnet-4-20250514>> .env
    echo.
    echo [OK] Anthropic Claude configured.
) else if "%CHOICE%"=="2" (
    echo.
    set /p "API_KEY=Enter your OpenAI API key: "
    echo OPENAI_API_KEY=!API_KEY!> .env
    echo OPENAI_MODEL=gpt-4>> .env
    echo.
    echo [OK] OpenAI GPT configured.
) else if "%CHOICE%"=="3" (
    echo OLLAMA_MODEL=llama3.2> .env
    echo OLLAMA_BASE_URL=http://localhost:11434>> .env
    echo.
    echo [OK] Ollama configured (using llama3.2).
    echo [NOTE] Make sure Ollama is running before starting: ollama serve
) else (
    echo.
    echo [SKIP] No LLM configured.
    echo        Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or OLLAMA_MODEL
    echo        in your environment or create a .env file.
)

:setup_complete
echo.
echo ============================================
echo         Setup Complete!
echo ============================================
echo.
echo Directory structure:
echo   venv\          - Python virtual environment
echo   state\         - Created on first run (memory, logs)
echo   config\        - Personality and peer configuration
echo.
echo Next steps:
echo   1. Run start.bat to launch Synth Mind (CLI only)
echo   2. Run start_dashboard.bat to launch with web dashboard
echo.
echo ============================================

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat 2>nul

pause
