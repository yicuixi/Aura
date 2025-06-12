#!/bin/bash

# Aura AI 项目设置脚本
# 自动检查环境、安装依赖、配置服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Aura AI 项目设置助手${NC}"
echo "============================================="

# 检查Python版本
echo -e "${YELLOW}🐍 检查Python环境...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version | cut -d " " -f 2)
    echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python未安装，请先安装Python 3.11+${NC}"
    exit 1
fi

# 检查pip
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip未安装，请先安装pip${NC}"
    exit 1
fi

# 创建虚拟环境选项
echo ""
read -p "是否创建Python虚拟环境？(推荐) (y/N): " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
    $PYTHON_CMD -m venv aura_env
    
    # 激活虚拟环境
    source aura_env/bin/activate
    echo -e "${GREEN}✅ 虚拟环境已创建并激活${NC}"
    echo -e "${BLUE}💡 下次使用前请运行: source aura_env/bin/activate${NC}"
fi

# 安装Python依赖
echo ""
echo -e "${YELLOW}📦 安装Python依赖...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✅ Python依赖安装完成${NC}"

# 检查Ollama
echo ""
echo -e "${YELLOW}🔍 检查Ollama服务...${NC}"
if curl -s http://localhost:11435/api/tags > /dev/null; then
    echo -e "${GREEN}✅ Ollama服务运行正常${NC}"
    
    # 检查模型
    if ollama list | grep -q "qwen2.5"; then
        echo -e "${GREEN}✅ Qwen2.5模型已安装${NC}"
    else
        echo -e "${YELLOW}📥 正在下载Qwen2.5模型...${NC}"
        ollama pull qwen2.5:7b
        echo -e "${GREEN}✅ 模型下载完成${NC}"
    fi
else
    echo -e "${RED}❌ Ollama服务未运行${NC}"
    echo -e "${YELLOW}请先安装并启动Ollama:${NC}"
    echo "   1. 访问 https://ollama.ai/ 下载安装"
    echo "   2. 运行: ollama serve"
    echo "   3. 下载模型: ollama pull qwen2.5:7b"
    
    read -p "是否现在安装Ollama？(需要管理员权限) (y/N): " install_ollama
    if [[ $install_ollama =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://ollama.ai/install.sh | sh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "请访问 https://ollama.ai/ 下载macOS版本"
        else
            echo "请访问 https://ollama.ai/ 下载对应版本"
        fi
    fi
fi

# 配置环境文件
echo ""
echo -e "${YELLOW}⚙️ 配置环境文件...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ 已创建.env配置文件${NC}"
else
    echo -e "${BLUE}💡 .env文件已存在${NC}"
fi

# 创建必要目录
echo ""
echo -e "${YELLOW}📁 创建必要目录...${NC}"
mkdir -p data db logs memory
echo -e "${GREEN}✅ 目录创建完成${NC}"

# Docker环境检查
echo ""
echo -e "${YELLOW}🐳 检查Docker环境...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker已安装${NC}"
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose已安装${NC}"
        echo -e "${BLUE}💡 可以使用Docker部署: ./start_aura.sh${NC}"
    else
        echo -e "${YELLOW}⚠️ Docker Compose未安装${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Docker未安装，将使用本地Python环境${NC}"
fi

# 完成设置
echo ""
echo -e "${GREEN}🎉 Aura AI 设置完成！${NC}"
echo ""
echo -e "${BLUE}🚀 启动方式：${NC}"
echo "1. 本地Python环境:"
echo "   python aura.py"
echo ""
echo "2. Web API模式:"
echo "   python aura_api.py"
echo ""
echo "3. Docker模式:"
echo "   ./start_aura.sh"
echo ""
echo -e "${BLUE}📖 更多信息请查看 README.md${NC}"

# 询问是否立即启动
echo ""
read -p "是否现在启动Aura？(y/N): " start_now
if [[ $start_now =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🚀 启动Aura AI...${NC}"
    $PYTHON_CMD aura.py
fi
