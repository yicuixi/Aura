#!/bin/bash

# Aura AI Quick Start Script
# Support command line mode and Web API mode

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Aura AI Docker Deployment Assistant${NC}"
echo "==============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not installed, please install Docker first${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose not installed, please install Docker Compose first${NC}"
    exit 1
fi

# Check Ollama service
echo -e "${YELLOW}Checking Ollama service...${NC}"
if curl -s http://localhost:11435/api/tags > /dev/null; then
    echo -e "${GREEN}OK: Ollama service is running${NC}"
else
    echo -e "${RED}ERROR: Ollama service not running, please start Ollama first:${NC}"
    echo "   ollama serve"
    echo "   ollama pull qwen3:4b"
    exit 1
fi

# Show deployment mode selection
echo ""
echo "Select deployment mode:"
echo "1) Command line mode (for local use, learning)"
echo "2) Web API mode (for integration, remote access)"
echo "3) View current container status"
echo "4) Stop all services"
echo "5) Clean and redeploy"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo -e "${BLUE}Starting command line mode...${NC}"
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml down 2>/dev/null || true
        docker-compose up -d --build
        
        echo -e "${GREEN}OK: Command line mode started successfully!${NC}"
        echo ""
        echo "Usage:"
        echo "   docker exec -it aura_ai python aura.py"
        echo ""
        echo "View logs:"
        echo "   docker-compose logs -f aura"
        ;;
        
    2)
        echo -e "${BLUE}Starting Web API mode...${NC}"
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml up -d --build
        
        echo -e "${YELLOW}Waiting for service to start...${NC}"
        sleep 10
        
        # Check API service health status
        max_attempts=30
        attempt=1
        while [ $attempt -le $max_attempts ]; do
            if curl -s http://localhost:5000/health > /dev/null; then
                echo -e "${GREEN}OK: Web API mode started successfully!${NC}"
                echo ""
                echo "API service addresses:"
                echo "   - Health check: http://localhost:5000/health"
                echo "   - Chat API: http://localhost:5000/v1/chat/completions"
                echo "   - Search service: http://localhost:8088"
                echo ""
                echo "Test API:"
                echo '   curl -X POST http://localhost:5000/v1/chat/completions \'
                echo '     -H "Content-Type: application/json" \'
                echo '     -d '"'"'{"messages": [{"role": "user", "content": "Hello"}]}'"'"
                break
            fi
            echo -e "${YELLOW}Waiting for API service to start... ($attempt/$max_attempts)${NC}"
            sleep 2
            ((attempt++))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            echo -e "${RED}ERROR: API service startup timeout, check logs:${NC}"
            echo "   docker-compose -f docker-compose-api.yml logs aura-api"
        fi
        ;;
        
    3)
        echo -e "${BLUE}Current container status:${NC}"
        echo ""
        echo "=== Command line mode ==="
        docker-compose ps 2>/dev/null || echo "Not running"
        echo ""
        echo "=== Web API mode ==="
        docker-compose -f docker-compose-api.yml ps 2>/dev/null || echo "Not running"
        ;;
        
    4)
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose-api.yml down 2>/dev/null || true
        echo -e "${GREEN}OK: All services stopped${NC}"
        ;;
        
    5)
        echo -e "${YELLOW}Clean and redeploy...${NC}"
        read -p "This will delete all containers and images, are you sure? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            docker-compose down -v 2>/dev/null || true
            docker-compose -f docker-compose-api.yml down -v 2>/dev/null || true
            docker system prune -f
            echo -e "${GREEN}OK: Cleanup completed, please select deployment mode again${NC}"
        else
            echo "CANCELED: Operation cancelled"
        fi
        ;;
        
    *)
        echo -e "${RED}ERROR: Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}Common commands:${NC}"
echo "  View logs: docker-compose logs -f [service_name]"
echo "  Restart service: docker-compose restart [service_name]"
echo "  Enter container: docker exec -it [container_name] bash"
echo "  Stop service: docker-compose down"
echo ""
echo -e "${GREEN}Deployment completed!${NC}"