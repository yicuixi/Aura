# Aura AI 快速开始指南

欢迎使用Aura AI！这个指南将帮你在5分钟内启动项目。

## 🚀 一键设置

### Windows用户
```cmd
# 1. 下载项目
git clone https://github.com/your-username/aura.git
cd aura

# 2. 运行设置脚本
setup.bat

# 3. 选择启动方式
start_aura.bat
```

### Linux/Mac用户
```bash
# 1. 下载项目
git clone https://github.com/your-username/aura.git
cd aura

# 2. 运行设置脚本
chmod +x setup.sh
./setup.sh

# 3. 选择启动方式
chmod +x start_aura.sh
./start_aura.sh
```

## ⚡ 最简启动

如果你已经有Python 3.11+和Ollama：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动Ollama（如果未运行）
ollama serve
ollama pull qwen2.5:7b

# 启动Aura
python aura.py
```

## 🐳 Docker用户

```bash
# 确保Ollama在宿主机运行
ollama serve
ollama pull qwen2.5:7b

# 一键启动
./start_aura.sh  # 或 start_aura.bat
```

## 🆘 遇到问题？

1. **检查依赖**: `pip install -r requirements.txt`
2. **检查Ollama**: `curl http://localhost:11435/api/tags`
3. **查看详细文档**: `README.md`
4. **运行诊断**: `python -c "import aura; print('OK')"`

## 📖 下一步

- 阅读完整的 [README.md](README.md)
- 自定义配置文件 [.env](.env)
- 添加知识文档到 [data/](data/) 目录
- 探索Web API模式

祝你使用愉快！ 🎉
