@echo off
setlocal enabledelayedexpansion

REM Aura AI Windows 快速启动脚本
REM 支持命令行模式和Web API模式

echo ================================
echo 🚀 Aura AI Docker 部署助手
echo ================================

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 检查Ollama服务
echo 🔍 检查Ollama服务...
curl -s http://localhost:11435/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama服务未运行，请先启动Ollama:
    echo    ollama serve
    echo    ollama pull qwen2.5:7b
    pause
    exit /b 1
) else (
    echo ✅ Ollama服务运行正常
)

echo.
echo 📋 请选择部署模式:
echo 1^) 命令行模式 ^(适合本地使用、学习^)
echo 2^) Web API模式 ^(适合集成、远程访问^)
echo 3^) 查看现有容器状态
echo 4^) 停止所有服务
echo 5^) 清理和重新部署
echo.

set /p choice="请输入选择 (1-5): "

if "%choice%"=="1" (
    echo 🖥️ 启动命令行模式...
    docker-compose down >nul 2>&1
    docker-compose -f docker-compose-api.yml down >nul 2>&1
    docker-compose up -d --build
    
    echo ✅ 命令行模式启动成功！
    echo.
    echo 💡 使用方法:
    echo    docker exec -it aura_ai python aura.py
    echo.
    echo 🔧 查看日志:
    echo    docker-compose logs -f aura
    
) else if "%choice%"=="2" (
    echo 🌐 启动Web API模式...
    docker-compose down >nul 2>&1
    docker-compose -f docker-compose-api.yml down >nul 2>&1
    docker-compose -f docker-compose-api.yml up -d --build
    
    echo ⏳ 等待服务启动...
    timeout /t 10 /nobreak >nul
    
    REM 检查API服务健康状态
    set attempt=1
    set max_attempts=30
    
    :check_health
    curl -s http://localhost:5000/health >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Web API模式启动成功！
        echo.
        echo 🌐 API服务地址:
        echo    - 健康检查: http://localhost:5000/health
        echo    - 聊天API: http://localhost:5000/v1/chat/completions
        echo    - 搜索服务: http://localhost:8088
        echo.
        echo 💡 测试API:
        echo    curl -X POST http://localhost:5000/v1/chat/completions \
        echo      -H "Content-Type: application/json" \
        echo      -d "{\"messages\": [{\"role\": \"user\", \"content\": \"你好\"}]}"
        goto end
    )
    
    if !attempt! lss !max_attempts! (
        echo ⏳ 等待API服务启动... ^(!attempt!/!max_attempts!^)
        timeout /t 2 /nobreak >nul
        set /a attempt+=1
        goto check_health
    ) else (
        echo ❌ API服务启动超时，请检查日志:
        echo    docker-compose -f docker-compose-api.yml logs aura-api
    )
    
) else if "%choice%"=="3" (
    echo 📊 当前容器状态:
    echo.
    echo === 命令行模式 ===
    docker-compose ps 2>nul || echo 未运行
    echo.
    echo === Web API模式 ===
    docker-compose -f docker-compose-api.yml ps 2>nul || echo 未运行
    
) else if "%choice%"=="4" (
    echo 🛑 停止所有服务...
    docker-compose down >nul 2>&1
    docker-compose -f docker-compose-api.yml down >nul 2>&1
    echo ✅ 所有服务已停止
    
) else if "%choice%"=="5" (
    echo 🧹 清理和重新部署...
    set /p confirm="这将删除所有容器和镜像，确定继续? (y/N): "
    if /i "!confirm!"=="y" (
        docker-compose down -v >nul 2>&1
        docker-compose -f docker-compose-api.yml down -v >nul 2>&1
        docker system prune -f >nul 2>&1
        echo ✅ 清理完成，请重新选择部署模式
    ) else (
        echo ❌ 操作已取消
    )
    
) else (
    echo ❌ 无效选择
    goto end
)

:end
echo.
echo 🔧 常用命令:
echo   查看日志: docker-compose logs -f [服务名]
echo   重启服务: docker-compose restart [服务名]
echo   进入容器: docker exec -it [容器名] bash
echo   停止服务: docker-compose down
echo.
echo 🎉 部署完成！
pause
