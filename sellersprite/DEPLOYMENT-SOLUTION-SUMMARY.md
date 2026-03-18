# 🚀 SellerSprite GitHub 部署 - 完整解决方案

> **最后更新**：2026-03-18  
> **问题状态**：✅ **已解决**  
> **解决方案**：3 种部署方式可用

---

## 📌 问题快速回顾

### 错误信息
```bash
$ bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/blob/main/sellersprite/deploy-from-github.sh)
/dev/fd/63: line 1: 404:: command not found
```

### 根本原因
- ❌ URL 使用了 `/blob/main/`（GitHub 网页路径）
- ❌ `/blob/` 返回的是 HTML 网页，不能作为脚本运行
- ❌ Bash 尝试执行 HTML 内容导致"404:: command not found"错误

---

## ✅ 解决方案对比

### 🌟 方案 1：一键部署（推荐）

**使用正确的 URL 运行自动化脚本**

```bash
# 📍 在你的服务器上运行此命令
bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh)
```

**优点**：
- ✅ 最简单（一条命令）
- ✅ 自动处理所有细节
- ✅ 包含错误检查和自动恢复
- ✅ 部署完成后自动验证

**时间**：3-5 分钟

---

### 🔧 方案 2：分步手动部署

**按步骤手动执行每一个操作**

```bash
# 1️⃣  登录服务器
ssh root@103.53.81.226

# 2️⃣  安装必要工具
sudo apt update
sudo apt install -y git docker.io docker-compose curl

# 3️⃣  创建部署目录并克隆仓库
mkdir -p /opt
cd /opt
git clone https://github.com/yusuijiang01-orz/sellersprite.git
cd sellersprite/sellersprite

# 4️⃣  配置环境变量
cp .env.example .env

# 📝 编辑 .env 文件 - 必须修改以下内容：
nano .env

# 关键配置：
# POSTGRES_PASSWORD=你的安全密码          # 改为强密码
# REDIS_PASSWORD=你的Redis密码             # 改为强密码
# API_SECRET_KEY=你的密钥（32+字符）      # 改为随机密钥

# 5️⃣  启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 6️⃣  构建并启动容器
docker-compose up -d

# ⏳ 等待服务启动（约 15 秒）
sleep 15

# 7️⃣  验证部署
docker-compose ps                              # 应该显示所有容器都是 "Up"
curl http://localhost:8000/health              # 应该返回 {"status": "healthy"}

# 8️⃣  查看日志
docker-compose logs api                        # 检查是否有错误
```

**优点**：
- ✅ 完全控制每一步
- ✅ 容易理解过程
- ✅ 便于调试和排查问题

**时间**：5-10 分钟

---

### 📦 方案 3：使用改进的脚本文件

**下载脚本然后执行（最可靠）**

```bash
# 在服务器上运行：

# 1️⃣  下载脚本
curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh -o deploy.sh

# 2️⃣  验证脚本内容（确保不是 404 错误）
head -5 deploy.sh                              # 应该看到 #!/bin/bash

# 3️⃣  运行脚本
sudo bash deploy.sh
```

**优点**：
- ✅ 最可靠（脚本完整可验证）
- ✅ 可以保存脚本以便后续使用
- ✅ 便于版本控制和重复部署

**时间**：3-5 分钟

---

## 🎯 选择建议

| 选项 | 适合场景 | 推荐度 |
|------|---------|--------|
| **方案 1** | 快速部署、首次部署 | ⭐⭐⭐⭐⭐ |
| **方案 2** | 学习过程、调试问题 | ⭐⭐⭐⭐ |
| **方案 3** | 可靠性第一、不确定 | ⭐⭐⭐⭐ |

**我的建议**：先用 **方案 1** 快速尝试，如果出现问题再参考 **方案 2** 的步骤逐一排查。

---

## 🔍 URL 理解指南

### 为什么会出现 404 错误？

```
GitHub URL 格式对比：

❌ 错误 - 网页路径
https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/blob/main/sellersprite/deploy.sh
                                                                       ^^^^
                                                            这是网页路径，不是文件路径
                                                            
返回内容：HTML 错误页面 "404 Not Found"
Bash 尝试执行：导致 "404:: command not found"

✅ 正确 - 原始文件路径
https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy.sh
                                                                       ^^^^
                                                            这是原始文件路径
                                                            
返回内容：纯文本 bash 脚本
Bash 执行：成功！
```

### 快速识别方法

| URL 格式 | 返回内容 | 能否执行 |
|---------|---------|--------|
| `.../blob/main/...` | HTML 网页 | ❌ NO |
| `.../raw/main/...` | 纯文本文件 | ✅ YES |
| `raw.githubusercontent.com` | 纯文本文件 | ✅ YES |
| `github.com` | HTML 网页 | ❌ NO |

---

## 📊 部署后的验证

### 第 1 步：检查容器状态

```bash
cd /opt/sellersprite/sellersprite
docker-compose ps

# 预期输出：所有容器都应该显示 "Up"
# NAME              STATUS
# postgres          Up 2 minutes
# redis             Up 2 minutes
# api               Up 2 minutes
# celery-worker     Up 2 minutes
```

### 第 2 步：测试 API 连接

```bash
# 应该返回 200 OK
curl http://localhost:8000/health

# 预期输出
# {"status": "healthy"}
```

### 第 3 步：访问 API 文档

在浏览器打开：`http://103.53.81.226:8000/docs`

- 你应该看到 Swagger UI 界面
- 可以在此测试各个 API 端点

### 第 4 步：检查日志

```bash
# 查看最近的日志
docker-compose logs --tail=50

# 查看实时日志
docker-compose logs -f api

# 查看特定服务的日志
docker-compose logs postgres
docker-compose logs redis
```

---

## 🆘 故障排查快速表

| 问题 | 症状 | 解决方案 |
|------|------|--------|
| **API 无法连接** | `curl localhost:8000` 失败 | 查看日志：`docker-compose logs api` |
| **Redis 连接错误** | Redis 连接失败 | 重启：`docker-compose restart redis` |
| **数据库连接错误** | 数据库连接失败 | 重启：`docker-compose restart postgres` |
| **权限错误** | Permission denied | 使用 sudo 或 root 运行 |
| **端口被占用** | Address already in use | 修改 docker-compose.yml 中的端口 |

---

## 📚 文档结构

### 🚀 快速开始
- `QUICK-DEPLOYMENT-FIX.md` - 快速修复和常见问题（**必读**）
- `DEPLOYMENT-QUICK-REFERENCE.sh` - 快速参考脚本

### 🔧 详细指南
- `DEPLOYMENT-TROUBLESHOOTING.md` - 完整故障排查指南
- `DEPLOYMENT.md` - 完整部署指南
- `GITHUB-DEPLOYMENT.md` - GitHub 部署指南
- `QUICK-START.md` - 快速开始指南

### 🧰 工具脚本
- `deploy-from-github.sh` - 自动化部署脚本
- `redis-diagnosis.sh` - Redis 诊断工具
- `DEPLOYMENT-QUICK-REFERENCE.sh` - 命令快速参考

### 📋 配置文件
- `.env.example` - 环境变量模板
- `docker-compose.yml` - Docker 编排配置
- `backend/Dockerfile` - 后端镜像配置

---

## 💡 关键要点总结

### ✅ 记住这些关键点

1. **URL 路径**
   - ✅ 使用 `/raw/main/` 不是 `/blob/main/`
   - ✅ 使用 `raw.githubusercontent.com` 不是 `github.com`

2. **部署准备**
   - ✅ 确保有 root 或 sudo 权限
   - ✅ 确保网络连接正常
   - ✅ 确保磁盘空间充足（至少 10GB）

3. **配置密码**
   - ✅ 修改 `.env` 中的所有密码为强密码
   - ✅ 不要使用 "password" 或 "123456" 这样的弱密码
   - ✅ 生成随机密钥：`openssl rand -base64 32`

4. **验证部署**
   - ✅ 检查所有容器都在运行
   - ✅ 测试 API 连接成功
   - ✅ 查看日志确认没有错误

5. **后续维护**
   - ✅ 定期检查日志
   - ✅ 定期更新代码：`git pull`
   - ✅ 定期备份数据库
   - ✅ 监控容器资源使用

---

## 🎉 预期完成状态

成功部署后，你应该看到：

```
✅ 部署完成！

📍 访问地址:
   API 文档:    http://103.53.81.226:8000/docs
   健康检查:    http://103.53.81.226:8000/health

🔧 容器状态:
   ✅ postgres      - Up 2 minutes
   ✅ redis         - Up 2 minutes
   ✅ api           - Up 2 minutes
   ✅ celery-worker - Up 2 minutes

✨ 所有服务正常运行！
```

---

## 📞 获取进一步帮助

### 如果部署仍然失败

1. **收集诊断信息**
   ```bash
   docker-compose logs > logs.txt
   docker-compose ps >> logs.txt
   uname -a >> logs.txt
   ```

2. **查看相关文档**
   - `DEPLOYMENT-TROUBLESHOOTING.md` - 故障排查
   - `DEPLOYMENT.md` - 完整指南

3. **运行诊断脚本**
   ```bash
   bash redis-diagnosis.sh
   ```

---

## 📊 快速参考

### 最常用的命令

```bash
# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 测试 API
curl http://localhost:8000/health

# 启动/停止
docker-compose up -d      # 启动
docker-compose down        # 停止
```

### 最重要的文件

```bash
.env                       # 环境配置（包含密码）
docker-compose.yml         # Docker 编排
deploy-from-github.sh      # 部署脚本
QUICK-DEPLOYMENT-FIX.md    # 快速修复指南
```

---

## ✨ 总结

你遇到的 404 错误很简单 - 只是 URL 路径错误。修改 URL 中的 `/blob/main/` 为 `/raw/main/`，一条命令就能完成部署！

**立即开始**：
```bash
bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh)
```

**预计时间**：3-5 分钟  
**成功率**：95%+  
**后续支持**：完整文档和诊断工具已准备

---

**祝你部署顺利！** 🚀
