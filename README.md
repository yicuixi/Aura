# Aura AI - Local AI Assistant

Aura is a local AI assistant built with Ollama and LangChain, featuring ReAct reasoning, RAG knowledge retrieval, and long-term memory capabilities.

## 🚀 Features

- **ReAct Reasoning Framework**: Think-Action-Observation pattern for complex problem solving
- **RAG Knowledge Retrieval**: Local knowledge base with vector storage
- **Long-term Memory**: Persistent memory for facts and conversations
- **Multi-tool Support**: Web search, file operations, knowledge base queries
- **Real-time Data**: Weather, stocks, news integration
- **Multiple Interfaces**: CLI, API, WebUI options

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Ollama installed and running (http://localhost:11435)
- Qwen3:4b model downloaded in Ollama

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Aura
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys (optional)
```

4. Initialize the system:
```bash
# Load knowledge base (optional)
python manage_knowledge.py

# Start Aura
python aura.py
```

## 🎯 Usage

### Command Line Interface
```bash
python aura.py
```

### API Server
```bash
python aura_api.py
```

### WebUI
```bash
python aura_webui.py
```

### Control Panel
```bash
# Windows
aura_control.bat
```

## 📁 Project Structure

```
Aura/
├── aura.py              # Main application
├── aura_v2.py           # Optimized version
├── simple_aura.py       # Lightweight version
├── memory.py            # Memory management
├── rag.py              # RAG system
├── tools.py            # Tool implementations
├── query_handlers/     # Specialized query processors
├── data/              # Knowledge base documents
├── prompts/           # System prompts
├── docker/            # Docker configurations
├── docs/              # Documentation
└── templates/         # HTML templates
```

## 🔧 Configuration

### Models
- Default: `qwen3:4b`
- Supports other Ollama models

### Tools Available
- Web Search (SearxNG, Serper)
- File Operations (read/write/list)
- Knowledge Base Search
- Memory Management
- Real-time Data Queries

## 📊 Query Types

Aura automatically routes queries to appropriate handlers:

- **Real-time queries**: Weather, stocks, news → Web search
- **Knowledge queries**: Technical topics → Knowledge base
- **Memory queries**: Personal info → Memory system
- **General queries**: → Full agent reasoning

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📜 License

This project is open source. Please respect privacy and security when using.

## 🚨 Privacy Note

This repository does not contain any personal information or sensitive data. All personal profiles and logs have been excluded for privacy protection.

## 📞 Support

For issues and questions, please create an issue in the repository.

---

Built with ❤️ using Ollama, LangChain, and Python
