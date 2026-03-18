#!/bin/bash

#==============================================================================
# GitHub 到 Debian 服务器的一键部署脚本
# 
# 使用方法:
#   1. 在服务器上运行: bash deploy-from-github.sh
#   2. 输入 GitHub 仓库 URL
#   3. 脚本会自动克隆、配置、并启动
#
# 需求:
#   - root 权限
#   - Debian/Ubuntu 系统
#   - 网络连接
#==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
INSTALL_DIR="/opt/sellersprite"
LOG_FILE="/var/log/github-deploy.log"

#==============================================================================
# 日志函数
#==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

#==============================================================================
# 基础检查
#==============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "请使用 root 权限运行此脚本"
        echo "使用方法: sudo bash deploy-from-github.sh"
        exit 1
    fi
}

print_banner() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo "              GitHub 到 Debian 的一键部署脚本"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo ""
}

#==============================================================================
# 交互式配置
#==============================================================================

read_github_url() {
    log_info "请输入 GitHub 仓库 URL"
    echo "示例: https://github.com/username/sellersprite"
    read -p "GitHub URL: " GITHUB_URL
    
    if [[ -z "$GITHUB_URL" ]]; then
        log_error "GitHub URL 不能为空"
        exit 1
    fi
    
    log_success "GitHub URL: $GITHUB_URL"
}

read_deploy_config() {
    echo ""
    log_info "请配置部署参数"
    echo ""
    
    read -p "安装目录 (默认: /opt/sellersprite): " INPUT_DIR
    INSTALL_DIR=${INPUT_DIR:-/opt/sellersprite}
    
    read -p "数据库密码 (默认: password): " DB_PASS
    DB_PASS=${DB_PASS:-password}
    
    read -p "Redis 密码 (留空表示无密码): " REDIS_PASS
    REDIS_PASS=${REDIS_PASS:-}
    
    log_success "配置完成"
    echo ""
    echo "部署配置:"
    echo "  - 安装目录: $INSTALL_DIR"
    echo "  - GitHub URL: $GITHUB_URL"
    echo "  - 数据库密码: ****"
    echo "  - Redis 密码: ${REDIS_PASS:-(无)}"
    echo ""
}

#==============================================================================
# 系统准备
#==============================================================================

install_prerequisites() {
    log_info "=================================================="
    log_info "安装系统依赖..."
    log_info "=================================================="
    
    apt update
    
    # 检查是否安装了 Git
    if ! command -v git &> /dev/null; then
        log_info "安装 Git..."
        apt install -y git
    fi
    
    # 检查是否安装了 Docker
    if ! command -v docker &> /dev/null; then
        log_info "安装 Docker..."
        apt install -y docker.io docker-compose
        systemctl start docker
        systemctl enable docker
    else
        log_success "Docker 已安装"
    fi
    
    # 检查是否安装了 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &>/dev/null; then
        log_info "安装 Docker Compose..."
        apt install -y docker-compose
    else
        log_success "Docker Compose 已安装"
    fi
    
    # 检查 curl
    if ! command -v curl &> /dev/null; then
        log_info "安装 curl..."
        apt install -y curl
    fi
    
    log_success "系统依赖安装完成"
    echo ""
}

#==============================================================================
# 克隆仓库
#==============================================================================

clone_repository() {
    log_info "=================================================="
    log_info "克隆 GitHub 仓库..."
    log_info "=================================================="
    
    # 检查目录是否存在
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "目录已存在: $INSTALL_DIR"
        read -p "是否覆盖? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "操作取消"
            exit 1
        fi
        rm -rf "$INSTALL_DIR"
    fi
    
    # 创建目录
    mkdir -p "$INSTALL_DIR"
    
    # 克隆仓库
    log_info "正在从 $GITHUB_URL 克隆..."
    if git clone "$GITHUB_URL" "$INSTALL_DIR"; then
        log_success "仓库克隆成功"
    else
        log_error "克隆失败，请检查 URL 和网络连接"
        exit 1
    fi
    
    echo ""
}

#==============================================================================
# 环境配置
#==============================================================================

setup_env() {
    log_info "=================================================="
    log_info "配置环境变量..."
    log_info "=================================================="
    
    cd "$INSTALL_DIR"
    
    # 检查是否存在 .env.example
    if [[ ! -f .env.example ]]; then
        log_warning ".env.example 不存在，跳过环境配置"
        return
    fi
    
    # 复制 .env 文件
    cp .env.example .env
    
    # 更新密码（如果存在相关变量）
    if grep -q "POSTGRES_PASSWORD" .env; then
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DB_PASS/" .env
    fi
    
    if grep -q "REDIS_PASSWORD" .env && [[ -n "$REDIS_PASS" ]]; then
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASS/" .env
    fi
    
    log_success "环境变量配置完成"
    
    # 显示 .env 内容（敏感信息隐藏）
    echo ""
    log_info ".env 文件已生成，关键配置："
    grep -E "^[^#]" .env | head -15 || true
    echo ""
}

#==============================================================================
# Docker 部署
#==============================================================================

deploy_docker() {
    log_info "=================================================="
    log_info "Docker Compose 部署..."
    log_info "=================================================="
    
    cd "$INSTALL_DIR"
    
    # 检查是否存在 docker-compose.yml
    if [[ ! -f docker-compose.yml ]]; then
        log_error "docker-compose.yml 不存在"
        log_info "请确保仓库中包含 docker-compose.yml 文件"
        exit 1
    fi
    
    # 构建并启动容器
    log_info "正在构建 Docker 镜像..."
    if docker-compose build; then
        log_success "Docker 镜像构建成功"
    else
        log_error "Docker 镜像构建失败"
        exit 1
    fi
    
    log_info "正在启动 Docker 容器..."
    if docker-compose up -d; then
        log_success "Docker 容器启动成功"
    else
        log_error "Docker 容器启动失败"
        docker-compose logs
        exit 1
    fi
    
    # 等待服务就绪
    log_info "等待服务就绪..."
    sleep 5
    
    echo ""
    log_success "Docker 部署完成"
    echo ""
}

#==============================================================================
# 验证部署
#==============================================================================

verify_deployment() {
    log_info "=================================================="
    log_info "验证部署..."
    log_info "=================================================="
    
    cd "$INSTALL_DIR"
    
    echo ""
    echo "容器状态:"
    docker-compose ps
    
    echo ""
    echo "等待 API 启动..."
    sleep 5
    
    # 测试 API 连接
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "API 健康检查通过 ✓"
    else
        log_warning "API 未就绪，可能需要更多时间..."
    fi
    
    # 显示重要信息
    echo ""
    log_success "部署完成！"
    echo ""
}

#==============================================================================
# 显示部署信息
#==============================================================================

show_deployment_info() {
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo "                    部署成功！"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📋 部署信息:"
    echo "   - 安装目录: $INSTALL_DIR"
    echo "   - GitHub 源: $GITHUB_URL"
    echo "   - 部署方式: Docker Compose"
    echo ""
    echo "🌐 访问地址:"
    echo "   - API 文档: http://103.53.81.226:8000/docs"
    echo "   - API 健康: http://103.53.81.226:8000/health"
    echo ""
    echo "📝 常用命令:"
    echo "   cd $INSTALL_DIR"
    echo "   docker-compose ps           # 查看容器状态"
    echo "   docker-compose logs -f      # 查看日志"
    echo "   docker-compose restart      # 重启服务"
    echo "   docker-compose down         # 停止服务"
    echo ""
    echo "🔄 更新代码:"
    echo "   cd $INSTALL_DIR"
    echo "   git pull"
    echo "   docker-compose up -d --build"
    echo ""
    echo "📊 部署日志:"
    echo "   tail -f $LOG_FILE"
    echo ""
    echo -e "${YELLOW}⚠️  重要提示:${NC}"
    echo "   1. .env 文件包含敏感信息，请妥善保管"
    echo "   2. 生产环境建议配置 SSL 证书"
    echo "   3. 定期备份数据库和 Redis 数据"
    echo ""
}

#==============================================================================
# 主函数
#==============================================================================

main() {
    print_banner
    check_root
    
    # 交互式输入
    read_github_url
    read_deploy_config
    
    # 确认
    echo ""
    read -p "确认开始部署? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "部署已取消"
        exit 1
    fi
    
    echo ""
    
    # 执行部署
    install_prerequisites
    clone_repository
    setup_env
    deploy_docker
    verify_deployment
    show_deployment_info
    
    log_success "所有步骤完成！"
}

main "$@"
