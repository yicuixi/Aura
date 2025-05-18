@echo off
echo =====================================
echo     Aura Git Cleanup Script
echo =====================================
echo.

REM Create backup directory
if not exist "backup_before_cleanup" mkdir "backup_before_cleanup"

REM Stop possible running processes
echo Stopping possible Python processes...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Delete log files
echo Removing log files...
del /q aura.log 2>nul
rmdir /s /q logs 2>nul

REM Delete cache files
echo Removing Python cache...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q query_handlers\__pycache__ 2>nul
rmdir /s /q docker\searxng\__pycache__ 2>nul

REM Delete database and runtime data
echo Removing database files...
rmdir /s /q db 2>nul
rmdir /s /q open-webui-data 2>nul
rmdir /s /q qdrant_data 2>nul
rmdir /s /q ollama 2>nul
rmdir /s /q memory 2>nul

REM Delete runtime generated files
echo Removing runtime files...
del /q memory.json 2>nul
del /q env_path.txt 2>nul
del /q deleted 2>nul
del /q CLEANUP_REPORT.md 2>nul

echo.
echo =====================================
echo     Cleanup Complete!
echo =====================================
echo.
echo Files kept:
echo - Core Python files
echo - Config files (.env, requirements.txt)
echo - Documentation and templates
echo - Sample data files
echo.
echo Personal info backed up to: backup_before_cleanup
echo.
echo Ready for Git initialization!
echo.
pause
