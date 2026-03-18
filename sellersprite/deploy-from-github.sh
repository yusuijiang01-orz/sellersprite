#!/bin/bash

# ============================================================================
# SellerSprite 从 GitHub 一键部署脚本 - Debian/Ubuntu 服务器
# ============================================================================
# 用法: bash deploy-from-github.sh [仓库URL] [部署目录] [分支]
# 示例: bash deploy-from-github.sh https://github.com/yusuijiang01-orz/sellersprite.git /opt/sellersprite main
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# 1. 前置检查
# ============================================================================
log_info "开始前置环境检查..."

if [[ $EUID -ne 0 ]]; then
   log_error "此脚本必须以 root 身份运行"
   echo "请使用: sudo bash $0"
   exit 1
fi

# 检查必要命令
commands=("git" "docker" "docker-compose")
for cmd in "${commands[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        log_warn "$cmd 未安装，尝试自动安装..."
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y "$cmd"
        else
            log_error "$cmd 未安装且无法自动安装"
            exit 1
        fi
    fi
done

log_success "环境检查完成"

# ============================================================================
# 2. 配置变量
# ============================================================================
log_info "配置部署参数..."

REPO_URL="${1:-https://github.com/yusuijiang01-orz/sellersprite.git}"
DEPLOY_DIR="${2:-/opt/sellersprite}"
BRANCH="${3:-main}"

log_info "仓库地址: $REPO_URL"
log_info "部署目录: $DEPLOY_DIR"
log_info "分支名: $BRANCH"

# ============================================================================
# 3. 准备部署目录
# ============================================================================
log_info "准备部署目录..."

if [ -d "$DEPLOY_DIR" ]; then
    log_warn "目录 $DEPLOY_DIR 已存在"
    read -p "是否删除并重新部署? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$DEPLOY_DIR"
        log_info "已删除旧目录"
    else
        log_info "保留现有目录，进行更新..."
    fi
fi

mkdir -p "$DEPLOY_DIR"
log_success "部署目录准备完成"

# ============================================================================
# 4. 克隆或更新仓库
# ============================================================================
log_info "处理 GitHub 仓库..."

if [ -d "$DEPLOY_DIR/.git" ]; then
    log_info "仓库已存在，执行更新..."
    cd "$DEPLOY_DIR"
    git pull origin "$BRANCH"
    log_success "仓库更新完成"
else
    log_info "克隆 GitHub 仓库..."
    if git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DEPLOY_DIR"; then
        log_success "仓库克隆完成"
    else
        log_error "克隆失败，请检查仓库地址和网络连接"
        exit 1
    fi
fi

# 进入项目目录
cd "$DEPLOY_DIR"

# 进入 sellersprite 子目录（如果存在）
if [ -d "sellersprite" ]; then
    cd sellersprite
    log_info "进入 sellersprite 子目录"
fi

WORK_DIR=$(pwd)
log_success "工作目录: $WORK_DIR"

# ============================================================================
# 5. 环境配置
# ============================================================================
log_info "配置环境变量..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success ".env 文件已生成"
        
        log_warn "请编辑 .env 文件并设置实际的密码和配置:"
        echo "   nano .env"
        echo ""
        log_info "关键配置项:"
        echo "   POSTGRES_PASSWORD=your-secure-password"
        echo "   REDIS_PASSWORD=your-redis-password"
        echo "   API_SECRET_KEY=your-secret-key-32-chars-minimum"
        echo ""
        read -p "配置完成后按 Enter 继续..."
    else
        log_error ".env.example 不存在，无法生成 .env 文件"
        log_info "请手动创建 .env 文件"
        exit 1
    fi
else
    log_success ".env 文件已存在"
fi

# ============================================================================
# 6. 启动 Docker 服务
# ============================================================================
log_info "启动 Docker 服务..."

# 检查 Docker 守护程序
if ! docker ps &>/dev/null; then
    log_info "启动 Docker 守护程序..."
    systemctl start docker || service docker start
    sleep 2
fi

# 启用 Docker 自启动
systemctl enable docker 2>/dev/null || true

log_success "Docker 已就绪"

# ============================================================================
# 7. 构建并启动容器
# ============================================================================
log_info "构建并启动容器..."

# 拉取最新镜像
log_info "拉取最新镜像..."
docker-compose pull 2>/dev/null || log_warn "镜像拉取失败，尝试本地构建"

# 启动容器
if docker-compose up -d; then
    log_success "容器启动成功"
else
    log_error "容器启动失败"
    log_info "查看详细日志:"
    docker-compose logs
    exit 1
fi

# ============================================================================
# 8. 等待服务就绪
# ============================================================================
log_info "等待服务启动..."

sleep 15

# 检查 API 是否就绪
max_attempts=40
attempt=0
api_ready=false

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API 已就绪"
        api_ready=true
        break
    fi
    attempt=$((attempt + 1))
    printf "${BLUE}ℹ️  等待 API 就绪... ($attempt/$max_attempts)${NC}\r"
    sleep 1
done

echo ""
if [ "$api_ready" = false ]; then
    log_warn "API 可能未完全启动，请检查日志"
    log_info "运行诊断: docker-compose logs api"
fi

# ============================================================================
# 9. 验证部署
# ============================================================================
log_info "验证部署状态..."

echo ""
echo "════════════════════════════════════════"
echo "         容器状态"
echo "════════════════════════════════════════"
docker-compose ps

echo ""
echo "════════════════════════════════════════"
echo "         服务可访问性检查"
echo "════════════════════════════════════════"

# 测试 API
echo -n "API 服务... "
if curl -s http://localhost:8000/health | grep -q "healthy" 2>/dev/null; then
    log_success "正常"
    HEALTH_STATUS="✅ API (http://localhost:8000)"
else
    log_warn "异常"
    HEALTH_STATUS="⚠️  API (http://localhost:8000)"
fi

# 测试 Redis
echo -n "Redis 服务... "
if docker-compose exec -T redis redis-cli ping &>/dev/null; then
    log_success "正常"
else
    log_warn "异常"
fi

# 测试数据库
echo -n "数据库连接... "
if docker-compose exec -T api python -c "from app.database import engine; print('OK')" &>/dev/null 2>&1; then
    log_success "正常"
else
    log_warn "异常，可能需要运行初始化"
    log_info "运行初始化: docker-compose exec api python init_db.py"
fi

# ============================================================================
# 10. 部署完成
# ============================================================================
echo ""
echo "════════════════════════════════════════"
log_success "部署完成！"
echo "════════════════════════════════════════"
echo ""

SERVER_IP=$(hostname -I | awk '{print $1}')
log_success "SellerSprite 已成功部署"
echo ""
echo "📍 访问地址:"
echo "   API 文档:    http://$SERVER_IP:8000/docs"
echo "   健康检查:    http://$SERVER_IP:8000/health"
echo ""
echo "🔧 常用命令:"
echo "   查看日志:     docker-compose logs -f api"
echo "   查看所有日志: docker-compose logs"
echo "   重启服务:     docker-compose restart"
echo "   停止服务:     docker-compose down"
echo "   启动服务:     docker-compose up -d"
echo "   进入容器:     docker-compose exec api bash"
echo ""
echo "📚 关键文件位置:"
echo "   工作目录:     $WORK_DIR"
echo "   环境配置:     $WORK_DIR/.env"
echo "   日志文件:     通过 docker-compose logs 查看"
echo ""
echo "❓ 遇到问题? 查看文档:"
echo "   部署指南:     GITHUB-DEPLOYMENT.md"
echo "   故障排查:     DEPLOYMENT_FIX.md"
echo "   快速开始:     QUICK-START.md"
echo ""
if [ -f "redis-diagnosis.sh" ]; then
    echo "🔍 运行诊断脚本:"
    echo "   bash redis-diagnosis.sh"
    echo ""
fi
echo "✨ 部署完成，祝你使用愉快！"
echo ""
