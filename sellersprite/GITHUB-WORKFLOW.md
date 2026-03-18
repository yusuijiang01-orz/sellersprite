# GitHub 部署完整工作流程

## 📋 目录

1. [本地开发阶段](#本地开发阶段)
2. [上传到 GitHub](#上传到-github)
3. [服务器部署](#服务器部署)
4. [后续维护](#后续维护)

---

## 🖥️ 本地开发阶段

### 前置要求

```bash
# 安装 Git
# Windows: https://git-scm.com/download/win
# Mac: brew install git
# Linux: apt install git

# 验证安装
git --version
```

### 初始化项目仓库

```bash
cd d:/App/sellersprite

# 初始化 Git 仓库
git init

# 配置用户信息（首次使用）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"

# 验证配置
git config --list
```

### 创建 .gitignore 文件

在项目根目录创建 `.gitignore`：

```bash
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

# 环境配置（敏感信息）
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Docker
.dockerignore
docker-compose.override.yml

# 日志
*.log
logs/

# 操作系统
.DS_Store
Thumbs.db

# 数据文件
*.db
db.sqlite3
dump.rdb
*.sql

# 临时文件
.tmp/
temp/
.cache/
EOF
```

### 提交初始代码

```bash
# 查看未跟踪文件
git status

# 添加所有文件到暂存区
git add .

# 提交初始版本
git commit -m "Initial commit: SellerSprite Clone 项目初始化

- 添加 FastAPI 后端
- 配置 PostgreSQL 数据库
- 集成 Redis 缓存
- 配置 Docker 部署
- 添加 Celery 任务队列"

# 查看提交历史
git log --oneline -5
```

### 本地测试

```bash
# 测试 Docker Compose
docker-compose up -d

# 验证服务
docker-compose ps
curl http://localhost:8000/health

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

---

## 🚀 上传到 GitHub

### 第 1 步：创建 GitHub 仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `sellersprite`
   - **Description**: `Amazon product research and data analysis tool`
   - **Visibility**: `Public` 或 `Private`
   - **不要** 勾选"Initialize this repository with"
3. 点击 "Create repository"

### 第 2 步：连接本地仓库到 GitHub

```bash
cd d:/App/sellersprite

# 添加远程仓库
git remote add origin https://github.com/你的用户名/sellersprite.git

# 重命名分支（如果需要）
git branch -M main

# 推送代码到 GitHub
git push -u origin main

# 验证推送成功
git branch -vv
```

### 第 3 步：验证 GitHub 仓库

1. 访问 https://github.com/你的用户名/sellersprite
2. 检查文件是否都已上传
3. 查看提交历史是否正确

### 创建 GitHub 令牌（可选，私有仓库需要）

如果是私有仓库，需要设置访问令牌：

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 勾选 `repo` 权限
4. 点击 "Generate token"
5. **复制并保存** 令牌（只显示一次）

在服务器上使用：

```bash
# 克隆私有仓库时使用令牌
git clone https://你的用户名:令牌@github.com/你的用户名/sellersprite.git
```

---

## 📦 服务器部署

### 前置要求

- Debian/Ubuntu 系统
- 10GB 磁盘空间
- 4GB+ RAM
- 网络连接

### 方式 1：自动部署脚本（推荐）⭐⭐⭐

#### 1.1 下载并运行脚本

```bash
# 登录服务器
ssh root@103.53.81.226

# 一键部署（推荐）
bash <(curl -sL https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh)

# 或分步下载后运行
curl -o /tmp/deploy.sh https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh
bash /tmp/deploy.sh
```

#### 1.2 按照提示输入参数

```
请输入 GitHub 仓库 URL: https://github.com/你的用户名/sellersprite.git
安装目录 (默认: /opt/sellersprite): 
数据库密码 (默认: password): 你的强密码
Redis 密码 (留空表示无密码): 
```

#### 1.3 等待部署完成

脚本会自动：
- ✅ 安装 Docker 和 Docker Compose
- ✅ 克隆 GitHub 仓库
- ✅ 配置 .env 文件
- ✅ 启动 Docker 容器
- ✅ 验证服务

### 方式 2：手动部署（更可控）

#### 2.1 安装依赖

```bash
ssh root@103.53.81.226

# 更新包列表
apt update

# 安装必要工具
apt install -y git curl

# 安装 Docker
apt install -y docker.io

# 安装 Docker Compose
apt install -y docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 2.2 启动 Docker 服务

```bash
# 启动 Docker 守护进程
systemctl start docker

# 设置开机自启
systemctl enable docker

# 验证 Docker
docker ps
```

#### 2.3 克隆项目

```bash
# 进入部署目录
cd /opt

# 克隆仓库
git clone https://github.com/你的用户名/sellersprite.git

# 进入项目目录
cd sellersprite

# 查看分支
git branch -a
```

#### 2.4 配置环境变量

```bash
# 复制 .env 示例文件
cp .env.example .env

# 编辑 .env 文件
nano .env

# 修改以下关键配置
# POSTGRES_PASSWORD=你的强密码
# REDIS_PASSWORD=你的强密码
# LOG_LEVEL=INFO

# 保存退出：Ctrl+O → Enter → Ctrl+X
```

#### 2.5 启动服务

```bash
# 构建 Docker 镜像
docker-compose build

# 启动所有容器
docker-compose up -d

# 查看容器状态
docker-compose ps

# 等待服务启动
sleep 10

# 验证 API
curl http://localhost:8000/health
```

#### 2.6 验证部署成功

```bash
# 查看容器状态
docker-compose ps

# 应该看到这些容器运行中：
# - postgres (healthy)
# - redis (healthy)
# - api (running)
# - celery (running)

# 测试 API 连接
curl http://localhost:8000/health
# 输出：{"status": "healthy"}

# 查看 API 文档
# 浏览器访问：http://103.53.81.226:8000/docs
```

---

## 🔄 后续维护

### 查看日志

```bash
cd /opt/sellersprite

# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api       # API 日志
docker-compose logs -f redis     # Redis 日志
docker-compose logs -f postgres  # 数据库日志
docker-compose logs -f celery    # Celery 日志

# 导出日志到文件
docker-compose logs > logs.txt
```

### 更新代码

#### 更新流程

```bash
cd /opt/sellersprite

# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 验证
docker-compose ps
curl http://localhost:8000/health

# 5. 查看日志
docker-compose logs -f api
```

#### 设置自动更新

创建 `/opt/sellersprite/update.sh`：

```bash
#!/bin/bash
cd /opt/sellersprite
echo "[$(date)] 开始更新..." >> /var/log/sellersprite-update.log
git pull >> /var/log/sellersprite-update.log 2>&1
docker-compose build >> /var/log/sellersprite-update.log 2>&1
docker-compose up -d >> /var/log/sellersprite-update.log 2>&1
echo "[$(date)] 更新完成" >> /var/log/sellersprite-update.log
```

添加到 crontab（每天午夜自动更新）：

```bash
chmod +x /opt/sellersprite/update.sh

# 编辑 crontab
crontab -e

# 添加这一行
0 0 * * * /opt/sellersprite/update.sh
```

### 管理容器

```bash
# 查看容器状态
docker-compose ps

# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart api

# 停止服务
docker-compose stop

# 完全停止并删除容器
docker-compose down

# 重新启动
docker-compose up -d
```

### 备份数据

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U postgres sellersprite > backup_$(date +%Y%m%d).sql

# 备份 Redis 数据
docker cp sellersprite-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb

# 验证备份
ls -lh backup_*
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘空间
df -h

# 查看内存使用
free -h

# 查看进程
ps aux | grep docker
```

---

## 📝 常见操作

### 修改密码

```bash
# 1. 编辑 .env 文件
nano .env

# 2. 修改密码字段
# POSTGRES_PASSWORD=新密码
# REDIS_PASSWORD=新密码

# 3. 重启服务
docker-compose restart

# 注意：修改数据库密码后，容器内的连接字符串也需要更新
```

### 查看 API 文档

```bash
# 在浏览器中访问
http://103.53.81.226:8000/docs

# 或者从命令行查看
curl http://localhost:8000/docs | less
```

### 进入容器调试

```bash
# 进入 API 容器
docker-compose exec api bash

# 在容器内查看文件
ls -la
cat .env

# 运行 Python 命令
python -c "import app.config; print(app.config.settings)"

# 退出容器
exit
```

### 完全重置（谨慎！删除所有数据）

```bash
cd /opt/sellersprite

# 停止并删除容器及数据卷
docker-compose down -v

# 重新启动（重建所有内容）
docker-compose up -d
```

---

## 🆘 故障排查

### 常见问题

| 问题 | 症状 | 解决方案 |
|------|------|--------|
| Redis 连接失败 | `Connection refused` | `docker-compose logs redis` |
| API 无法启动 | `502 Bad Gateway` | `docker-compose logs api` |
| 数据库连接失败 | `FATAL: password authentication failed` | 检查 .env 文件中的密码 |
| 端口被占用 | `Port already in use` | 修改 docker-compose.yml 中的端口 |

### 检查清单

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 检查 Redis
docker-compose exec redis redis-cli ping

# 3. 检查数据库
docker-compose exec postgres psql -U postgres -c "\l"

# 4. 检查 API
curl http://localhost:8000/health

# 5. 查看系统资源
docker stats
free -h
df -h
```

---

## 📞 获取帮助

如果遇到问题，请收集以下信息：

```bash
# 收集诊断信息
cd /opt/sellersprite

# 1. 容器状态
docker-compose ps > diagnosis.txt

# 2. 错误日志
docker-compose logs api >> diagnosis.txt

# 3. 系统信息
uname -a >> diagnosis.txt
docker --version >> diagnosis.txt

# 4. 环境检查
cat .env.example >> diagnosis.txt

# 分享这个文件获取帮助
cat diagnosis.txt
```

---

**祝部署顺利！** 🚀

