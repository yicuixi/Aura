# Aura AI Agent

Aura是一个基于LangChain和Ollama的智能AI Agent系统，拥有长期记忆、知识检索和工具使用能力。

## 功能特点

- 基于Qwen2.5模型的自然语言处理
- RAG (检索增强生成) 知识库系统
- 长期记忆管理
- 多种工具能力支持
- 本地部署与隐私保护

## 目录结构

- `aura.py` - 主程序入口（推荐使用）
- `simple_aura.py` - 轻量级版本，直接调用Ollama API
- `rag.py` - 知识检索系统
- `memory.py` - 长期记忆管理
- `tools.py` - 工具函数集合
- `data/` - 知识库文档存放目录
- `db/` - 向量数据库存储目录

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动Ollama服务

确保已安装Ollama并下载Qwen2.5模型：

```bash
ollama pull qwen2.5:7b
```

### 3. 准备知识库

将文档放入`data/`目录，支持.txt, .pdf, .md, .csv等格式。

### 4. 启动Aura

```bash
python aura.py  # 推荐（标准版）
# 或
python simple_aura.py   # 轻量级版本
```

## 使用说明

- 启动后直接与Aura对话
- 输入"加载知识"可以将data目录中的文档加入知识库
- 使用"exit"或"退出"结束对话

## 系统能力

- **知识检索**: 从已加载的文档中查找相关信息
- **长期记忆**: 记住重要事实和偏好
- **工具使用**: 文件操作、网络搜索等
- **对话管理**: 保持上下文连贯性

## 注意事项

- 确保Ollama服务正常运行
- 第一次使用时需要下载模型和嵌入模型，可能需要一些时间
- 知识库越大，检索可能越慢，建议合理控制文档数量
