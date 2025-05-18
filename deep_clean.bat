@echo off
echo =====================================
echo     Deep Clean for Git
echo =====================================
echo.

REM Additional cleanup for unnecessary files

echo Removing duplicate and unnecessary files...

REM Remove redundant versions (keep only main aura.py)
del /q aura_webui.py 2>nul
del /q simple_aura.py 2>nul

REM Remove test and optimization files
del /q test_optimization.py 2>nul
del /q optimize_aura.py 2>nul

REM Remove duplicate tools in docker/searxng
del /q docker\searxng\tools.py 2>nul

REM Remove old documentation
del /q docs\README_old.md 2>nul

REM Remove script files (keep only essential ones)
del /q cleanup_for_git.bat 2>nul
del /q push_to_github.bat 2>nul
del /q docker_build.bat 2>nul
del /q docker\searxng\start_searxng.bat 2>nul
del /q docker\searxng\restart_searxng.bat 2>nul

REM Remove backup directory after confirming
echo.
echo Do you want to remove backup_before_cleanup? (y/n)
set /p remove_backup=
if /i "%remove_backup%"=="y" (
    rmdir /s /q backup_before_cleanup 2>nul
    echo Backup directory removed.
)

echo.
echo Deep clean complete!
echo.
echo Final project structure:
echo Core files: aura.py, aura_api.py, memory.py, rag.py, tools.py
echo Config: requirements.txt, .env, docker files
echo Data: data/, query_handlers/, prompts/, templates/
echo Docs: README.md, docs/
echo.
pause
