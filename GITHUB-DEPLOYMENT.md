# GitHub 到 Debian 服务器部署指南

## 🚀 快速开始（3 步）

### 第 1 步：在本地上传项目到 GitHub

#### 1.1 初始化 Git（如果还没有）

```bash
cd d:/App/sellersprite
git init
git add .
git commit -m "Initial commit"
```

#### 1.2 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 创建新仓库（例如 `sellersprite`）
3. **不要** 勾选"Initialize with README"

#### 1.3 推送到 GitHub

```bash
git remote add origin https://github.com/你的用户名/sellersprite.git
git branch -M main
git push -u origin main

# 如果推送失败，可能需要配置 Git 凭证
# 设置 Personal Access Token: https://github.com/settings/tokens
```

### 第 2 步：在服务器上下载部署脚本

```bash
# 登录到服务器
ssh root@103.53.81.226

# 下载部署脚本
curl -o deploy-from-github.sh https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh

# 或者用 wget
wget https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh

# 给予执行权限
chmod +x deploy-from-github.sh
```

### 第 3 步：运行部署脚本

```bash
# 以 root 身份运行
sudo bash deploy-from-github.sh

# 按照提示输入：
# - GitHub 仓库 URL
# - 安装目录
# - 数据库密码
# - Redis 密码

# 脚本会自动：
# ✓ 安装 Docker
# ✓ 克隆代码
# ✓ 配置环境
# ✓ 启动服务
# ✓ 验证部署
```

---

## 📋 详细步骤

### 准备阶段：GitHub 仓库设置

#### 检查项目文件

确保你的项目包含这些关键文件：

```
sellersprite/
├── docker-compose.yml          # ✓ 必须
├── backend/
│   ├── Dockerfile             # ✓ 必须
│   ├── requirements.txt        # ✓ 必须
│   ├── main.py
│   ├── init_db.py
│   └── app/
└── .env.example               # ✓ 必须
```

**如果缺少这些文件，参考我提供的文件**

#### 创建 .gitignore

```bash
# 在项目根目录创建 .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.venv/
venv/

# 环境配置
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker
.dockerignore

# 日志
*.log

# 操作系统
.DS_Store
Thumbs.db

# 数据
db.sqlite3
*.db
dump.rdb
EOF
```

#### 创建 README.md

```bash
cat > README.md << 'EOF'
# SellerSprite Clone

亚马逊选品与数据分析工具

## 快速开始

### Docker Compose 部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/sellersprite.git
cd sellersprite

# 2. 配置环境
cp .env.example .env

# 3. 启动服务
docker compose up -d

# 4. 验证
curl http://localhost:8000/health
```

### 访问 API 文档

http://localhost:8000/docs

## 部署到 Debian 服务器

### 方法 1：使用部署脚本（推荐）

```bash
ssh root@你的服务器IP
curl -o deploy.sh https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh
sudo bash deploy.sh
```

### 方法 2：手动部署

参考 DEPLOYMENT.md

## 技术栈

- FastAPI
- PostgreSQL
- Redis
- Celery
- Docker

## 文档

- [部署指南](./DEPLOYMENT.md)
- [API 文档](http://localhost:8000/docs)
EOF
```

### 部署阶段：到服务器

#### 方式 1：使用自动部署脚本（推荐）

这是最简单的方式，完全自动化。

```bash
# 在服务器上
ssh root@103.53.81.226

# 下载并运行部署脚本
bash <(curl -sL https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh)
```

**脚本会自动处理：**
- ✓ 安装 Docker 和 Docker Compose
- ✓ 克隆 GitHub 仓库
- ✓ 配置 .env 文件
- ✓ 启动 Docker 容器
- ✓ 验证服务

#### 方式 2：手动部署（更灵活）

```bash
# 1. 登录服务器
ssh root@103.53.81.226

# 2. 安装 Docker
apt update
apt install -y docker.io docker-compose git

# 3. 启动 Docker
systemctl start docker
systemctl enable docker

# 4. 克隆项目
cd /opt
git clone https://github.com/你的用户名/sellersprite.git

# 5. 配置环境
cd sellersprite
cp .env.example .env
# 编辑 .env 文件，设置密码等
nano .env

# 6. 启动服务
docker-compose up -d

# 7. 验证
docker-compose ps
curl http://localhost:8000/health
```

---

## 🔄 更新代码

### 拉取最新代码

```bash
cd /opt/sellersprite

# 1. 获取最新代码
git pull

# 2. 重建并启动
docker-compose up -d --build

# 3. 查看状态
docker-compose ps
```

### 设置自动更新

创建 `/opt/sellersprite/update.sh`：

```bash
#!/bin/bash
cd /opt/sellersprite
git pull
docker-compose up -d --build
```

然后添加到 crontab（每天午夜自动更新）：

```bash
crontab -e

# 添加这一行
0 0 * * * bash /opt/sellersprite/update.sh >> /var/log/sellersprite-update.log 2>&1
```

---

## 📊 常用命令

### 查看服务状态

```bash
# 查看所有容器
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f redis
docker-compose logs -f postgres
```

### 管理服务

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重启特定服务
docker-compose restart api
```

### 进入容器

```bash
# 进入 API 容器
docker-compose exec api bash

# 进入 Redis 容器
docker-compose exec redis redis-cli

# 进入数据库容器
docker-compose exec postgres psql -U postgres
```

### 清理

```bash
# 停止并删除容器（保留数据）
docker-compose down

# 完全重置（删除所有数据）
docker-compose down -v

# 清理未使用的镜像
docker image prune -a
```

---

## 🔒 安全配置

### 1. 更改默认密码

编辑 `.env` 文件，更改这些密码为强密码：

```bash
POSTGRES_PASSWORD=你的强密码
REDIS_PASSWORD=你的强密码
API_KEY=你的API密钥
```

### 2. 配置防火墙

```bash
# 仅允许必要的端口
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
```

### 3. 配置 SSL 证书

使用 Let's Encrypt 的免费证书：

```bash
# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 申请证书
certbot certonly --standalone -d 你的域名.com
```

### 4. 配置 Nginx 反向代理

参考 DEPLOYMENT.md 中的 Nginx 配置部分。

---

## 📈 监控和日志

### 查看日志

```bash
# 实时日志
docker-compose logs -f api

# 查看最后 100 行
docker-compose logs api | tail -100

# 导出日志
docker-compose logs api > api-logs.txt
```

### 监控资源使用

```bash
# 查看容器资源使用情况
docker stats

# 查看磁盘空间
df -h

# 查看内存使用
free -h
```

### 备份数据

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U postgres sellersprite > backup.sql

# 备份 Redis 数据
docker cp sellersprite-redis:/data/dump.rdb ./redis-backup.rdb
```

---

## ✅ 验证清单

部署完成后，检查以下项目：

- [ ] Docker 容器全部运行（`docker-compose ps`）
- [ ] API 可访问（`curl http://localhost:8000/health`）
- [ ] Redis 可连接（`docker-compose exec redis redis-cli ping`）
- [ ] 数据库已初始化（`docker-compose logs api | grep "database"`）
- [ ] API 文档可访问（http://103.53.81.226:8000/docs）

---

## 🆘 故障排查

### API 无法启动

```bash
# 查看详细错误
docker-compose logs api

# 常见原因：
# 1. Redis 未启动 - 检查: docker-compose logs redis
# 2. 数据库未初始化 - 查看日志信息
# 3. 环境变量错误 - 检查 .env 文件
```

### Redis 连接失败

```bash
# 查看 Redis 日志
docker-compose logs redis

# 测试连接
docker-compose exec redis redis-cli ping
# 应该输出: PONG
```

### 端口被占用

```bash
# 检查端口占用
lsof -i :8000
lsof -i :5432
lsof -i :6379

# 修改 docker-compose.yml 中的端口映射
# 例如: "8001:8000" 改为使用 8001 端口
```

### 容器内存不足

```bash
# 查看容器大小
docker ps -s

# 清理未使用的容器和镜像
docker system prune -a
```

---

## 📞 需要帮助？

- 📖 完整部署指南：参考 DEPLOYMENT.md
- 🐛 问题诊断：运行 redis-diagnosis.sh
- 📝 查看日志：docker-compose logs
- 🌐 访问文档：http://你的服务器IP:8000/docs

---

## 🎯 下一步

1. ✅ 将项目上传到 GitHub
2. ✅ 在服务器上运行部署脚本
3. ✅ 验证服务运行正常
4. ✅ 配置 SSL 和反向代理
5. ✅ 设置定期备份

祝部署顺利！🚀

