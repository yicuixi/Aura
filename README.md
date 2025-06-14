# 🌐 网络搜索API配置指南

Aura支持多种网络搜索方式，从完全免费的本地部署到商业API服务。本指南将详细介绍如何申请和配置各种搜索API。

## 🚀 推荐配置方案

### 方案一：完全免费 (推荐新手)
- **SearxNG本地部署** - 完全免费，隐私友好
- 适合：个人使用，注重隐私，技术学习

### 方案二：免费+付费混合 (推荐)  
- **SearxNG** + **Google Custom Search** (免费额度)
- 适合：轻度商业使用，成本控制

### 方案三：商业级配置
- **SearxNG** + **Serper API** + **SerpAPI**
- 适合：高频使用，商业项目，稳定性要求高

## 📋 搜索服务对比

| 服务 | 费用 | 每月免费额度 | 稳定性 | 设置难度 | 隐私保护 |
|------|------|-------------|--------|----------|----------|
| SearxNG | 免费 | 无限制 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Google CSE | 免费/付费 | 100次/天 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Serper API | 付费 | 2500次 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| SerpAPI | 付费 | 100次 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🔧 方法一：SearxNG本地部署 (推荐)

### 优势
- ✅ **完全免费** - 无API限制
- ✅ **隐私保护** - 所有搜索都在本地进行
- ✅ **聚合搜索** - 同时搜索Google、Bing、DuckDuckGo等
- ✅ **无追踪** - 不记录用户搜索历史

### 安装方法

#### Docker方式 (推荐)
```bash
# 1. 创建searxng目录
mkdir searxng && cd searxng

# 2. 下载配置文件
curl -o docker-compose.yml https://raw.githubusercontent.com/searxng/searxng-docker/master/docker-compose.yaml

# 3. 生成密钥
sed -i "s|ultrasecretkey|$(openssl rand -hex 32)|g" docker-compose.yml

# 4. 启动服务
docker-compose up -d

# 5. 测试访问
curl "http://localhost:8080/search?q=test&format=json"
```

#### 手动安装 (Linux)
```bash
# 1. 安装依赖
sudo apt update
sudo apt install python3-dev python3-pip python3-venv uwsgi uwsgi-plugin-python3 git build-essential libxslt-dev zlib1g-dev libffi-dev libssl-dev

# 2. 克隆项目
cd /usr/local
sudo git clone https://github.com/searxng/searxng.git
cd searxng

# 3. 安装searxng
sudo -H pip3 install -e .

# 4. 创建配置
sudo cp searx/settings.yml searx/settings_local.yml

# 5. 生成密钥
sudo sed -i "s/ultrasecretkey/$(openssl rand -hex 32)/g" searx/settings_local.yml

# 6. 启动服务
python3 searx/webapp.py
```

### 配置Aura
```bash
# 在.env文件中设置
SEARXNG_URL=http://localhost:8080
```

---

## 🔍 方法二：Google Custom Search API

### 优势
- ✅ **免费额度** - 每天100次免费搜索
- ✅ **Google质量** - 使用Google搜索引擎
- ✅ **稳定可靠** - Google官方API
- ✅ **简单易用** - 申请配置简单

### 申请步骤

#### 1. 创建Google Cloud项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击 **"创建项目"**
3. 输入项目名称：`Aura-Search-API`
4. 点击 **"创建"**

#### 2. 启用Custom Search API
1. 在项目中，转到 **"API和服务"** > **"库"**
2. 搜索 **"Custom Search API"**
3. 点击并选择 **"启用"**

#### 3. 创建API密钥
1. 转到 **"API和服务"** > **"凭据"**
2. 点击 **"创建凭据"** > **"API密钥"**
3. 复制生成的API密钥
4. 建议点击 **"限制密钥"** 设置使用限制

#### 4. 创建自定义搜索引擎
1. 访问 [Google Custom Search](https://cse.google.com/cse/)
2. 点击 **"添加"**
3. 在 **"要搜索的网站"** 中输入 `*` (搜索整个网络)
4. 点击 **"创建"**
5. 在控制面板中，点击 **"设置"** > **"基本"**
6. 复制 **"搜索引擎ID"**

#### 5. 配置Aura
```bash
# 在.env文件中添加
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here
```

### 价格信息
- **免费额度**: 100次搜索/天
- **付费价格**: $5/1000次搜索
- **月费上限**: 约$150/月

---

## ⚡ 方法三：Serper API (推荐付费方案)

### 优势
- ✅ **性价比高** - $50/万次搜索
- ✅ **免费试用** - 2500次免费搜索
- ✅ **快速稳定** - 平均响应时间<1秒
- ✅ **简单易用** - 一个API密钥搞定

### 申请步骤

#### 1. 注册账户
1. 访问 [Serper.dev](https://serper.dev/)
2. 点击 **"Get API Key"**
3. 使用Google或GitHub账户注册
4. 验证邮箱地址

#### 2. 获取API密钥
1. 登录后自动跳转到控制台
2. 复制显示的API密钥
3. 查看免费额度：2500次搜索

#### 3. 配置Aura
```bash
# 在.env文件中添加
SERPER_API_KEY=your_serper_api_key_here
```

### 价格信息
- **免费额度**: 2500次搜索
- **付费价格**: $50/万次搜索
- **特点**: 无月费，按使用付费

---

## 🔥 方法四：SerpAPI (功能最强)

### 优势
- ✅ **功能丰富** - 支持Google、Bing、Yahoo等多个搜索引擎
- ✅ **数据详细** - 提供丰富的搜索结果元数据
- ✅ **高度可靠** - 企业级API服务
- ✅ **灵活定价** - 多种套餐选择

### 申请步骤

#### 1. 注册账户
1. 访问 [SerpAPI](https://serpapi.com/)
2. 点击 **"Sign Up"**
3. 填写基本信息注册
4. 验证邮箱地址

#### 2. 获取API密钥
1. 登录后转到控制台
2. 在 **"API Key"** 部分复制密钥
3. 查看免费额度：100次搜索/月

#### 3. 配置Aura
```bash
# 在.env文件中添加
SERPAPI_KEY=your_serpapi_key_here
```

### 价格信息
- **免费额度**: 100次搜索/月
- **基础套餐**: $50/月 (5000次搜索)
- **专业套餐**: $150/月 (15000次搜索)
- **企业套餐**: 定制价格

---

## 🔧 完整配置示例

### .env文件配置
```bash
# === 搜索服务配置 ===

# SearxNG本地搜索 (优先级最高)
SEARXNG_URL=http://localhost:8080
SEARXNG_SECRET=your_random_secret_key_here

# Google Custom Search (备选方案1)
GOOGLE_API_KEY=AIzaSyABC123DEF456GHI789JKL012MNO345PQR
GOOGLE_CSE_ID=123456789012345678901:abcdefghijk

# Serper API (备选方案2)
SERPER_API_KEY=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t

# SerpAPI (备选方案3)
SERPAPI_KEY=abcdef123456789ghijklmnop987654321qrstuvw
```

### 搜索优先级设置
Aura按以下优先级尝试搜索服务：
1. **SearxNG** (本地，免费)
2. **Google Custom Search** (免费额度)
3. **Serper API** (付费，性价比高)
4. **SerpAPI** (付费，功能强大)

---

## 🛠️ 故障排除

### SearxNG常见问题

**问题1**: SearxNG无法启动
```bash
# 检查端口占用
sudo netstat -tulpn | grep :8080

# 重启Docker容器
docker-compose restart searxng
```

**问题2**: 搜索无结果
```bash
# 检查配置文件
docker exec searxng cat /etc/searxng/settings.yml

# 查看日志
docker logs searxng
```

### API密钥问题

**问题1**: API密钥无效
- 检查密钥是否正确复制
- 确认API服务已启用
- 检查API使用限制设置

**问题2**: 超出配额限制
- 查看API控制台的使用统计
- 考虑升级套餐或添加备用API
- 实施缓存机制减少API调用

### 网络连接问题

**问题1**: 连接超时
```bash
# 测试网络连接
curl -I https://www.google.com
curl -I https://serper.dev
curl -I https://serpapi.com
```

**问题2**: DNS解析失败
```bash
# 修改DNS设置
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```

---

## 🎯 最佳实践建议

### 1. 多重备份策略
- 至少配置2个搜索服务
- 本地SearxNG + 1个云API
- 监控API使用量，避免超限

### 2. 成本优化
- 优先使用免费服务
- 设置API使用上限
- 定期清理无用的API密钥

### 3. 隐私保护
- 优先使用SearxNG本地搜索
- 定期轮换API密钥
- 避免在日志中记录敏感查询

### 4. 性能优化
- 设置合理的超时时间
- 实施搜索结果缓存
- 监控各API服务的响应时间

---

## ❓ 常见问题

**Q: 哪种搜索方式最好？**
A: 对于个人使用，推荐SearxNG本地部署。对于商业项目，推荐SearxNG + Serper API组合。

**Q: 免费额度用完了怎么办？**
A: 可以申请多个免费账户，或者升级到付费套餐，或者添加其他搜索服务。

**Q: 搜索结果质量如何？**
A: Google Custom Search和SerpAPI质量最高，Serper API性价比最好，SearxNG适合隐私保护。

**Q: 如何监控API使用量？**
A: 在各API服务的控制台可以查看使用统计，也可以在Aura中添加使用量记录。

**Q: 可以只使用一种搜索服务吗？**
A: 可以，但建议至少配置2种以确保稳定性。修改`tools.py`文件可以调整搜索优先级。

---

**配置完成后，重启Aura即可开始使用网络搜索功能！** 🎉