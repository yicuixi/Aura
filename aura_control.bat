@echo off
REM Aura Master Control Program - 合并版本
REM 此脚本整合了多个控制脚本的功能

:MENU
cls
echo ========================================
echo      Aura AI - 控制面板
echo ========================================
echo.
echo 当前目录: %CD%
echo.
echo [1] 启动Aura (标准模式)
echo [2] 启动Aura API (用于OpenWebUI)
echo [3] 启动完整Docker环境
echo [4] 切换WebUI版本
echo [5] 管理知识库
echo [6] 清理临时文件
echo [7] 磁盘空间分析
echo [8] 退出
echo.
set /p choice=选择选项 (1-8): 

if "%choice%"=="1" goto START_AURA
if "%choice%"=="2" goto START_API
if "%choice%"=="3" goto START_DOCKER
if "%choice%"=="4" goto SWITCH_WEBUI
if "%choice%"=="5" goto KNOWLEDGE
if "%choice%"=="6" goto CLEANUP
if "%choice%"=="7" goto DISK_SPACE
if "%choice%"=="8" goto END
goto MENU

:START_AURA
cls
echo ======================================
echo         启动Aura AI系统
echo ======================================
echo.
echo 正在激活conda环境...
echo.

call D:\Program\Anaconda\Scripts\activate.bat llm
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 错误: 无法激活conda环境。
    echo 请检查您的Anaconda安装。
    pause
    goto MENU
)

echo.
echo 环境已激活。启动Aura...
python aura.py
pause
goto MENU

:START_API
cls
echo ======================================
echo      启动Aura API (用于OpenWebUI)
echo ======================================
echo.

if not exist "aura_api.py" (
    echo 创建API脚本...
    echo import time > aura_api.py
    echo from flask import Flask, request, jsonify >> aura_api.py
    echo from aura import AuraAgent >> aura_api.py
    echo. >> aura_api.py
    echo app = Flask(__name__) >> aura_api.py
    echo aura = AuraAgent(model_name="qwen3:4b", verbose=False) >> aura_api.py
    echo. >> aura_api.py
    echo @app.route('/v1/chat/completions', methods=['POST']) >> aura_api.py
    echo def chat_completions(): >> aura_api.py
    echo     try: >> aura_api.py
    echo         data = request.json >> aura_api.py
    echo         messages = data.get('messages', []) >> aura_api.py
    echo         user_message = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), "") >> aura_api.py
    echo         response = aura.process_query(user_message) >> aura_api.py
    echo         return jsonify({ >> aura_api.py
    echo             "id": "aura-response", >> aura_api.py
    echo             "object": "chat.completion", >> aura_api.py
    echo             "created": int(time.time()), >> aura_api.py
    echo             "model": "aura", >> aura_api.py
    echo             "choices": [ >> aura_api.py
    echo                 { >> aura_api.py
    echo                     "index": 0, >> aura_api.py
    echo                     "message": { >> aura_api.py
    echo                         "role": "assistant", >> aura_api.py
    echo                         "content": response >> aura_api.py
    echo                     }, >> aura_api.py
    echo                     "finish_reason": "stop" >> aura_api.py
    echo                 } >> aura_api.py
    echo             ] >> aura_api.py
    echo         }) >> aura_api.py
    echo     except Exception as e: >> aura_api.py
    echo         return jsonify({"error": str(e)}), 500 >> aura_api.py
    echo. >> aura_api.py
    echo if __name__ == '__main__': >> aura_api.py
    echo     print("Starting Aura API on port 5000...") >> aura_api.py
    echo     app.run(host='0.0.0.0', port=5000) >> aura_api.py
)

echo.
echo 在llm环境中启动API...
echo.
echo 在OpenWebUI中使用此URL: http://localhost:5000
echo.
call D:\Program\Anaconda\Scripts\activate.bat llm
python aura_api.py
goto MENU

:START_DOCKER
cls
echo ======================================
echo         启动Aura Docker环境
echo ======================================
echo.

REM 检查Docker是否运行
echo 检查Docker服务...
docker info > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [错误] Docker未运行，请先启动Docker。
  pause
  goto MENU
)
echo [成功] Docker正在运行

echo 选择Docker环境配置:
echo [1] 标准配置
echo [2] 轻量级配置
echo [3] 备用配置
echo [4] 返回主菜单
echo.
set /p docker_choice=选择配置: 

if "%docker_choice%"=="1" (
    echo 启动标准Docker配置...
    docker-compose up -d
)
if "%docker_choice%"=="2" (
    echo 启动轻量级Docker配置...
    if not exist "D:\Docker\ollama" mkdir "D:\Docker\ollama"
    if not exist "D:\Docker\qdrant" mkdir "D:\Docker\qdrant"
    docker-compose -f docker-compose-lightweight.yml up -d
)
if "%docker_choice%"=="3" (
    echo 启动备用Docker配置...
    docker-compose -f docker-compose-alt.yml up -d
)
if "%docker_choice%"=="4" goto MENU

echo.
echo 等待服务启动 (10秒)...
timeout /t 10 /nobreak > nul

echo.
echo 检查服务状态...
docker ps

echo.
echo ======================================
echo    Aura Docker环境已启动!
echo ======================================
echo.
echo 请访问 http://localhost:3000 使用WebUI
echo.
echo 按任意键打开浏览器...
pause > nul
start http://localhost:3000
goto MENU

:SWITCH_WEBUI
cls
echo ======================================
echo           切换WebUI版本
echo ======================================
echo.
echo [1] 重启OpenWebUI
echo [2] 切换到轻量级WebUI
echo [3] 切换到备用WebUI
echo [4] 返回主菜单
echo.
set /p webui_choice=选择选项: 

if "%webui_choice%"=="1" (
    echo 重启OpenWebUI...
    docker stop open-webui
    docker rm open-webui
    docker-compose up -d openwebui
    docker system prune -f
)
if "%webui_choice%"=="2" (
    echo 切换到轻量级WebUI...
    docker-compose down
    if not exist "D:\Docker\ollama" mkdir "D:\Docker\ollama"
    if not exist "D:\Docker\qdrant" mkdir "D:\Docker\qdrant"
    docker-compose -f docker-compose-lightweight.yml up -d
)
if "%webui_choice%"=="3" (
    echo 切换到备用WebUI...
    docker-compose down
    docker-compose -f docker-compose-alt.yml up -d
)
if "%webui_choice%"=="4" goto MENU

echo.
echo 等待服务启动 (10秒)...
timeout /t 10 /nobreak > nul

echo.
echo ======================================
echo    WebUI已切换!
echo ======================================
echo.
echo 请访问 http://localhost:3000 使用WebUI
echo (如果使用备用WebUI，请访问 http://localhost:3001)
echo.
echo 按任意键打开浏览器...
pause > nul
start http://localhost:3000
goto MENU

:KNOWLEDGE
cls
echo ========================================
echo           知识库管理器
echo ========================================
echo.
echo [1] 将文档加载到知识库
echo [2] 重置知识库
echo [3] 返回主菜单
echo.
set /p kb_choice=选择选项 (1-3): 

if "%kb_choice%"=="1" goto LOAD_DOCS
if "%kb_choice%"=="2" goto RESET_KB
if "%kb_choice%"=="3" goto MENU
goto KNOWLEDGE

:LOAD_DOCS
cls
echo ========================================
echo         将文档加载到知识库
echo ========================================
echo.
echo 可用的文档格式:
echo - Markdown (.md)
echo - PDF (.pdf)
echo - Text (.txt)
echo - CSV (.csv)
echo.
set /p format=输入文档格式 (.md, .pdf, .txt, .csv): 

echo.
echo 这将从data目录加载%format%文件。
set /p confirm=继续? (Y/N): 
if /i not "%confirm%"=="Y" goto KNOWLEDGE

call D:\Program\Anaconda\Scripts\activate.bat llm
python -c "from aura import AuraAgent; agent = AuraAgent(); agent.load_knowledge('%format%')"
echo.
pause
goto KNOWLEDGE

:RESET_KB
cls
echo ========================================
echo            重置知识库
echo ========================================
echo.
echo 警告: 这将重置整个知识库。
echo 删除前将创建备份。
echo.
set /p confirm=确定要继续吗? (Y/N): 
if /i not "%confirm%"=="Y" goto KNOWLEDGE

call D:\Program\Anaconda\Scripts\activate.bat llm
python -c "from aura import AuraAgent; agent = AuraAgent(); agent.reset_knowledge_base()"
echo.
pause
goto KNOWLEDGE

:CLEANUP
cls
echo ========================================
echo         清理临时文件
echo ========================================
echo.
echo 将删除的文件:
echo - 临时Python脚本 (*_fixed.py, *_proxy.py)
echo - 临时批处理文件 (保留aura_control.bat)
echo - Python缓存文件
echo.
set /p confirm=继续清理? (Y/N): 
if /i not "%confirm%"=="Y" goto MENU

echo.
echo 删除临时Python脚本...
del *_fixed.py *_proxy.py improved_proxy.py simple_proxy.py 2>nul

echo 删除Python缓存...
if exist __pycache__ rmdir /s /q __pycache__ 2>nul

echo.
echo 清理完成!
pause
goto MENU

:DISK_SPACE
cls
echo ========================================
echo           磁盘空间分析
echo ========================================
echo.
echo 当前磁盘空间:
wmic logicaldisk get deviceid, size, freespace, description

echo.
echo 常见的空间使用问题:
echo 1. Anaconda缓存 (conda clean -y --all)
echo 2. Windows临时文件
echo 3. Docker镜像和容器
echo 4. 下载文件夹
echo.

REM 检查Anaconda缓存大小
echo 检查Anaconda缓存大小...
call conda clean -y --dry-run

echo.
echo 选项:
echo [1] 清理Anaconda缓存
echo [2] 清理Windows临时文件
echo [3] 清理Docker系统
echo [4] 返回主菜单
echo.
set /p disk_choice=选择选项 (1-4): 

if "%disk_choice%"=="1" (
    echo.
    echo 清理Anaconda缓存...
    call conda clean -y --all
    echo 完成!
    pause
)

if "%disk_choice%"=="2" (
    echo.
    echo 清理Windows临时文件...
    echo 删除%TEMP%文件...
    del /q/f/s %TEMP%\*
    echo 完成!
    pause
)

if "%disk_choice%"=="3" (
    echo.
    echo 清理Docker系统...
    docker system prune -f
    echo 完成!
    pause
)

goto MENU

:END
cls
echo ========================================
echo      感谢使用Aura AI系统
echo ========================================
echo.
exit /b
