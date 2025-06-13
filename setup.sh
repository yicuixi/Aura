#!/bin/bash

# Aura AI Project Setup Script
# Auto check environment, install dependencies, configure services

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Aura AI Project Setup Assistant${NC}"
echo "============================================="

# Check Python version
echo -e "${YELLOW}Checking Python environment...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    echo -e "${GREEN}OK: Python version: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version | cut -d " " -f 2)
    echo -e "${GREEN}OK: Python version: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}ERROR: Python not installed, please install Python 3.11+${NC}"
    exit 1
fi

# Check pip
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo -e "${RED}ERROR: pip not installed, please install pip first${NC}"
    exit 1
fi

# Create virtual environment option
echo ""
read -p "Create Python virtual environment? (recommended) (y/N): " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv aura_env
    
    # Activate virtual environment
    source aura_env/bin/activate
    echo -e "${GREEN}OK: Virtual environment created and activated${NC}"
    echo -e "${BLUE}TIP: Next time run: source aura_env/bin/activate${NC}"
fi

# Install Python dependencies
echo ""
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}OK: Python dependencies installed${NC}"

# Check Ollama
echo ""
echo -e "${YELLOW}Checking Ollama service...${NC}"
if curl -s http://localhost:11435/api/tags > /dev/null; then
    echo -e "${GREEN}OK: Ollama service is running${NC}"
    
    # Check model
    if ollama list | grep -q "qwen3"; then
        echo -e "${GREEN}OK: qwen3:4b model installed${NC}"
    else
        echo -e "${YELLOW}Downloading qwen3:4b model...${NC}"
        ollama pull qwen3:4b
        echo -e "${GREEN}OK: Model download completed${NC}"
    fi
else
    echo -e "${RED}ERROR: Ollama service not running${NC}"
    echo -e "${YELLOW}Please install and start Ollama first:${NC}"
    echo "   1. Visit https://ollama.ai/ to download and install"
    echo "   2. Run: ollama serve"
    echo "   3. Download model: ollama pull qwen3:4b"
    
    read -p "Install Ollama now? (requires admin privileges) (y/N): " install_ollama
    if [[ $install_ollama =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://ollama.ai/install.sh | sh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Please visit https://ollama.ai/ to download macOS version"
        else
            echo "Please visit https://ollama.ai/ to download appropriate version"
        fi
    fi
fi

# Configure environment file
echo ""
echo -e "${YELLOW}Configuring environment file...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}OK: Created .env configuration file${NC}"
else
    echo -e "${BLUE}INFO: .env file already exists${NC}"
fi

# Create necessary directories
echo ""
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p data db logs memory
echo -e "${GREEN}OK: Directories created${NC}"

# Docker environment check
echo ""
echo -e "${YELLOW}Checking Docker environment...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}OK: Docker installed${NC}"
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}OK: Docker Compose installed${NC}"
        echo -e "${BLUE}TIP: Can use Docker deployment: ./start_aura.sh${NC}"
    else
        echo -e "${YELLOW}WARNING: Docker Compose not installed${NC}"
    fi
else
    echo -e "${YELLOW}WARNING: Docker not installed, will use local Python environment${NC}"
fi

# Setup complete
echo ""
echo -e "${GREEN}Aura AI Setup Complete!${NC}"
echo ""
echo -e "${BLUE}Startup Options:${NC}"
echo "1. Local Python environment:"
echo "   python aura.py"
echo ""
echo "2. Web API mode:"
echo "   python aura_api.py"
echo ""
echo "3. Docker mode:"
echo "   ./start_aura.sh"
echo ""
echo -e "${BLUE}For more information, see README.md${NC}"

# Ask if start now
echo ""
read -p "Start Aura now? (y/N): " start_now
if [[ $start_now =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Starting Aura AI...${NC}"
    $PYTHON_CMD aura.py
fi