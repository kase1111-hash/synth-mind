@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    Synth Mind - One-Click Setup ^& Run
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

:: Check if we're in the right directory
if not exist "run_synth.py" (
    echo [ERROR] run_synth.py not found.
    echo Please run this script from the synth-mind directory.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

:: Activate virtual environment
echo.
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install/upgrade dependencies
echo.
echo [SETUP] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Check for LLM configuration
echo.
echo ============================================
echo           LLM Provider Setup
echo ============================================

:: Check existing environment variables
set "HAS_CONFIG=0"
if defined ANTHROPIC_API_KEY set "HAS_CONFIG=1"
if defined OPENAI_API_KEY set "HAS_CONFIG=1"
if defined OLLAMA_MODEL set "HAS_CONFIG=1"

if "%HAS_CONFIG%"=="1" (
    echo [OK] LLM provider already configured.
    goto :run_app
)

:: Check for .env file
if exist ".env" (
    echo [OK] Found .env file, loading configuration...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
    goto :run_app
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
    set /p "API_KEY=Enter your Anthropic API key: "
    set "ANTHROPIC_API_KEY=!API_KEY!"
    echo ANTHROPIC_API_KEY=!API_KEY!> .env
    echo [OK] Anthropic configured
) else if "%CHOICE%"=="2" (
    set /p "API_KEY=Enter your OpenAI API key: "
    set "OPENAI_API_KEY=!API_KEY!"
    echo OPENAI_API_KEY=!API_KEY!> .env
    echo [OK] OpenAI configured
) else if "%CHOICE%"=="3" (
    set "OLLAMA_MODEL=llama3.2"
    echo OLLAMA_MODEL=llama3.2> .env
    echo [OK] Ollama configured (using llama3.2)
    echo [NOTE] Make sure Ollama is running: ollama serve
) else (
    echo [SKIP] No LLM configured. Set environment variables manually.
)

:run_app
echo.
echo ============================================
echo         Starting Synth Mind
echo ============================================
echo.
echo Commands while running:
echo   /state   - View internal state
echo   /dream   - Show dream buffer
echo   /reflect - Force reflection
echo   /project - Start a project
echo   /quit    - Save and exit
echo.
echo ============================================
echo.

:: Run the application
python run_synth.py

:: Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat 2>nul

echo.
echo Synth Mind has exited.
pause
