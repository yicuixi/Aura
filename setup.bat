@echo off
setlocal enabledelayedexpansion

REM Aura AI 项目设置脚本 - Windows版本
REM 自动检查环境、安装依赖、配置服务

echo ========================================
echo 🚀 Aura AI 项目设置助手
echo ========================================

REM 检查Python
echo 🐍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.11+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo ✅ Python版本: !PYTHON_VERSION!
)

REM 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip未安装，请先安装pip
    pause
    exit /b 1
)

REM 创建虚拟环境选项
echo.
set /p create_venv="是否创建Python虚拟环境？(推荐) (y/N): "
if /i "!create_venv!"=="y" (
    echo 📦 创建虚拟环境...
    python -m venv aura_env
    
    REM 激活虚拟环境
    call aura_env\Scripts\activate.bat
    echo ✅ 虚拟环境已创建并激活
    echo 💡 下次使用前请运行: aura_env\Scripts\activate.bat
)

REM 安装Python依赖
echo.
echo 📦 安装Python依赖...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
) else (
    echo ✅ Python依赖安装完成
)

REM 检查Ollama
echo.
echo 🔍 检查Ollama服务...
curl -s http://localhost:11435/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama服务未运行
    echo 请先安装并启动Ollama:
    echo    1. 访问 https://ollama.ai/ 下载安装
    echo    2. 运行: ollama serve
    echo    3. 下载模型: ollama pull qwen2.5:7b
    
    set /p install_ollama="是否现在打开Ollama下载页面？ (y/N): "
    if /i "!install_ollama!"=="y" (
        start https://ollama.ai/
    )
) else (
    echo ✅ Ollama服务运行正常
    
    REM 检查模型
    ollama list | findstr "qwen2.5" >nul 2>&1
    if errorlevel 1 (
        echo 📥 正在下载Qwen2.5模型...
        ollama pull qwen2.5:7b
        echo ✅ 模型下载完成
    ) else (
        echo ✅ Qwen2.5模型已安装
    )
)

REM 配置环境文件
echo.
echo ⚙️ 配置环境文件...
if not exist .env (
    copy .env.example .env >nul
    echo ✅ 已创建.env配置文件
) else (
    echo 💡 .env文件已存在
)

REM 创建必要目录
echo.
echo 📁 创建必要目录...
if not exist data mkdir data
if not exist db mkdir db
if not exist logs mkdir logs
if not exist memory mkdir memory
echo ✅ 目录创建完成

REM Docker环境检查
echo.
echo 🐳 检查Docker环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Docker未安装，将使用本地Python环境
    echo 如需Docker支持，请安装Docker Desktop
) else (
    echo ✅ Docker已安装
    
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo ⚠️ Docker Compose未安装
    ) else (
        echo ✅ Docker Compose已安装
        echo 💡 可以使用Docker部署: start_aura.bat
    )
)

REM 完成设置
echo.
echo 🎉 Aura AI 设置完成！
echo.
echo 🚀 启动方式：
echo 1. 本地Python环境:
echo    python aura.py
echo.
echo 2. Web API模式:
echo    python aura_api.py
echo.
echo 3. Docker模式:
echo    start_aura.bat
echo.
echo 📖 更多信息请查看 README.md

REM 询问是否立即启动
echo.
set /p start_now="是否现在启动Aura？ (y/N): "
if /i "!start_now!"=="y" (
    echo 🚀 启动Aura AI...
    python aura.py
)

pause
