#!/bin/bash
# ============================================================================
# SellerSprite 快速部署参考卡
# ============================================================================

# 🔴 问题
# bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/blob/main/...)
# /dev/fd/63: line 1: 404:: command not found

# ============================================================================
# ✅ 解决方案 1：使用正确的 URL（推荐）
# ============================================================================

bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh)

# ============================================================================
# ✅ 解决方案 2：分步手动部署
# ============================================================================

# 第 1 步：登录服务器
ssh root@103.53.81.226

# 第 2 步：安装依赖
sudo apt update && sudo apt install -y git docker.io docker-compose curl

# 第 3 步：克隆项目
cd /opt && git clone https://github.com/yusuijiang01-orz/sellersprite.git
cd sellersprite/sellersprite

# 第 4 步：配置环境
cp .env.example .env
# 编辑 .env 文件，设置密码和配置
nano .env

# 第 5 步：启动服务
docker-compose up -d

# 第 6 步：等待服务启动
sleep 15

# 第 7 步：验证部署
docker-compose ps                    # 查看容器状态
curl http://localhost:8000/health    # 测试 API
docker-compose logs api              # 查看日志

# ============================================================================
# ✅ 关键 URL 对比
# ============================================================================

# ❌ 错误（会导致 404 错误）
# https://raw.githubusercontent.com/用户/仓库/blob/main/路径/文件.sh

# ✅ 正确
# https://raw.githubusercontent.com/用户/仓库/main/路径/文件.sh

# ============================================================================
# 🔍 常用命令
# ============================================================================

# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f api          # 实时日志
docker-compose logs --tail=100      # 最后 100 行

# 重启服务
docker-compose restart
docker-compose restart api

# 停止/启动
docker-compose down                 # 停止所有服务
docker-compose up -d                # 启动所有服务

# 进入容器
docker-compose exec api bash        # 进入 API 容器
docker-compose exec redis bash      # 进入 Redis 容器

# 测试连接
curl http://localhost:8000/health   # 测试 API
docker-compose exec redis redis-cli ping  # 测试 Redis

# ============================================================================
# 📍 访问地址
# ============================================================================

# API 文档：      http://103.53.81.226:8000/docs
# 健康检查：      http://103.53.81.226:8000/health
# 工作目录：      /opt/sellersprite/sellersprite
# 环境配置：      /opt/sellersprite/sellersprite/.env

# ============================================================================
# 🆘 故障排查
# ============================================================================

# 如果 API 无法连接
docker-compose logs api
docker-compose restart api

# 如果 Redis 无法连接
docker-compose logs redis
docker-compose restart redis

# 如果数据库无法连接
docker-compose logs postgres
docker-compose restart postgres

# 完全重置（慎用）
docker-compose down -v
docker-compose up -d

# ============================================================================
# 📚 相关文档
# ============================================================================

# DEPLOYMENT-TROUBLESHOOTING.md   - 故障排查完整指南
# QUICK-DEPLOYMENT-FIX.md         - 快速修复指南
# DEPLOYMENT.md                   - 完整部署指南
# GITHUB-DEPLOYMENT.md            - GitHub 部署指南
# QUICK-START.md                  - 快速开始

# ============================================================================
# 💡 关键提示
# ============================================================================

# 1. 确保使用 /raw/main/ 而不是 /blob/main/
# 2. 所有容器都应该显示为 "Up" 状态
# 3. API 应该返回 200 状态码和 {"status": "healthy"}
# 4. 修改 .env 中的密码为强密码
# 5. 定期检查日志和容器状态

# ============================================================================
