#!/bin/bash

# Aura AI 快速启动脚本
# 支持命令行模式和Web API模式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Aura AI Docker 部署助手${NC}"
echo "==============================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装，请先安装Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 检查Ollama服务
echo -e "${YELLOW}🔍 检查Ollama服务...${NC}"
if curl -s http://localhost:11435/api/tags > /dev/null; then
    echo -e "${GREEN}✅ Ollama服务运行正常${NC}"
else
    echo -e "${RED}❌ Ollama服务未运行，请先启动Ollama:${NC}"
    echo "   ollama serve"
    echo "   ollama pull qwen2.5:7b"
    exit 1
fi

# 显示部署模式选择
echo ""
echo "📋 请选择部署模式:"
echo "1) 命令行模式 (适合本地使用、学习)"
echo "2) Web API模式 (适合集成、远程访问)"
echo "3) 查看现有容器状态"
echo "4) 停止所有服务"
echo "5) 清理和重新部署"

read -p "请输入选择 (1-5): " choice

case $choice in
    1)
        echo -e "${BLUE}🖥️ 启动命令行模式...${NC}"
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml down 2>/dev/null || true
        docker-compose up -d --build
        
        echo -e "${GREEN}✅ 命令行模式启动成功！${NC}"
        echo ""
        echo "💡 使用方法:"
        echo "   docker exec -it aura_ai python aura.py"
        echo ""
        echo "🔧 查看日志:"
        echo "   docker-compose logs -f aura"
        ;;
        
    2)
        echo -e "${BLUE}🌐 启动Web API模式...${NC}"
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml up -d --build
        
        echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
        sleep 10
        
        # 检查API服务健康状态
        max_attempts=30
        attempt=1
        while [ $attempt -le $max_attempts ]; do
            if curl -s http://localhost:5000/health > /dev/null; then
                echo -e "${GREEN}✅ Web API模式启动成功！${NC}"
                echo ""
                echo "🌐 API服务地址:"
                echo "   - 健康检查: http://localhost:5000/health"
                echo "   - 聊天API: http://localhost:5000/v1/chat/completions"
                echo "   - 搜索服务: http://localhost:8088"
                echo ""
                echo "💡 测试API:"
                echo '   curl -X POST http://localhost:5000/v1/chat/completions \'
                echo '     -H "Content-Type: application/json" \'
                echo '     -d '"'"'{"messages": [{"role": "user", "content": "你好"}]}'"'"
                break
            fi
            echo -e "${YELLOW}⏳ 等待API服务启动... ($attempt/$max_attempts)${NC}"
            sleep 2
            ((attempt++))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            echo -e "${RED}❌ API服务启动超时，请检查日志:${NC}"
            echo "   docker-compose -f docker-compose-api.yml logs aura-api"
        fi
        ;;
        
    3)
        echo -e "${BLUE}📊 当前容器状态:${NC}"
        echo ""
        echo "=== 命令行模式 ==="
        docker-compose ps 2>/dev/null || echo "未运行"
        echo ""
        echo "=== Web API模式 ==="
        docker-compose -f docker-compose-api.yml ps 2>/dev/null || echo "未运行"
        ;;
        
    4)
        echo -e "${YELLOW}🛑 停止所有服务...${NC}"
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml down 2>/dev/null || true
        echo -e "${GREEN}✅ 所有服务已停止${NC}"
        ;;
        
    5)
        echo -e "${YELLOW}🧹 清理和重新部署...${NC}"
        read -p "这将删除所有容器和镜像，确定继续? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            docker-compose down -v 2>/dev/null || true
            docker-compose -f docker-compose-api.yml down -v 2>/dev/null || true
            docker system prune -f
            echo -e "${GREEN}✅ 清理完成，请重新选择部署模式${NC}"
        else
            echo "❌ 操作已取消"
        fi
        ;;
        
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}🔧 常用命令:${NC}"
echo "  查看日志: docker-compose logs -f [服务名]"
echo "  重启服务: docker-compose restart [服务名]"
echo "  进入容器: docker exec -it [容器名] bash"
echo "  停止服务: docker-compose down"
echo ""
echo -e "${GREEN}🎉 部署完成！${NC}"
