# SellerSprite Clone - 部署指南

## 🚀 快速开始

有两种部署方式可选，**强烈推荐使用 Docker Compose**（更可靠、更简单）。

---

## 📦 方案 1：Docker Compose 部署（推荐）⭐⭐⭐

### 前置要求

- Docker（版本 20.10+）
- Docker Compose（版本 1.29+）
- 至少 4GB 内存
- 10GB 磁盘空间

### 安装步骤

#### 1. 检查 Docker 和 Docker Compose

```bash
# 检查 Docker
docker --version
# 输出示例: Docker version 24.0.0

# 检查 Docker Compose
docker compose version
# 输出示例: Docker Compose version 2.20.0

# 如果未安装，参考官方文档安装
# https://docs.docker.com/install/
# https://docs.docker.com/compose/install/
```

#### 2. 准备项目文件

```bash
# 克隆或上传项目到服务器
cd /opt
git clone <your-repo> sellersprite
cd sellersprite

# 或直接上传文件到 /opt/sellersprite
scp -r ./backend root@103.53.81.226:/opt/sellersprite/
scp -r ./frontend root@103.53.81.226:/opt/sellersprite/
scp docker-compose.yml root@103.53.81.226:/opt/sellersprite/
```

#### 3. 配置环境变量

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑 .env 文件，根据需要修改配置
nano .env

# 关键配置项：
# - POSTGRES_PASSWORD: 数据库密码（改为强密码）
# - REDIS_PASSWORD: Redis 密码（可选，生产环境建议设置）
# - LOG_LEVEL: 日志级别（开发用 DEBUG，生产用 INFO）
```

#### 4. 启动容器

```bash
# 创建并启动所有容器
docker compose up -d

# 查看输出（可选）
docker compose logs -f
```

#### 5. 验证部署

```bash
# 查看所有容器状态
docker compose ps

# 测试 API 连接
curl http://localhost:8000/health
# 应该返回: {"status": "healthy"}

# 测试 Redis 连接
docker compose exec redis redis-cli ping
# 应该返回: PONG

# 查看 API 文档
# 在浏览器中打开: http://<server-ip>:8000/docs
```

#### 6. 初始化数据库（首次部署）

```bash
# 进入 API 容器
docker compose exec api bash

# 在容器内运行初始化脚本
python init_db.py

# 退出容器
exit
```

### 常用命令

```bash
# 查看服务日志
docker compose logs -f api          # API 日志
docker compose logs -f celery       # Celery 日志
docker compose logs -f redis        # Redis 日志

# 重启服务
docker compose restart api          # 重启 API
docker compose restart celery       # 重启 Celery
docker compose restart redis        # 重启 Redis

# 停止服务
docker compose down                 # 停止并移除容器
docker compose down -v              # 停止并移除容器及数据

# 更新代码
git pull
docker compose up -d --build        # 重建并启动
```

### 故障排查

#### Redis 连接失败

```bash
# 检查 Redis 状态
docker compose ps
# redis 容器应该显示为 "healthy" 状态

# 查看 Redis 日志
docker compose logs redis

# 测试 Redis 连接
docker compose exec redis redis-cli ping

# 重启 Redis
docker compose restart redis
```

#### API 无法启动

```bash
# 查看详细日志
docker compose logs api -f

# 检查文件权限
docker compose exec api ls -la

# 重建镜像
docker compose up -d --build
```

#### 端口被占用

```bash
# 检查端口占用
lsof -i :8000
lsof -i :5432
lsof -i :6379

# 修改 docker-compose.yml 中的端口
# 例如: "8001:8000" 改为使用 8001 端口
```

---

## 🔧 方案 2：传统 systemd 部署

### 前置要求

- Ubuntu 20.04+ 或 Debian 11+
- root 权限
- Python 3.11+
- PostgreSQL 15+
- Redis 7.0+

### 安装步骤

#### 1. 下载改进的安装脚本

```bash
# 使用改进的脚本
cd /opt
git clone <your-repo> sellersprite
cd sellersprite/backend

chmod +x install-improved.sh
```

#### 2. 运行安装脚本

```bash
# 以 root 权限运行
sudo bash install-improved.sh

# 脚本会引导你配置：
# - 数据库主机、端口、用户名、密码
# - Redis 主机、端口
# - 安装目录
```

#### 3. 验证安装

```bash
# 查看 Redis 状态
sudo systemctl status redis-server

# 查看 API 状态
sudo systemctl status sellersprite-api

# 查看 Celery 状态
sudo systemctl status sellersprite-celery

# 测试 Redis 连接
redis-cli ping
# 应该返回: PONG

# 查看日志
sudo journalctl -u sellersprite-api -f
```

### 常用命令

```bash
# 查看服务状态
sudo systemctl status redis-server
sudo systemctl status sellersprite-api
sudo systemctl status sellersprite-celery

# 启动/停止/重启服务
sudo systemctl start sellersprite-api
sudo systemctl stop sellersprite-api
sudo systemctl restart sellersprite-api

# 查看日志
sudo journalctl -u sellersprite-api -f      # 实时日志
sudo journalctl -u sellersprite-api -n 100  # 最后 100 行

# 查看安装日志
tail -f /var/log/sellersprite-install.log
```

### 故障排查

#### Redis 连接失败

```bash
# 检查 Redis 状态和详细错误
sudo systemctl status redis-server -l

# 查看 Redis 日志
sudo tail -f /var/log/redis/redis-server.log

# 诊断 Redis
redis-cli ping           # 测试连接
redis-cli info          # 查看信息
redis-cli config get *  # 查看配置

# 修复 Redis（如果出现权限错误）
sudo chown -R redis:redis /var/lib/redis
sudo chown -R redis:redis /var/log/redis
sudo systemctl restart redis-server
```

#### API 无法连接

```bash
# 查看 API 日志
sudo journalctl -u sellersprite-api -f

# 检查端口
sudo netstat -tlnp | grep 8000
# 或
sudo ss -tlnp | grep 8000

# 如果端口被占用，修改 .env 中的 API_PORT

# 重启 API
sudo systemctl restart sellersprite-api
```

---

## 🔒 生产环境部署

### 反向代理配置（Nginx）

创建 `/etc/nginx/sites-available/sellersprite`：

```nginx
upstream sellersprite_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向 HTTPS（可选）
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    # 代理配置
    location / {
        proxy_pass http://sellersprite_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API 文档
    location /docs {
        proxy_pass http://sellersprite_api/docs;
    }

    location /redoc {
        proxy_pass http://sellersprite_api/redoc;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/sellersprite \
    /etc/nginx/sites-enabled/sellersprite

sudo nginx -t
sudo systemctl restart nginx
```

### 监控和维护

```bash
# 定期检查磁盘空间
df -h

# 检查数据库备份
ls -la /backup/

# 监控 Redis 内存使用
redis-cli info memory

# 监控进程资源
top
htop  # 如果安装了的话
```

### 备份策略

```bash
# 备份 PostgreSQL
sudo -u postgres pg_dump sellersprite > /backup/sellersprite_$(date +%Y%m%d).sql

# 备份 Redis 数据
cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb

# 设置自动备份（cron）
# 编辑: sudo crontab -e
# 添加：0 2 * * * /opt/sellersprite/backup.sh
```

---

## 📊 监控和日志

### 日志位置

**Docker Compose 方式：**
```bash
docker compose logs <service-name>
```

**systemd 方式：**
- API 日志: `journalctl -u sellersprite-api`
- Celery 日志: `journalctl -u sellersprite-celery`
- Redis 日志: `/var/log/redis/redis-server.log`
- 安装日志: `/var/log/sellersprite-install.log`

### 性能监控

```bash
# Redis 内存和连接数
redis-cli info memory
redis-cli info clients

# PostgreSQL 连接
sudo -u postgres psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# CPU 和内存使用
top
free -h
```

---

## ✅ 部署检查清单

- [ ] Docker / systemd 依赖已安装
- [ ] 环境变量已配置（.env 文件）
- [ ] Redis 已成功启动并通过健康检查
- [ ] PostgreSQL 已启动并数据库已创建
- [ ] API 服务已启动（端口 8000 监听）
- [ ] Celery Worker 已启动
- [ ] API 文档可访问（http://server:8000/docs）
- [ ] Redis 连接测试通过（redis-cli ping）
- [ ] 防火墙已允许所需端口
- [ ] SSL 证书已配置（生产环境）

---

## 📞 常见问题

**Q: Redis 连接失败怎么办？**
A: 查看上面的"Redis 连接失败"故障排查部分。常见原因是 Redis 服务未启动或配置错误。

**Q: 如何更新代码？**
A: 
- Docker: `git pull && docker compose up -d --build`
- systemd: `cd /opt/sellersprite && git pull && systemctl restart sellersprite-api`

**Q: 如何扩展 Celery Worker？**
A: 
- Docker: 在 docker-compose.yml 中添加多个 `celery` 服务
- systemd: 创建多个 systemd 服务实例

**Q: 如何配置 SSL？**
A: 使用 Let's Encrypt 的免费证书，参考 Nginx 配置部分。

---

## 📖 更多资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Docker 文档](https://docs.docker.com/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [Redis 文档](https://redis.io/documentation)
- [Celery 文档](https://docs.celeryproject.io/)

