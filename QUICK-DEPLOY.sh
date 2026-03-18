#!/bin/bash

#==============================================================================
# GitHub 部署快速参考 - 一句话部署
# 
# 这个脚本是 deploy-from-github.sh 的简化版，用于快速部署
#==============================================================================

# 全局设置
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# 快速部署指南
# ============================================================================

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════╗
║                     GitHub 到 Debian 部署快速指南                        ║
╚══════════════════════════════════════════════════════════════════════════╝

📝 3 步快速部署：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
第 1 步：上传到 GitHub（本地执行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ cd d:/App/sellersprite
$ git init
$ git add .
$ git commit -m "Initial commit"
$ git remote add origin https://github.com/你的用户名/sellersprite.git
$ git push -u origin main

💡 提示：如果没有 GitHub 账户，请先注册：https://github.com/signup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
第 2 步：登录服务器（服务器执行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ ssh root@103.53.81.226

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
第 3 步：运行部署脚本（服务器执行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ bash <(curl -sL https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh)

或者分步：

$ curl -o deploy.sh https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh
$ sudo bash deploy.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 部署完成后：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

访问 API 文档：http://103.53.81.226:8000/docs

常用命令：
  查看状态：         docker-compose ps
  查看日志：         docker-compose logs -f
  重启服务：         docker-compose restart
  停止服务：         docker-compose down

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 后续更新代码：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ cd /opt/sellersprite
$ git pull
$ docker-compose up -d --build

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 手动部署（如果自动脚本失败）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ ssh root@103.53.81.226

# 安装必要软件
$ apt update
$ apt install -y docker.io docker-compose git curl

# 启动 Docker
$ systemctl start docker
$ systemctl enable docker

# 克隆项目
$ cd /opt
$ git clone https://github.com/你的用户名/sellersprite.git
$ cd sellersprite

# 配置环境
$ cp .env.example .env

# 启动服务
$ docker-compose up -d

# 验证
$ docker-compose ps
$ curl http://localhost:8000/health

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆘 故障排查：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

查看日志：
$ docker-compose logs api

Redis 连接失败：
$ docker-compose logs redis
$ docker-compose exec redis redis-cli ping

容器状态：
$ docker-compose ps

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 完整文档：参考 GITHUB-DEPLOYMENT.md 和 DEPLOYMENT.md

💡 需要帮助？请提供：
   1. 具体错误信息
   2. docker-compose ps 的输出
   3. docker-compose logs 的输出

祝部署顺利！🚀

EOF
