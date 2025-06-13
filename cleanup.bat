@echo off
echo ==========================================
echo     Aura AI Project Cleanup Tool
echo ==========================================
echo.

echo This script will delete the following temporary files:
echo - temp_to_delete/ directory and its contents
echo - Other temporary files
echo.

set /p confirm="Are you sure you want to delete these files? (y/N): "
if /i "%confirm%"=="y" (
    echo.
    echo Cleaning temporary files...
    
    if exist "temp_to_delete" (
        rmdir /s /q "temp_to_delete"
        echo OK: Deleted temp_to_delete/ directory
    ) else (
        echo INFO: temp_to_delete/ directory does not exist
    )
    
    echo OK: Cleanup completed!
    echo.
    echo Now you can safely perform git operations:
    echo   git add .
    echo   git commit -m "Fix think tag issue and config conflicts"
    echo   git push
) else (
    echo CANCELED: Operation cancelled
)

echo.
pause