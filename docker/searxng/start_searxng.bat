@echo off
REM SearXNG Startup Script

echo Starting SearXNG search engine...
echo.

REM Make sure to run in the correct directory
cd /d D:\Code\Aura\docker\searxng

REM Start SearXNG container
docker-compose up -d

echo.
echo SearXNG started at: http://localhost:8088
echo Please wait 30 seconds for service to fully start...
echo After startup, Aura will be able to use web search function
echo.
echo Press any key to continue...
pause > nul
