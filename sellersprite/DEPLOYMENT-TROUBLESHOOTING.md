# 🚀 SellerSprite 部署故障排查指南

## 🔴 问题：404 错误

### 错误信息
```
/dev/fd/63: line 1: 404:: command not found
```

### 原因分析

你的 URL 路径有误，导致 `curl` 下载到的是 GitHub 错误页面而不是脚本文件。

**错误的 URL**：
```bash
https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/blob/main/sellersprite/deploy-from-github.sh
                                                                    ^^^
                                                          应该是 /raw/ 而不是 /blob/
```

**正确的 URL**：
```bash
https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/raw/main/sellersprite/deploy-from-github.sh
                                                                    ^^^
                                                          正确的路径前缀
```

---

## ✅ 解决方案

### 方案 1：使用正确的 URL（最简单）

```bash
# ✅ 正确的命令 - 复制并在服务器上运行
bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh)
```

**说明**：
- `/raw/main/` 是原始文件路径（不是网页路径）
- `sellersprite/` 是子目录名
- `deploy-from-github.sh` 是脚本文件名

### 方案 2：分步手动部署（更可靠）

```bash
# 1️⃣  登录服务器
ssh root@103.53.81.226

# 2️⃣  安装必要工具
apt update && apt install -y git docker.io docker-compose curl

# 3️⃣  克隆仓库到 /opt
mkdir -p /opt
cd /opt
git clone https://github.com/yusuijiang01-orz/sellersprite.git

# 4️⃣  进入项目目录
cd sellersprite/sellersprite

# 5️⃣  配置环境变量
cp .env.example .env

# 📝 编辑 .env - 设置数据库密码等关键配置
nano .env

# 关键配置项（必须修改）：
# POSTGRES_PASSWORD=你的数据库密码
# REDIS_PASSWORD=你的Redis密码
# API_SECRET_KEY=你的密钥（至少32个字符）

# 6️⃣  启动服务
docker-compose up -d

# 7️⃣  等待 15 秒让服务启动
sleep 15

# 8️⃣  验证部署
docker-compose ps
curl http://localhost:8000/health

# ✅ 访问应用
# API 文档: http://103.53.81.226:8000/docs
# 健康检查: http://103.53.81.226:8000/health
```

### 方案 3：使用改进的部署脚本

如果你的仓库中已经有了改进的 `deploy-from-github.sh`：

```bash
# 1. 下载脚本到本地
curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh -o deploy.sh

# 2. 在服务器上运行
ssh root@103.53.81.226 'bash -s' < deploy.sh
```

---

## 🔍 故障诊断

如果部署后出现问题，按照以下步骤诊断：

### 1. 查看容器状态
```bash
cd /opt/sellersprite/sellersprite
docker-compose ps

# 输出示例（所有容器都应该是 Up）:
# NAME              COMMAND                  SERVICE     STATUS
# postgres-db       docker-entrypoint.sh     postgres    Up 2 minutes
# redis-server      redis-server --appe...  redis       Up 2 minutes
# api               uvicorn main:app --...  api         Up 2 minutes
# celery-worker     celery -A celery_app...  worker      Up 2 minutes
```

### 2. 查看详细日志
```bash
# API 服务日志
docker-compose logs api

# Redis 服务日志
docker-compose logs redis

# 数据库日志
docker-compose logs postgres

# 查看最近 100 行日志
docker-compose logs --tail=100

# 实时查看日志
docker-compose logs -f api
```

### 3. 测试各个服务

```bash
# 测试 API
curl http://localhost:8000/health

# 测试 Redis
docker-compose exec redis redis-cli ping

# 测试数据库
docker-compose exec postgres psql -U postgres -d sellersprite -c "SELECT 1"

# 进入 API 容器进行调试
docker-compose exec api bash
```

### 4. 常见问题

#### ❌ API 无法连接
```bash
# 查看 API 日志
docker-compose logs api

# 检查端口是否在监听
netstat -tlnp | grep 8000
ss -tlnp | grep 8000

# 重启 API 服务
docker-compose restart api
```

#### ❌ Redis 连接失败
```bash
# 查看 Redis 日志
docker-compose logs redis

# 测试 Redis 连接
docker-compose exec redis redis-cli ping

# 重启 Redis
docker-compose restart redis

# 运行 Redis 诊断脚本（如果存在）
bash redis-diagnosis.sh
```

#### ❌ 数据库连接失败
```bash
# 查看数据库日志
docker-compose logs postgres

# 检查数据库是否在运行
docker ps | grep postgres

# 重启数据库
docker-compose restart postgres

# 重新初始化所有服务
docker-compose down -v
docker-compose up -d
```

#### ❌ 权限错误
```bash
# 确保以 root 运行
sudo -i

# 或使用 sudo
sudo docker-compose ps
```

---

## 📋 完整部署清单

使用以下清单确保部署成功：

- [ ] 服务器可以访问（SSH 连接正常）
- [ ] 安装了 Docker 和 Docker Compose
- [ ] 克隆了 GitHub 仓库
- [ ] 创建并配置了 `.env` 文件
- [ ] 所有容器都在运行（`docker-compose ps`）
- [ ] API 可以访问（`curl http://localhost:8000/health`）
- [ ] 数据库连接正常
- [ ] Redis 连接正常
- [ ] 可以访问 API 文档（`http://IP:8000/docs`）

---

## 🆘 获取帮助

### 如果问题仍未解决

1. **收集诊断信息**：
   ```bash
   # 保存所有服务日志
   docker-compose logs > deploy_logs.txt
   
   # 保存容器状态
   docker-compose ps > container_status.txt
   
   # 保存系统信息
   uname -a >> diagnostic_info.txt
   df -h >> diagnostic_info.txt
   ```

2. **分享诊断结果**：
   - 完整的错误日志
   - 命令输出
   - 部署步骤

3. **参考文档**：
   - `DEPLOYMENT.md` - 完整部署指南
   - `GITHUB-DEPLOYMENT.md` - GitHub 部署指南
   - `QUICK-START.md` - 快速开始
   - `DEPLOYMENT_FIX.md` - Redis 问题修复

---

## 📌 重点回顾

### URL 路径对比

| 用途 | URL 格式 | 示例 |
|------|---------|------|
| 网页浏览 | `blob/main/` | `github.com/user/repo/blob/main/file.sh` |
| 原始文件 | `raw/main/` | `raw.githubusercontent.com/.../raw/main/file.sh` |
| 直接下载 | `raw/main/` | `curl -sL raw.githubusercontent.com/.../raw/main/file.sh` |

### 正确的 curl 命令格式

```bash
# ✅ 正确
curl -sL https://raw.githubusercontent.com/user/repo/main/path/file.sh | bash

# ❌ 错误 - 使用了 blob 而不是 raw
curl -sL https://raw.githubusercontent.com/user/repo/blob/main/path/file.sh | bash
```

---

**记住：任何时候遇到"404"错误，首先检查 URL 中是否使用了正确的 `/raw/main/` 路径！**
