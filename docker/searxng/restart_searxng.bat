@echo off
echo ====================================
echo   Restarting SearXNG for Aura
echo ====================================

echo Stopping SearXNG container...
docker stop searxng_aura

echo Removing SearXNG container...
docker rm searxng_aura

echo Starting SearXNG with new configuration...
docker-compose up -d

echo Waiting for SearXNG to initialize (10 seconds)...
timeout /t 10

echo Testing SearXNG search functionality...
python test_search.py

echo Done!
