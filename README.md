# Aura AI宝宝 🤖✨

> 一个拥有"灵魂"的个人AI助手，基于Ollama、LangChain和Qwen3模型构建的本地化AI Agent系统

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-latest-green.svg)
![Ollama](https://img.shields.io/badge/Ollama-Qwen3-orange.svg)

## 🎯 核心特性

- 🧠 **智能对话**: 基于Qwen3:4b模型的自然语言交互
- 🔍 **知识检索**: RAG系统，可加载本地文档进行问答
- 💾 **长期记忆**: 记住用户偏好和对话历史
- 🛠️ **工具调用**: 支持文件操作、网络搜索等功能
- 🌐 **多种接口**: CLI命令行 + Web API两种使用方式
- 🏠 **完全本地**: 基于Ollama部署，保护隐私安全

## 🚀 快速开始

### 环境要求
- **Windows 10/11** (主要支持)
- **Python 3.8+**
- **8GB+ 内存** (推荐16GB)

### 1. 安装Ollama
```bash
# 下载并安装Ollama
# 访问 https://ollama.ai 下载Windows版本

# 启动Ollama服务
ollama serve

# 下载Qwen3模型
ollama pull qwen3:4b
```

### 2. 安装项目依赖
```bash
# 克隆项目
git clone https://github.com/yourusername/aura-ai.git
cd aura-ai

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 启动Aura
```bash
# CLI模式 - 命令行交互
python aura_react.py

# API模式 - Web服务接口
uvicorn api:app --host 0.0.0.0 --port 5000
```

## 📁 项目结构

```
Aura/
├── aura_react.py              # ReAct Agent 主入口
├── api.py                     # FastAPI Web API
├── rag.py                     # RAG知识检索系统
├── memory.py                  # 记忆管理系统
├── tools.py                   # 工具集成模块
├── mcp_server.py              # MCP知识库服务
├── requirements.txt           # Python依赖
├── job_hunter/                # 自动求职模块
├── evaluation/                # 评估框架
├── data/                      # 知识库数据目录
├── docker/                    # Docker配置
└── reports/                   # 评估报告
```

## 🔧 使用方法

### CLI模式 (命令行交互)
```bash
python aura_react.py
```

**功能特色:**
- 💬 直接对话交互
- 📚 加载知识库: 输入 `加载知识`
- 🧠 记忆功能: 记住用户偏好
- 🔍 智能搜索: 自动判断是否需要联网搜索

### API模式 (Web服务)
```bash
uvicorn api:app --host 0.0.0.0 --port 5000
```

**API端点:**
- `GET /health` - 健康检查
- `POST /chat` - 聊天接口
- `POST /knowledge/add` - 添加知识
- `GET /knowledge/search` - 知识检索

**测试API:**
```bash
# 健康检查
curl http://localhost:5000/health

# 聊天测试
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}]}'
```

## 🌐 网络搜索配置

Aura支持多种搜索服务：

### 1. SearxNG (需要自部署)
SearxNG是开源搜索引擎，需要自己部署实例：

```bash
# 自己部署(推荐)
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker
docker-compose up -d

# 配置API访问
SEARXNG_URL=http://localhost:8080
```

### 2. Google Custom Search
```bash
# 申请地址: https://console.cloud.google.com/
# 1. 创建项目并启用Custom Search API
# 2. 创建API密钥
# 3. 在 https://cse.google.com/ 创建搜索引擎

GOOGLE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_search_engine_id
```

### 3. Serper API (高性价比)
```bash
# 申请地址: https://serper.dev/
# 免费额度: 2500次搜索

SERPER_API_KEY=your_serper_key_here
```

### 4. Windows配置向导
```bash
# Windows用户可直接运行
windows_api_config.bat
```

## 📝 添加知识库

### 支持的文件格式
- `.md` - Markdown文件
- `.txt` - 纯文本文件
- `.pdf` - PDF文档
- `.csv` - CSV数据文件

### 添加步骤
1. 将文档放入 `data/` 目录
2. 启动Aura CLI模式
3. 输入 `加载知识` 命令
4. 选择文件格式（默认.md）

## 🐳 Docker部署

### 快速启动
```bash
# Linux/macOS用户
./start_aura.sh

# 选择模式:
# 1) 命令行模式
# 2) Web API模式
```

### 手动Docker操作
```bash
# 启动服务
docker-compose up -d

# 进入容器使用CLI
docker exec -it aura_ai python aura_react.py

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## ⚙️ 配置文件

### 环境变量 (.env)
```bash
# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen3:4b

# 搜索配置 (选择一种即可)
SEARXNG_URL=http://localhost:8080
GOOGLE_API_KEY=your_key
GOOGLE_CSE_ID=your_id
SERPER_API_KEY=your_key

# API服务配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

## 🔍 常见问题

### Q1: Ollama连接失败
```bash
# 检查Ollama服务
ollama list

# 重启服务
ollama serve

# 确认端口
netstat -an | findstr 11434
```

### Q2: 模型下载慢
```bash
# 设置代理 (如果需要)
set HTTPS_PROXY=http://proxy:8080
ollama pull qwen3:4b
```

### Q3: 搜索功能不工作
1. 检查网络连接
2. 运行 `windows_api_config.bat` 配置搜索API
3. 或部署SearxNG本地实例

### Q4: 知识库加载失败
1. 确认文档在 `data/` 目录下
2. 检查文件格式是否支持
3. 确保文件编码为UTF-8

## 📐 评测框架（Evaluation Framework）

Aura 内置了一套完整的 Agent / RAG 自动化评测体系，覆盖**检索质量**、**任务完成率**、**能力维度分析**和**多模型横向对比**四个层次。

### 评测指标体系

| 层次 | 指标 | 说明 |
|------|------|------|
| RAG检索 | Hit Rate@K | Top-K 中包含相关文档的查询比例 |
| RAG检索 | MRR | Mean Reciprocal Rank，越接近1越好 |
| RAG检索 | Faithfulness / Relevance | LLM-as-Judge 评估生成质量 |
| Agent | 工具调用准确率 | 正确判断是否使用工具及选对工具 |
| Agent | 任务成功率 | 回答包含期望关键词的比例 |
| 能力维度 | 逻辑推理 / 知识检索 / 工具调用 / 多轮对话 / 指令遵循 / 安全拒绝 | 6维细粒度打分 |
| 横向对比 | 综合得分排名 | 同一测试集跨模型对比，量化能力差距 |

### 快速运行评测

```bash
# 运行所有评测（RAG + Agent + 能力维度）
python run_evaluation.py --save

# 只评测 Agent（含能力维度分析）
python run_evaluation.py --agent --save

# 多模型横向对比（量化行业能力水平）
python run_evaluation.py --compare qwen2.5:7b,qwen3:4b,llama3:8b --save

# 使用 DeepSeek 作为外部 Judge（替代本地模型自评，结果更客观）
python run_evaluation.py --llm-eval --deepseek-judge YOUR_API_KEY --save

# 快速冒烟（每类只跑3条用例）
python run_evaluation.py --quick
```

### 测试集结构

在 `evaluation/test_dataset.json` 的每条用例中，通过 `dimension` 字段指定能力维度：

```json
{
  "question": "帮我分析这段代码的时间复杂度",
  "expected_tool": "search_knowledge",
  "expected_contains": ["O(n)"],
  "dimension": "reasoning"
}
```

支持的维度值：`reasoning`（逻辑推理）、`knowledge`（知识检索）、`tool_use`（工具调用）、`multi_turn`（多轮对话）、`instruction`（指令遵循）、`safety`（安全拒绝）

### 评测报告示例

```
╔══════════════════════════════════════════════════════════╗
║                    Agent评估摘要                          ║
╠══════════════════════════════════════════════════════════╣
║  工具调用准确率:  85.71%                                  ║
║  任务成功率:      78.57%                                  ║
║  平均响应时间:    3240ms                                  ║
║  通过/总数:         11/14                                 ║
╚══════════════════════════════════════════════════════════╝

能力维度得分:
   • 工具调用:   90.00% [█████████░]  (9/10)
   • 知识检索:   80.00% [████████░░]  (4/5)
   • 逻辑推理:   66.67% [██████░░░░]  (2/3)
```

## 🚀 高级功能

### 1. 自定义工具
可在 `tools.py` 中添加自定义工具函数

### 2. 记忆管理
- 自动记住用户偏好
- 保存对话历史
- 支持手动添加记忆

### 3. 多模态支持 (计划中)
- 图像识别
- 语音交互
- 文档解析

## 📈 更新日志

### v1.0.0 (2025-06-15)
- ✨ 基础AI Agent框架
- 🔍 RAG知识检索系统
- 💾 长期记忆功能
- 🛠️ 工具调用支持
- 🌐 多种搜索服务集成
- 🐳 Docker容器化部署

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**让Aura成为你最贴心的AI伙伴！** ✨🤖