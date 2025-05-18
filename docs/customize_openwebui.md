# 为Aura定制OpenWebUI

本指南将帮助您配置和定制OpenWebUI，使其更好地与Aura AI集成。

## 基本定制

### 修改系统提示词

为了让OpenWebUI中使用的Qwen模型表现得像Aura，您可以设置一个定制的系统提示词：

1. 在OpenWebUI中创建新聊天
2. 点击设置图标，选择"高级"
3. 在"系统提示"中输入以下内容：

```
你是Aura，一个智能个人助手，拥有以下能力：
1. 记忆用户偏好和重要信息
2. 使用知识库回答专业问题
3. 搜索网络获取最新信息
4. 处理复杂查询和生成内容

与用户交流时保持友好、专业的态度，提供有洞察力的回答和建议。
如果需要更多信息来回答问题，主动询问用户。
```

4. 点击"保存"

### 设置RAG知识检索插件

OpenWebUI支持插件，您可以启用RAG知识检索插件来连接Aura的知识库：

1. 在OpenWebUI中，转到"插件"选项卡
2. 启用"RAG"插件
3. 配置API端点为`http://localhost:5000/api/search_knowledge`
4. 测试连接

## 高级定制

### 添加Aura API集成

要将Aura的所有功能集成到OpenWebUI，您需要使用API桥接脚本：

1. 运行Aura API服务：
   ```bash
   python aura_webui.py
   ```

2. 在OpenWebUI中配置自定义工具：
   - 转到"设置" > "开发者选项"
   - 添加以下API端点：
     - 知识库搜索: `http://localhost:5000/api/search_knowledge`
     - 记忆存储: `http://localhost:5000/api/save_memory`
     - 记忆检索: `http://localhost:5000/api/recall_memory`
     - 网络搜索: `http://localhost:5000/api/search_web`
     - 文件读写: `http://localhost:5000/api/read_file` 和 `http://localhost:5000/api/write_file`

### 使用OpenWebUI的提示词模板

创建以下提示词模板，方便快速访问Aura功能：

1. **记忆存储模板**
   ```
   请记住以下信息：
   类别: {{category}}
   键名: {{key}}
   值: {{value}}
   ```

2. **知识检索模板**
   ```
   请使用我的知识库搜索以下问题：
   {{query}}
   ```

3. **网络搜索模板**
   ```
   请搜索网络获取以下信息：
   {{query}}
   ```

## 界面定制

### 自定义CSS

您可以通过注入自定义CSS来改变OpenWebUI的外观：

1. 创建一个名为`custom.css`的文件，内容如下：
   ```css
   :root {
     --primary-color: #4f46e5;  /* 自定义主色调 */
     --background-color: #f9fafb;
     --text-color: #111827;
   }
   
   .chat-message-agent {
     background-color: rgba(79, 70, 229, 0.1);  /* Aura风格的消息背景 */
   }
   
   /* 自定义标题 */
   .app-title::before {
     content: "Aura AI";
     font-weight: bold;
   }
   ```

2. 使用浏览器扩展将CSS注入到OpenWebUI页面

### 添加Aura图标

您可以替换OpenWebUI默认图标：

1. 准备一个正方形的Aura图标 (PNG或SVG格式)
2. 使用浏览器控制台或CSS覆盖原始图标

## 高级功能整合

如果您想深度整合Aura和OpenWebUI，可以考虑以下修改：

1. **修改OpenWebUI源码**：如果您熟悉React，可以克隆OpenWebUI仓库并添加Aura专属组件
2. **为OpenWebUI创建Aura插件**：开发专门的插件，直接连接Aura的所有功能
3. **定制Docker镜像**：创建一个包含OpenWebUI和Aura所有组件的单一Docker镜像
