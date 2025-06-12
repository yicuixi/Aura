# Aura AI - Personal AI Assistant

Aura是一个基于Ollama和LangChain构建的本地AI助手，具备ReAct推理、RAG知识检索和长期记忆功能。

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
- Qwen3:4b模型已下载

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
   ollama pull qwen3:4b
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

```bash
# 启动所有服务 (Ollama + SearxNG + WebUI)
docker-compose up -d

# 检查服务状态
docker ps
```

## 📁 项目结构

```
Aura/
├── aura.py              # 🎯 主程序入口
├── memory.py            # 💾 长期记忆管理
├── rag.py              # 📚 RAG知识检索系统
├── tools.py            # 🔧 工具集实现
├── config/             # ⚙️ 配置文件
├── prompts/            # 📝 系统提示词模板
├── query_handlers/     # 🎛️ 专用查询处理器
├── data/               # 📄 知识库文档
│   └── example_profile.md  # 用户档案模板
├── docker/             # 🐳 Docker配置
├── db/                 # 🗃️ 向量数据库 (运行时生成)
└── personal_backup/    # 📋 个人信息备份
```

## 🔧 配置说明

### 基础配置

编辑 `config/aura.conf` 自定义设置：

```ini
[model]
name = qwen3:4b
base_url = http://localhost:11435
temperature = 0.7

[search]
searxng_url = http://localhost:8088
timeout = 15
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

在 `tools.py` 中添加新的工具函数，然后在 `aura_fixed.py` 中注册。

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
   ollama pull qwen3:4b
   
   # 查看已安装模型
   ollama list
   ```

3. **搜索功能异常**:
   ```bash
   # 检查SearxNG服务
   curl http://localhost:8088/search?q=test&format=json
   
   # 或设置API密钥使用其他搜索
   export SERPER_API_KEY=your_key
   ```

4. **知识库为空**:
   ```bash
   # 确保有文档在data目录
   ls data/
   
   # 运行加载知识命令
   python aura_fixed.py
   👤 输入: 加载知识
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

### v1.1 (Latest) - 清理版本
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