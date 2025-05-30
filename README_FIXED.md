# Aura AI - 修复版本使用指南

## 🔧 问题修复

原版本遇到的LLM输出解析错误已经解决。主要修复包括：

1. **输出清理机制**：自动移除`<think>`等思考标签
2. **增强系统提示**：明确禁止使用XML风格标签
3. **错误处理改进**：更好的解析错误处理
4. **简化查询逻辑**：减少复杂的路由判断

## 🚀 快速开始

### 1. 环境准备
```bash
# 确保Ollama服务正在运行
ollama serve

# 确保模型已下载
ollama pull qwen3:4b

# 检查端口11435是否可用
curl http://localhost:11435/api/tags
```

### 2. 运行修复版本
```bash
# 运行测试脚本验证修复
python test_aura_fixed.py

# 如果测试通过，运行主程序
python aura_fixed.py
```

### 3. 基本使用

#### 简单对话
```
👤 输入: 你好
🤖 Aura: 你好！我是Aura，你的AI助手。有什么可以帮助你的吗？
```

#### 记忆功能
```
👤 输入: 记住我喜欢蓝色
🤖 Aura: 好的，我已经记住你喜欢蓝色了。

👤 输入: 我喜欢什么颜色？
🤖 Aura: 根据我的记忆，你喜欢蓝色。
```

#### 知识查询
```
👤 输入: 什么是OAM
🤖 Aura: [搜索知识库] 轨道角动量(OAM)是光场的一个重要特性...
```

#### 实时搜索
```
👤 输入: 今天天气怎么样
🤖 Aura: [搜索网络] 让我为你查询当前的天气信息...
```

## 🛠️ 特殊命令

- `加载知识`：加载data目录中的文档到知识库
- `exit` 或 `退出`：结束对话
- `重置知识库`：清空并重置知识库

## 📁 项目结构

```
D:\Code\Aura\
├── aura.py              # 原版本（有解析错误）
├── aura_fixed.py        # 修复版本（推荐使用）
├── test_aura_fixed.py   # 测试脚本
├── config/
│   └── aura.conf        # 配置文件
├── memory.py            # 长期记忆管理
├── rag.py              # RAG知识检索
├── tools.py            # 工具集
├── data/               # 知识库文档
└── db/                 # 向量数据库
```

## 🔍 故障排除

### 常见问题

1. **连接Ollama失败**
   ```
   检查Ollama是否运行: ollama serve
   检查端口: netstat -an | grep 11435
   ```

2. **模型未找到**
   ```
   下载模型: ollama pull qwen3:4b
   列出模型: ollama list
   ```

3. **解析错误（已修复）**
   ```
   旧版本有此问题，请使用aura_fixed.py
   ```

4. **搜索功能不工作**
   ```
   检查SearxNG服务: curl http://localhost:8088
   或设置API密钥使用其他搜索引擎
   ```

### 性能优化建议

1. **调整模型参数**
   - 编辑`config/aura.conf`中的模型设置
   - 降低temperature可以使回复更确定性

2. **优化内存使用**
   - 定期清理对话历史
   - 控制知识库大小

3. **提升响应速度**
   - 使用更小的模型（如qwen:1.8b）
   - 减少工具数量
   - 优化搜索超时时间

## 📈 下一步计划

1. **立即改进**
   - 测试所有功能是否正常
   - 添加更多测试用例
   - 优化回复质量

2. **短期目标**
   - 完善记忆系统
   - 增强RAG功能
   - 添加更多实用工具

3. **长期愿景**
   - 多模态支持
   - 自主学习能力
   - 专业领域适配

## 🤝 反馈与支持

如果遇到问题或有改进建议，请：
1. 查看日志文件`aura.log`
2. 运行测试脚本进行诊断
3. 检查配置文件设置
4. 参考故障排除指南

---

**注意**：这是修复版本，解决了原版本的输出解析问题。建议使用`aura_fixed.py`替代原版本。
