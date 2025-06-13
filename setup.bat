@echo off
setlocal enabledelayedexpansion

REM Aura AI Project Setup Script - Windows Version
REM Auto check environment, install dependencies, configure services

echo ========================================
echo Aura AI Project Setup Assistant
echo ========================================

REM Check Python
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed, please install Python 3.11+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo OK: Python version: !PYTHON_VERSION!
)

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip not installed, please install pip first
    pause
    exit /b 1
)

REM Create virtual environment option
echo.
set /p create_venv="Create Python virtual environment? (recommended) (y/N): "
if /i "!create_venv!"=="y" (
    echo Creating virtual environment...
    python -m venv aura_env
    
    REM Activate virtual environment
    call aura_env\Scripts\activate.bat
    echo OK: Virtual environment created and activated
    echo TIP: Next time run: aura_env\Scripts\activate.bat
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Dependency installation failed, check network connection
    pause
    exit /b 1
) else (
    echo OK: Python dependencies installed
)

REM Check Ollama
echo.
echo Checking Ollama service...
curl -s http://localhost:11435/api/tags >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ollama service not running
    echo Please install and start Ollama first:
    echo    1. Visit https://ollama.ai/ to download
    echo    2. Run: ollama serve
    echo    3. Download model: ollama pull qwen3:4b
    
    set /p install_ollama="Open Ollama download page now? (y/N): "
    if /i "!install_ollama!"=="y" (
        start https://ollama.ai/
    )
) else (
    echo OK: Ollama service is running
    
    REM Check model
    ollama list | findstr "qwen3" >nul 2>&1
    if errorlevel 1 (
        echo Downloading qwen3:4b model...
        ollama pull qwen3:4b
        echo OK: Model download completed
    ) else (
        echo OK: qwen3:4b model installed
    )
)

REM Configure environment file
echo.
echo Configuring environment file...
if not exist .env (
    copy .env.example .env >nul
    echo OK: Created .env configuration file
) else (
    echo INFO: .env file already exists
)

REM Create necessary directories
echo.
echo Creating necessary directories...
if not exist data mkdir data
if not exist db mkdir db
if not exist logs mkdir logs
if not exist memory mkdir memory
echo OK: Directories created

REM Docker environment check
echo.
echo Checking Docker environment...
docker --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker not installed, will use local Python environment
    echo For Docker support, please install Docker Desktop
) else (
    echo OK: Docker installed
    
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Docker Compose not installed
    ) else (
        echo OK: Docker Compose installed
        echo TIP: Can use Docker deployment: start_aura.bat
    )
)

REM Setup complete
echo.
echo Aura AI Setup Complete!
echo.
echo Startup Options:
echo 1. Local Python environment:
echo    python aura.py
echo.
echo 2. Web API mode:
echo    python aura_api.py
echo.
echo 3. Docker mode:
echo    start_aura.bat
echo.
echo For more information, see README.md

REM Ask if start now
echo.
set /p start_now="Start Aura now? (y/N): "
if /i "!start_now!"=="y" (
    echo Starting Aura AI...
    python aura.py
)

pause