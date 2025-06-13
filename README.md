# Aura AI - Personal AI Assistant (修复版)

Aura是一个基于Ollama和LangChain构建的本地AI助手，具备RAG知识检索和长期记忆功能。

## 🔧 修复版本特性

- ✅ **修复Think标签问题** - 彻底解决qwen3:4b模型输出think标签的问题
- ✅ **配置文件统一** - 统一模型配置为qwen3:4b，解决配置冲突
- ✅ **超强输出清理** - 多层防护机制，确保输出干净
- ✅ **简化架构** - 移除复杂的Agent解析器，提高稳定性
- ✅ **拼写错误修复** - 修复`loggingjie`等拼写错误

## ✨ 核心特性

- **📚 RAG知识检索**: 本地知识库和向量存储
- **💾 长期记忆**: 持久化事实和对话记忆
- **🔧 多工具支持**: 网络搜索、文件操作、知识库查询
- **🌐 实时数据**: 天气、股票、新闻等实时信息集成
- **🔒 隐私保护**: 完全本地部署，数据不上传
- **🚫 Think标签清理**: 彻底解决模型输出思考过程的问题

## 🚀 快速开始

### 环境要求

- Python 3.11
- [Ollama](https://ollama.ai/) 已安装并运行
- qwen3:4b模型已下载

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

3. **启动Ollama服务**:
   ```bash
   ollama serve
   ```

4. **下载模型**:
   ```bash
   ollama pull qwen3:4b
   ```

5. **一键启动** (推荐):
   ```bash
   # Windows
   start_aura.bat
   
   # 或手动运行
   python aura.py
   ```

## 🎯 使用方法

### 命令行界面

```bash
python aura.py
```

**基本对话**:
```
👤 输入: 你好，介绍一下你自己
🤖 Aura: 你好！我是Aura，您的AI助手。我能帮助您解答问题、记忆信息和使用各种工具。

👤 输入: 今天天气怎么样？
🤖 Aura: [自动搜索网络] 让我为您查询当前天气...

👤 输入: 记住我喜欢蓝色
🤖 Aura: 好的，我已经记住您喜欢蓝色了。
```

**特殊命令**:
- `加载知识` - 将data目录中的文档加载到知识库
- `exit` 或 `退出` - 结束对话

## 📁 项目结构

```
Aura/
├── aura.py              # 🎯 主程序入口 (修复版)
├── config_reader.py     # ⚙️ 配置文件读取器
├── memory.py            # 💾 长期记忆管理
├── rag.py              # 📚 RAG知识检索系统
├── tools.py            # 🔧 工具集实现
├── config/             # ⚙️ 配置文件
│   └── aura.conf       # 主配置文件
├── .env                # 环境变量配置
├── data/               # 📄 知识库文档
├── db/                 # 🗃️ 向量数据库 (运行时生成)
├── start_aura.bat      # 🚀 Windows启动脚本
└── start_aura.sh       # 🚀 Linux/Mac启动脚本
```

## 🔧 配置说明

### 模型配置

配置文件：`config/aura.conf`
```ini
[model]
name = qwen3:4b              # 统一使用qwen3:4b
base_url = http://localhost:11435
temperature = 0.7
max_tokens = 2048
```

### 环境变量

配置文件：`.env`
```bash
# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11435
OLLAMA_MODEL=qwen3:4b        # 与config保持一致

# 其他配置
LOG_LEVEL=INFO
```

## 🛠️ 工具能力

Aura会智能路由不同类型的查询：

| 查询类型 | 处理方式 | 示例 |
|---------|----------|------|
| 🌐 实时信息 | 网络搜索 | "今天天气"、"最新新闻" |
| 📚 专业知识 | 知识库检索 | "深度学习原理"、"技术文档" |
| 💾 个人记忆 | 记忆系统 | "我的偏好"、"之前的对话" |
| 📁 文件操作 | 文件工具 | "读取文件"、"保存内容" |
| 🤖 通用对话 | 直接回答 | 日常对话和问答 |

## 🐛 故障排除

### 常见问题

1. **Think标签问题**:
   ```
   ✅ 已在修复版中彻底解决
   - 超强制系统提示
   - 五层输出清理机制
   - 最终安全清理保障
   ```

2. **连接Ollama失败**:
   ```bash
   # 检查Ollama状态
   curl http://localhost:11435/api/tags
   
   # 重启Ollama
   ollama serve
   ```

3. **模型未找到**:
   ```bash
   # 下载qwen3:4b模型
   ollama pull qwen3:4b
   
   # 查看已安装模型
   ollama list
   ```

4. **配置冲突**:
   ```
   ✅ 已在修复版中解决
   - 统一配置管理器
   - 配置文件优先级：aura.conf > .env > 默认值
   ```

5. **拼写错误**:
   ```
   ✅ 已修复所有已知拼写错误
   - loggingjie -> logging
   - 其他导入错误
   ```

### 🔧 调试技巧

```bash
# 查看完整配置
python aura.py
# 然后输入: 显示配置

# 检查日志文件
tail -f aura.log

# 测试Ollama连接
curl http://localhost:11435/api/tags

# 测试模型
curl -X POST http://localhost:11435/api/generate \
  -d '{"model": "qwen3:4b", "prompt": "你好"}'
```

## 🔒 隐私和安全

- ✅ **完全本地运行** - 所有数据保存在本地
- ✅ **无数据上传** - 不向外部服务发送个人信息
- ✅ **可定制隐私级别** - 用户完全控制数据和配置
- ✅ **开源透明** - 所有代码开放，无隐藏功能

## 📈 更新日志

### v1.3 (修复版) - 当前版本
- 🔧 **彻底修复Think标签问题** - 多层防护机制
- ⚙️ **统一配置管理** - 解决qwen2.5:7b和qwen3:4b冲突
- 🐛 **修复拼写错误** - loggingjie等导入错误
- 🚀 **简化启动流程** - 优化启动脚本和检查机制
- 📝 **清理项目结构** - 移除冗余文件，保持git整洁
- 🛡️ **增强输出清理** - 超级清理机制确保输出质量

### v1.2 - Docker版本
- 🐳 Docker部署支持
- 🌐 Web API接口
- 🔧 健康检查机制

### v1.1 - 清理版本
- 🧹 移除个人信息
- 📝 创建通用模板

### v1.0 - 初始版本
- ✨ 基础功能实现

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支: `git checkout -b feature/新功能`
3. 提交更改: `git commit -m '添加新功能'`
4. 推送分支: `git push origin feature/新功能`
5. 提交 Pull Request

## 📜 开源协议

本项目遵循开源协议。使用时请遵守隐私和安全最佳实践。

---

**修复版本特色：** 🚫 Think标签终结者 + ⚙️ 配置统一管理 + 🛡️ 超强输出清理

**使用愉快！** 🎉 如有问题欢迎反馈。

Built with ❤️ using Ollama, LangChain, and Python