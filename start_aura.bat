@echo off
echo ==========================================
echo     Aura AI (ReAct Agent)
echo ==========================================
echo.

echo Checking Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama service not running
    echo Please start Ollama first
    pause
    exit /b 1
)
echo OK: Ollama service is running

echo.
echo Starting Aura AI...
python aura_react.py

echo.
echo Program exited. Press any key to close...
pause >nul

pause >nul