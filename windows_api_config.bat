@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title Aura AI - Windows网络API配置向导

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    🌟 Aura AI 网络API配置向导                    ║
echo ║                         Windows专用版本                         ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 检查是否存在.env文件
if not exist ".env" (
    echo ⚠️  未找到.env配置文件，正在从模板创建...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✅ 已创建.env配置文件
    ) else (
        echo ❌ 未找到.env.example模板文件
        echo    请确保在Aura项目根目录运行此脚本
        pause
        exit /b 1
    )
    echo.
)

:MAIN_MENU
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    🌟 Aura AI 网络API配置向导                    ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 📋 当前配置状态：
echo.

REM 检查各种API配置状态
call :CHECK_CONFIG "SEARXNG_URL" "🔒 SearxNG本地搜索"
call :CHECK_CONFIG "GOOGLE_API_KEY" "🌍 Google Custom Search"
call :CHECK_CONFIG "SERPER_API_KEY" "⚡ Serper API"
call :CHECK_CONFIG "SERPAPI_KEY" "🔥 SerpAPI"

echo.
echo 🛠️  配置选项：
echo    [1] 配置SearxNG本地搜索 (免费推荐)
echo    [2] 配置Google Custom Search API
echo    [3] 配置Serper API (高性价比)
echo    [4] 配置SerpAPI (功能最强)
echo    [5] 查看当前配置
echo    [6] 测试搜索功能
echo    [7] 安装SearxNG Docker版
echo    [8] 重置所有配置
echo    [0] 退出
echo.
set /p choice="请选择操作 [0-8]: "

if "%choice%"=="1" goto CONFIG_SEARXNG
if "%choice%"=="2" goto CONFIG_GOOGLE
if "%choice%"=="3" goto CONFIG_SERPER
if "%choice%"=="4" goto CONFIG_SERPAPI
if "%choice%"=="5" goto VIEW_CONFIG
if "%choice%"=="6" goto TEST_SEARCH
if "%choice%"=="7" goto INSTALL_SEARXNG
if "%choice%"=="8" goto RESET_CONFIG
if "%choice%"=="0" goto EXIT
goto MAIN_MENU

:CONFIG_SEARXNG
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                     🔒 配置SearxNG本地搜索                      ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo SearxNG是完全免费的开源搜索引擎，保护隐私且无API限制。
echo.
echo 请输入SearxNG服务URL（按回车使用默认值）：
set /p searxng_url="URL [http://localhost:8080]: "
if "%searxng_url%"=="" set searxng_url=http://localhost:8080

echo.
echo 请输入SearxNG密钥（按回车自动生成）：
set /p searxng_secret="密钥 [自动生成]: "
if "%searxng_secret%"=="" (
    REM 生成随机密钥
    powershell -Command "$key = -join ((1..32) | ForEach {'{0:X}' -f (Get-Random -Max 16)}); Write-Output $key" > temp_key.txt
    set /p searxng_secret=<temp_key.txt
    del temp_key.txt
)

REM 更新.env文件
call :UPDATE_ENV_VAR "SEARXNG_URL" "%searxng_url%"
call :UPDATE_ENV_VAR "SEARXNG_SECRET" "%searxng_secret%"

echo.
echo ✅ SearxNG配置已保存！
echo.
echo 📝 下一步：
echo    1. 如果SearxNG未运行，请选择选项[7]安装Docker版本
echo    2. 或手动启动SearxNG服务
echo    3. 使用选项[6]测试搜索功能
echo.
pause
goto MAIN_MENU

:CONFIG_GOOGLE
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                   🌍 配置Google Custom Search                  ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Google Custom Search提供每天100次免费搜索。
echo.
echo 📋 申请步骤：
echo    1. 访问 Google Cloud Console: https://console.cloud.google.com/
echo    2. 创建新项目或选择现有项目
echo    3. 启用 "Custom Search API"
echo    4. 创建API凭据（API密钥）
echo    5. 访问 https://cse.google.com/ 创建自定义搜索引擎
echo    6. 在搜索网站中输入 * （搜索整个网络）
echo    7. 获取搜索引擎ID
echo.
echo 🔑 请输入Google API密钥：
set /p google_api_key="API Key: "

echo.
echo 🆔 请输入Google搜索引擎ID：
set /p google_cse_id="CSE ID: "

if "%google_api_key%"=="" (
    echo ❌ API密钥不能为空
    pause
    goto CONFIG_GOOGLE
)

if "%google_cse_id%"=="" (
    echo ❌ 搜索引擎ID不能为空
    pause
    goto CONFIG_GOOGLE
)

REM 更新.env文件
call :UPDATE_ENV_VAR "GOOGLE_API_KEY" "%google_api_key%"
call :UPDATE_ENV_VAR "GOOGLE_CSE_ID" "%google_cse_id%"

echo.
echo ✅ Google Custom Search配置已保存！
echo.
echo 💰 使用限制：
echo    - 免费额度：100次搜索/天
echo    - 付费价格：$5/1000次搜索
echo.
pause
goto MAIN_MENU

:CONFIG_SERPER
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                      ⚡ 配置Serper API                         ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Serper API提供高质量搜索结果，性价比高。
echo.
echo 📋 申请步骤：
echo    1. 访问 https://serper.dev/
echo    2. 点击 "Get API Key"
echo    3. 使用Google或GitHub账户注册
echo    4. 验证邮箱后即可获得API密钥
echo    5. 免费获得2500次搜索额度
echo.
echo 🔑 请输入Serper API密钥：
set /p serper_api_key="API Key: "

if "%serper_api_key%"=="" (
    echo ❌ API密钥不能为空
    pause
    goto CONFIG_SERPER
)

REM 更新.env文件
call :UPDATE_ENV_VAR "SERPER_API_KEY" "%serper_api_key%"

echo.
echo ✅ Serper API配置已保存！
echo.
echo 💰 价格信息：
echo    - 免费额度：2500次搜索
echo    - 付费价格：$50/10000次搜索
echo    - 特色：无月费，按使用计费
echo.
pause
goto MAIN_MENU

:CONFIG_SERPAPI
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                       🔥 配置SerpAPI                           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo SerpAPI提供最全面的搜索功能和数据提取能力。
echo.
echo 📋 申请步骤：
echo    1. 访问 https://serpapi.com/
echo    2. 点击 "Sign Up" 注册账户
echo    3. 填写基本信息并验证邮箱
echo    4. 登录后在控制台复制API密钥
echo    5. 免费获得100次搜索/月
echo.
echo 🔑 请输入SerpAPI密钥：
set /p serpapi_key="API Key: "

if "%serpapi_key%"=="" (
    echo ❌ API密钥不能为空
    pause
    goto CONFIG_SERPAPI
)

REM 更新.env文件
call :UPDATE_ENV_VAR "SERPAPI_KEY" "%serpapi_key%"

echo.
echo ✅ SerpAPI配置已保存！
echo.
echo 💰 价格信息：
echo    - 免费额度：100次搜索/月
echo    - 开发者套餐：$50/月（5000次搜索）
echo    - 生产套餐：$150/月（15000次搜索）
echo.
pause
goto MAIN_MENU

:VIEW_CONFIG
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                       📋 当前配置详情                           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

if exist ".env" (
    echo 📄 .env配置文件内容：
    echo ────────────────────────────────────────────────────────────────
    type .env | findstr /v "^#" | findstr /v "^$"
    echo ────────────────────────────────────────────────────────────────
) else (
    echo ❌ 未找到.env配置文件
)

echo.
echo 🔧 系统环境变量：
for %%i in (SEARXNG_URL GOOGLE_API_KEY GOOGLE_CSE_ID SERPER_API_KEY SERPAPI_KEY) do (
    if defined %%i (
        echo    %%i = !%%i!
    )
)

echo.
pause
goto MAIN_MENU

:TEST_SEARCH
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                       🔍 测试搜索功能                           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 测试SearxNG
echo 🔒 测试SearxNG连接...
call :GET_ENV_VAR "SEARXNG_URL" searxng_url
if not "%searxng_url%"=="" (
    curl -s -m 5 "%searxng_url%/search?q=test&format=json" >nul 2>&1
    if !errorlevel! equ 0 (
        echo    ✅ SearxNG连接成功
    ) else (
        echo    ❌ SearxNG连接失败
    )
) else (
    echo    ⚠️  SearxNG未配置
)

REM 测试Google API
echo 🌍 测试Google Custom Search...
call :GET_ENV_VAR "GOOGLE_API_KEY" google_key
call :GET_ENV_VAR "GOOGLE_CSE_ID" google_cse
if not "%google_key%"=="" if not "%google_cse%"=="" (
    curl -s -m 5 "https://www.googleapis.com/customsearch/v1?key=%google_key%&cx=%google_cse%&q=test" >nul 2>&1
    if !errorlevel! equ 0 (
        echo    ✅ Google API连接成功
    ) else (
        echo    ❌ Google API连接失败
    )
) else (
    echo    ⚠️  Google API未配置
)

REM 测试Serper API
echo ⚡ 测试Serper API...
call :GET_ENV_VAR "SERPER_API_KEY" serper_key
if not "%serper_key%"=="" (
    curl -s -m 5 -H "X-API-KEY: %serper_key%" "https://google.serper.dev/search" -d "{\"q\":\"test\"}" >nul 2>&1
    if !errorlevel! equ 0 (
        echo    ✅ Serper API连接成功
    ) else (
        echo    ❌ Serper API连接失败
    )
) else (
    echo    ⚠️  Serper API未配置
)

REM 测试SerpAPI
echo 🔥 测试SerpAPI...
call :GET_ENV_VAR "SERPAPI_KEY" serpapi_key
if not "%serpapi_key%"=="" (
    curl -s -m 5 "https://serpapi.com/search.json?api_key=%serpapi_key%&q=test" >nul 2>&1
    if !errorlevel! equ 0 (
        echo    ✅ SerpAPI连接成功
    ) else (
        echo    ❌ SerpAPI连接失败
    )
) else (
    echo    ⚠️  SerpAPI未配置
)

echo.
echo 📊 测试完成！建议配置至少2个搜索服务以确保稳定性。
echo.
pause
goto MAIN_MENU

:INSTALL_SEARXNG
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    🐳 安装SearxNG Docker版                     ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ 未检测到Docker Desktop
    echo.
    echo 📥 请先安装Docker Desktop for Windows：
    echo    1. 访问 https://www.docker.com/products/docker-desktop
    echo    2. 下载并安装Docker Desktop
    echo    3. 启动Docker Desktop
    echo    4. 重新运行此脚本
    echo.
    pause
    goto MAIN_MENU
)

echo ✅ 检测到Docker环境
echo.
echo 📦 正在创建SearxNG配置...

REM 创建searxng目录
if not exist "docker\searxng" mkdir "docker\searxng"
cd docker\searxng

REM 创建docker-compose.yml
echo version: '3.7'> docker-compose.yml
echo.>> docker-compose.yml
echo services:>> docker-compose.yml
echo   searxng:>> docker-compose.yml
echo     container_name: searxng>> docker-compose.yml
echo     image: searxng/searxng:latest>> docker-compose.yml
echo     restart: unless-stopped>> docker-compose.yml
echo     ports:>> docker-compose.yml
echo       - "8080:8080">> docker-compose.yml
echo     volumes:>> docker-compose.yml
echo       - ./settings:/etc/searxng:rw>> docker-compose.yml
echo     environment:>> docker-compose.yml
echo       - SEARXNG_BASE_URL=http://localhost:8080/>> docker-compose.yml

REM 创建设置目录
if not exist "settings" mkdir "settings"

REM 生成settings.yml
powershell -Command "$secret = -join ((1..32) | ForEach {'{0:X}' -f (Get-Random -Max 16)}); $yml = @'
use_default_settings: true
server:
  port: 8080
  bind_address: \"0.0.0.0\"
  secret_key: \"$secret\"
search:
  safe_search: 0
  autocomplete: \"\"
  default_lang: \"\"
engines:
  - name: bing
    disabled: false
  - name: google
    disabled: false
  - name: duckduckgo
    disabled: false
'@; $yml | Out-File -FilePath 'settings\settings.yml' -Encoding UTF8"

echo.
echo 🚀 启动SearxNG容器...
docker-compose up -d

if !errorlevel! equ 0 (
    echo ✅ SearxNG已成功启动！
    echo.
    echo 🌐 访问地址：http://localhost:8080
    echo 🔧 配置文件：docker\searxng\settings\settings.yml
    echo.
    echo 等待5秒钟让服务完全启动...
    timeout /t 5 /nobreak >nul
    
    REM 测试连接
    curl -s -m 10 "http://localhost:8080" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ SearxNG服务正常运行
        
        REM 自动配置Aura
        cd ..\..
        call :UPDATE_ENV_VAR "SEARXNG_URL" "http://localhost:8080"
        echo ✅ 已自动配置Aura使用SearxNG
    ) else (
        echo ⚠️  SearxNG可能需要更多时间启动，请稍后测试
    )
) else (
    echo ❌ SearxNG启动失败，请检查Docker状态
    cd ..\..
)

echo.
pause
goto MAIN_MENU

:RESET_CONFIG
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                       🔄 重置所有配置                           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo ⚠️  这将删除所有已配置的API密钥和设置
echo.
set /p confirm="确定要重置配置吗？(y/N): "
if /i not "%confirm%"=="y" goto MAIN_MENU

if exist ".env" (
    copy ".env.example" ".env" >nul
    echo ✅ 配置已重置为默认值
) else (
    echo ❌ 未找到.env文件
)

echo.
pause
goto MAIN_MENU

:EXIT
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                         👋 配置完成                            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 🎉 网络API配置向导已完成！
echo.
echo 📝 下一步：
echo    1. 运行 start_aura.bat 启动Aura
echo    2. 使用 python aura.py 进入命令行模式
echo    3. 使用 python aura_api.py 启动Web API服务
echo.
echo 📚 更多帮助：
echo    - 查看 README.md 获取详细文档
echo    - 查看 QUICKSTART.md 快速开始指南
echo.
echo 感谢使用Aura AI！ 🌟
echo.
pause
exit /b 0

REM ============================================================================
REM 辅助函数
REM ============================================================================

:CHECK_CONFIG
set config_name=%~1
set display_name=%~2
call :GET_ENV_VAR "%config_name%" config_value
if not "%config_value%"=="" (
    echo    %display_name% ✅ 已配置
) else (
    echo    %display_name% ❌ 未配置
)
goto :eof

:GET_ENV_VAR
set var_name=%~1
set result_var=%~2
for /f "tokens=2 delims==" %%a in ('findstr /i "^%var_name%=" .env 2^>nul') do (
    set %result_var%=%%a
)
goto :eof

:UPDATE_ENV_VAR
set var_name=%~1
set var_value=%~2

REM 创建临时文件
echo. > .env.tmp

REM 处理每一行
for /f "delims=" %%a in (.env) do (
    set line=%%a
    if "!line:~0,%var_name_len%!"=="%var_name%=" (
        echo %var_name%=%var_value%>> .env.tmp
    ) else (
        echo %%a>> .env.tmp
    )
)

REM 检查变量是否存在，如果不存在则添加
findstr /i "^%var_name%=" .env >nul 2>&1
if !errorlevel! neq 0 (
    echo %var_name%=%var_value%>> .env.tmp
)

REM 替换原文件
move .env.tmp .env >nul
goto :eof
