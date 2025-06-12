# Aura AI - Personal AI Assistant

Aura是一个基于Ollama和LangChain构建的本地AI助手，具备ReAct推理、RAG知识检索和长期记忆功能。

## 🐳 Docker 快速部署

**一键启动脚本：**
```bash
# Windows用户
start_aura.bat

# Linux/Mac用户
chmod +x start_aura.sh
./start_aura.sh
```

**手动部署：**
```bash
# 1. 启动Ollama（在宿主机）
ollama serve
ollama pull qwen2.5:7b

# 2. 选择部署模式
# 命令行模式
docker-compose up -d
docker exec -it aura_ai python aura.py

# Web API模式  
docker-compose -f docker-compose-api.yml up -d
curl http://localhost:5000/health
```

**服务地址：**
- Aura API: http://localhost:5000 (仅Web模式)
- SearxNG: http://localhost:8088
- Ollama: http://localhost:11435

详细配置请参考下方 **Docker部署** 部分。

## ✨ 核心特性

- **🧠 ReAct推理框架**: Think-Action-Observation模式的复杂问题解决
- **📚 RAG知识检索**: 本地知识库和向量存储
- **💾 长期记忆**: 持久化事实和对话记忆
- **🔧 多工具支持**: 网络搜索、文件操作、知识库查询
- **🌐 实时数据**: 天气、股票、新闻等实时信息集成
- **🔒 隐私保护**: 完全本地部署，数据不上传

## 🚀 快速开始

### 环境要求

- Python 3.11
- [Ollama](https://ollama.ai/) 已安装并运行 (http://localhost:11435)
- Qwen2.5模型已下载

### 安装步骤

1. **克隆项目**:
   ```bash
   git clone <your-repo-url>
   cd Aura
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **启动Ollama服务** (如果未启动):
   ```bash
   ollama serve
   ```

4. **下载模型** (如果未下载):
   ```bash
   ollama pull qwen2.5:7b
   ```

5. **运行Aura**:
   ```bash
   python aura.py
   ```

## 🎯 使用方法

### 命令行界面

```bash
python aura.py
```

**基本对话**:
```
👤 输入: 你好，介绍一下自己
🤖 Aura: 你好！我是Aura，您的AI助手...

👤 输入: 今天天气怎么样？
🤖 Aura: [自动搜索网络] 让我为您查询当前天气...

👤 输入: 记住我喜欢蓝色
🤖 Aura: 好的，我已经记住您喜欢蓝色了。
```

**特殊命令**:
- `加载知识` - 将data目录中的文档加载到知识库
- `exit` 或 `退出` - 结束对话

### Docker部署

Docker部署提供两种模式：

#### 模式1：命令行交互模式
适合本地开发、学习、个人使用
```bash
# 1. 确保Ollama在宿主机运行
ollama serve
ollama pull qwen2.5:7b

# 2. 启动所有服务
docker-compose up -d

# 3. 进入交互式会话
docker exec -it aura_ai python aura.py

# 4. 查看服务状态
docker-compose ps
```

#### 模式2：Web API模式
适合集成到其他应用、远程访问、多用户
```bash
# 1. 启动API服务
docker-compose -f docker-compose-api.yml up -d

# 2. 测试API
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}]
  }'

# 3. 健康检查
curl http://localhost:5000/health
```

**服务端口说明：**
- Aura API：`http://localhost:5000` (仅Web模式)
- SearxNG搜索：`http://localhost:8088`
- Ollama API：`http://localhost:11435`（宿主机）

**注意事项：**
- Ollama必须在宿主机运行，容器通过`host.docker.internal`访问
- 数据目录会挂载到容器，确保数据持久化
- 首次启动可能需要几分钟来下载依赖

## 📁 项目结构

```
Aura/
├── aura.py              # 🎯 主程序入口
├── aura_api.py          # 🌐 Web API服务
├── memory.py            # 💾 长期记忆管理
├── rag.py              # 📚 RAG知识检索系统
├── tools.py            # 🔧 工具集实现
├── config/             # ⚙️ 配置文件
├── prompts/            # 📝 系统提示词模板
├── query_handlers/     # 🎛️ 专用查询处理器
├── data/               # 📄 知识库文档
│   └── example_profile.md  # 用户档案模板
├── docker/             # 🐳 Docker配置
│   ├── docker-compose.yml      # 命令行模式
│   ├── docker-compose-api.yml  # Web API模式
│   ├── Dockerfile              # 基础镜像
│   ├── Dockerfile.api          # API镜像
│   ├── start_aura.bat          # Windows启动脚本
│   └── start_aura.sh           # Linux/Mac启动脚本
├── db/                 # 🗃️ 向量数据库 (运行时生成)
└── personal_backup/    # 📋 个人信息备份
```

## 🔧 配置说明

### 基础配置

编辑 `config/aura.conf` 自定义设置：

```ini
[model]
name = qwen2.5:7b
base_url = http://localhost:11435
temperature = 0.7

[search]
searxng_url = http://localhost:8088
timeout = 15
```

### 环境变量配置

复制 `.env.example` 为 `.env` 并修改：

```bash
# Ollama 配置
OLLAMA_BASE_URL=http://host.docker.internal:11435
OLLAMA_MODEL=qwen2.5:7b

# SearxNG 配置  
SEARXNG_SECRET=your_random_secret_key_here
SEARXNG_URL=http://searxng:8080

# API 配置 (仅Web模式)
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 个性化设置

1. **自定义用户信息**: 编辑 `data/example_profile.md`
2. **调整系统提示**: 编辑 `prompts/` 中的提示词文件
3. **添加知识文档**: 将文档放入 `data/` 目录，运行时使用"加载知识"命令

## 🛠️ 工具能力

Aura会智能路由不同类型的查询：

| 查询类型 | 处理方式 | 示例 |
|---------|----------|------|
| 🌐 实时信息 | 网络搜索 | "今天天气"、"最新新闻" |
| 📚 专业知识 | 知识库检索 | "深度学习原理"、"技术文档" |
| 💾 个人记忆 | 记忆系统 | "我的偏好"、"之前的对话" |
| 📁 文件操作 | 文件工具 | "读取文件"、"保存内容" |
| 🤖 通用对话 | 完整推理 | 复杂分析和综合任务 |

## 🎨 自定义指南

### 1. 个性化助手

编辑 `prompts/aura_claude_style.txt`:
```
你是Aura，[用户名]的AI助手。

**背景知识：**
[用户]是[职业/身份]，[特定信息]...
```

### 2. 添加知识库

```bash
# 将文档放入data目录
cp your_documents.md data/

# 在Aura中加载
👤 输入: 加载知识
请输入文件扩展名(默认.md): .md
```

### 3. 扩展工具功能

在 `tools.py` 中添加新的工具函数，然后在 `aura.py` 中注册。

## 🌐 Web API 使用

### OpenAI兼容API

```python
import requests

def chat_with_aura(message):
    response = requests.post(
        "http://localhost:5000/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": message}]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

# 使用示例
answer = chat_with_aura("帮我解释一下什么是RAG？")
print(answer)
```

### 扩展API端点

- `GET /health` - 健康检查
- `POST /v1/chat/completions` - OpenAI兼容聊天API
- `POST /api/knowledge/load` - 加载知识库
- `POST /api/memory/add` - 添加记忆
- `GET /api/memory/get` - 获取记忆

## 🐛 故障排除

### 常见问题

1. **连接Ollama失败**:
   ```bash
   # 检查Ollama状态
   curl http://localhost:11435/api/tags
   
   # 重启Ollama
   ollama serve
   ```

2. **模型未找到**:
   ```bash
   # 下载模型
   ollama pull qwen2.5:7b
   
   # 查看已安装模型
   ollama list
   ```

3. **搜索功能异常**:
   ```bash
   # 检查SearxNG服务
   curl "http://localhost:8088/search?q=test&format=json"
   
   # 重启SearxNG服务
   docker-compose restart searxng
   ```

4. **知识库为空**:
   ```bash
   # 确保有文档在data目录
   ls data/
   
   # 运行加载知识命令
   python aura.py
   👤 输入: 加载知识
   ```

5. **Docker服务异常**:
   ```bash
   # 检查容器状态
   docker-compose ps
   
   # 查看容器日志
   docker-compose logs aura
   
   # 重启服务
   docker-compose restart aura
   
   # 重新构建并启动
   docker-compose up --build -d
   
   # 检查宿主机Ollama连接
   docker exec -it aura_ai curl http://host.docker.internal:11435/api/tags
   ```

### 🔧 调试命令

```bash
# 查看所有容器状态
docker-compose ps

# 查看容器日志
docker-compose logs -f aura
docker-compose logs -f searxng

# 进入容器调试
docker exec -it aura_ai bash

# 重新构建并启动
docker-compose down
docker-compose up --build -d

# 清理所有容器和数据（谨慎使用）
docker-compose down -v
docker system prune -a
```

## 🔒 隐私和安全

- ✅ **完全本地运行** - 所有数据保存在本地
- ✅ **无个人信息** - 项目中不包含任何个人敏感信息
- ✅ **可定制隐私级别** - 用户完全控制数据和配置
- ✅ **开源透明** - 所有代码开放，无隐藏功能

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支: `git checkout -b feature/新功能`
3. 提交更改: `git commit -m '添加新功能'`
4. 推送分支: `git push origin feature/新功能`
5. 提交 Pull Request

## 📜 开源协议

本项目遵循开源协议。使用时请遵守隐私和安全最佳实践。

## 🆘 获取帮助

- 📖 查看项目文档和代码注释
- 🐛 [提交Issue](https://github.com/your-repo/issues) 报告问题
- 💬 [Discussions](https://github.com/your-repo/discussions) 参与讨论

---

## 📈 更新日志

### v1.2 (Latest) - Docker完整版
- 🐳 完整Docker化部署，支持命令行和Web API两种模式
- 🚀 一键启动脚本，Windows和Linux双平台支持
- 🌐 OpenAI兼容的Web API接口
- 🔧 健康检查和故障排除指南
- 📝 完整的Docker部署文档

### v1.1 - 清理版本
- 🧹 移除所有个人信息和敏感数据
- 🔧 修复LLM输出解析问题
- 📝 创建通用模板和配置
- 🚀 优化项目结构和文档

### v1.0 - 初始版本
- ✨ 基础ReAct推理框架
- 📚 RAG知识检索系统
- 💾 长期记忆功能
- 🔧 多工具集成

---

**使用愉快！** 🎉 如有问题欢迎反馈。

Built with ❤️ using Ollama, LangChain, and Python