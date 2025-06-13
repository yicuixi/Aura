@echo off
echo ==========================================
echo     Aura AI Launcher (Fixed Version)
echo ==========================================
echo.
echo Fixed: Think tag issue resolved
echo Model: qwen3:4b
echo.

echo Checking Ollama service...
curl -s http://localhost:11435/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama service not running
    echo Please start Ollama first: ollama serve
    pause
    exit /b 1
)

echo OK: Ollama service is running

echo.
echo Checking qwen3:4b model...
curl -s http://localhost:11435/api/show -d "{\"name\":\"qwen3:4b\"}" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: qwen3:4b model not found
    echo Downloading model...
    ollama pull qwen3:4b
    if %errorlevel% neq 0 (
        echo ERROR: Model download failed
        pause
        exit /b 1
    )
)

echo OK: qwen3:4b model ready

echo.
echo Starting Aura AI (Fixed Version)...
echo Multi-layer protection activated, Think tags disabled
echo.
python aura.py

echo.
echo Program exited. Press any key to close...
pause >nul