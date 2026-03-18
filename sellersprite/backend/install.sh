#!/bin/bash

#==============================================================================
# SellerSprite Clone - 一键安装脚本
# 
# 使用方法:
#   bash <(curl -sL https://raw.githubusercontent.com/YOUR_USERNAME/sellersprite-clone/main/install.sh)
#
# 或者下载后执行:
#   chmod +x install.sh && ./install.sh
#==============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="sellersprite-clone"
GIT_REPO=""
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_USER="www-data"
PYTHON_VERSION="3.11"

#==============================================================================
# 函数定义
#==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║       SellerSprite Clone - 一键安装脚本                        ║"
    echo "║       亚马逊选品与数据分析工具                                  ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
}

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "请使用 root 用户运行此脚本"
        log_info "使用方法: sudo bash install.sh"
        exit 1
    fi
}

# 检测操作系统
check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi

    if [[ "$OS" != "debian" && "$OS" != "ubuntu" && "$OS" != "raspbian" ]]; then
        log_warning "检测到操作系统: $OS"
        log_warning "此脚本主要针对 Debian/Ubuntu 设计，其他系统可能需要手动调整"
    fi
    
    log_info "检测到操作系统: $OS $VER"
}

# 读取配置
read_config() {
    print_banner
    
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo "                      配置信息"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Git 仓库地址
    read -p "Git 仓库地址 (留空使用当前目录): " GIT_REPO
    
    # 安装目录
    read -p "安装目录 (默认: /opt/sellersprite-clone): " INPUT_INSTALL_DIR
    INSTALL_DIR=${INPUT_INSTALL_DIR:-/opt/sellersprite-clone}
    
    # 数据库配置
    echo ""
    echo "📦 数据库配置"
    read -p "数据库主机 (默认: localhost): " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
    
    read -p "数据库端口 (默认: 5432): " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    
    read -p "数据库名称 (默认: sellersprite): " DB_NAME
    DB_NAME=${DB_NAME:-sellersprite}
    
    read -p "数据库用户名 (默认: selleruser): " DB_USER
    DB_USER=${DB_USER:-selleruser}
    
    while [[ -z "$DB_PASS" ]]; do
        read -s -p "数据库密码: " DB_PASS
        echo ""
        if [[ -z "$DB_PASS" ]]; then
            log_warning "密码不能为空"
        fi
    done
    
    # Redis 配置
    echo ""
    echo "📦 Redis 配置"
    read -p "Redis 主机 (默认: localhost): " REDIS_HOST
    REDIS_HOST=${REDIS_HOST:-localhost}
    
    read -p "Redis 端口 (默认: 6379): " REDIS_PORT
    REDIS_PORT=${REDIS_PORT:-6379}
    
    # 管理员配置
    echo ""
    echo "👤 管理员配置"
    read -p "API 密钥 (留空自动生成): " API_KEY
    if [[ -z "$API_KEY" ]]; then
        API_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 64 | head -n 1)
    fi
    
    echo ""
    log_info "配置完成，开始安装..."
    echo ""
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    # 更新 apt 源
    apt update
    
    # 安装基础工具
    apt install -y \
        curl \
        wget \
        git \
        vim \
        build-essential \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        uuid-runtime
    
    # 安装 PostgreSQL
    if ! command -v psql &> /dev/null; then
        log_info "安装 PostgreSQL..."
        apt install -y postgresql postgresql-contrib
    fi
    
    # 安装 Redis
    if ! command -v redis-server &> /dev/null; then
        log_info "安装 Redis..."
        apt install -y redis-server
    fi
    
    # 安装 Python
    if ! command -v python3 &> /dev/null; then
        log_info "安装 Python..."
        apt install -y python3 python3-venv python3-pip
    fi
    
    # 安装 Playwright 浏览器依赖
    log_info "安装 Playwright 浏览器依赖..."
    apt install -y \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        libxshmfence1 \
        libdbus-1-3
    
    # 安装 Chrome/Chromium
    if ! command -v chromium &> /dev/null; then
        log_info "安装 Chromium..."
        apt install -y chromium chromium-driver
    fi
    
    log_success "系统依赖安装完成"
}

# 配置数据库
setup_database() {
    log_info "配置数据库..."
    
    # 启动 PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # 等待 PostgreSQL 启动
    sleep 2
    
    # 创建用户和数据库
    su - postgres -c "psql -c \"SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'\"" | grep -q 1 || \
        su - postgres -c "psql -c \"CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';\"" && \
        su - postgres -c "psql -c \"CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};\"" && \
        log_success "数据库 ${DB_NAME} 创建完成" || \
        log_warning "数据库可能已存在"
    
    log_success "数据库配置完成"
}

# 配置 Redis
setup_redis() {
    log_info "配置 Redis..."
    
    # 启动 Redis
    systemctl start redis-server
    systemctl enable redis-server
    
    log_success "Redis 配置完成"
}

# 克隆/更新代码
setup_code() {
    log_info "配置代码..."
    
    # 创建安装目录
    mkdir -p ${INSTALL_DIR}
    
    if [[ -n "$GIT_REPO" ]]; then
        # 克隆仓库
        if [[ -d "${INSTALL_DIR}/.git" ]]; then
            log_info "更新代码..."
            cd ${INSTALL_DIR}
            git pull
        else
            log_info "克隆代码仓库..."
            git clone ${GIT_REPO} ${INSTALL_DIR}
        fi
    else
        # 使用当前目录的代码
        log_info "复制当前目录代码..."
        cp -r ${SCRIPT_DIR}/* ${INSTALL_DIR}/
    fi
    
    # 创建 www-data 用户（如果不存在）
    if ! id "${SERVICE_USER}" &>/dev/null; then
        useradd -r -s /bin/false ${SERVICE_USER}
    fi
    
    # 设置权限
    chown -R ${SERVICE_USER}:${SERVICE_USER} ${INSTALL_DIR}
    
    log_success "代码配置完成"
}

# 配置 Python 环境
setup_python() {
    log_info "配置 Python 环境..."
    
    cd ${INSTALL_DIR}
    
    # 创建虚拟环境
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    # 安装 Playwright 浏览器
    playwright install chromium
    
    # 退出虚拟环境
    deactivate
    
    log_success "Python 环境配置完成"
}

# 配置环境变量
setup_env() {
    log_info "配置环境变量..."
    
    cd ${INSTALL_DIR}
    
    # 创建 .env 文件
    cat > .env << EOF
# ===========================================
# SellerSprite Clone - 环境配置
# ===========================================

# 数据库配置
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DATABASE_URL_ASYNC=postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis 配置
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
CELERY_BROKER_URL=redis://${REDIS_HOST}:${REDIS_PORT}/1
CELERY_RESULT_BACKEND=redis://${REDIS_HOST}:${REDIS_PORT}/2

# 爬虫配置
MIN_REQUEST_DELAY=2
MAX_REQUEST_DELAY=5

# 亚马逊配置
AMAZON_MARKETPLACE=US
AMAZON_BASE_URL=https://www.amazon.com

# 缓存配置
CACHE_TTL_SECONDS=21600

# 日志
LOG_LEVEL=INFO

# API 密钥
API_KEY=${API_KEY}
EOF
    
    # 设置权限
    chmod 600 .env
    chown ${SERVICE_USER}:${SERVICE_USER} .env
    
    log_success "环境变量配置完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    cd ${INSTALL_DIR}
    source venv/bin/activate
    
    python init_db.py
    
    deactivate
    
    log_success "数据库初始化完成"
}

# 创建 Systemd 服务
setup_services() {
    log_info "创建系统服务..."
    
    # API 服务
    cat > /etc/systemd/system/sellersprite-api.service << 'EOF'
[Unit]
Description=SellerSprite API
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/sellersprite-clone
Environment="PATH=/opt/sellersprite-clone/venv/bin"
ExecStart=/opt/sellersprite-clone/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Celery Worker 服务
    cat > /etc/systemd/system/sellersprite-celery.service << 'EOF'
[Unit]
Description=SellerSprite Celery Worker
After=network.target redis-server.service
Wants=redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/sellersprite-clone
Environment="PATH=/opt/sellersprite-clone/venv/bin"
ExecStart=/opt/sellersprite-clone/venv/bin/celery -A app.celery_app worker --loglevel=info --pool=solo
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载 systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable sellersprite-api
    systemctl enable sellersprite-celery
    
    log_success "系统服务创建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动 API
    systemctl start sellersprite-api
    sleep 2
    
    # 启动 Celery
    systemctl start sellersprite-celery
    
    # 检查状态
    if systemctl is-active --quiet sellersprite-api; then
        log_success "API 服务已启动"
    else
        log_error "API 服务启动失败"
        journalctl -u sellersprite-api --no-pager -n 20
    fi
    
    if systemctl is-active --quiet sellersprite-celery; then
        log_success "Celery 服务已启动"
    else
        log_warning "Celery 服务启动失败（可能需要等待 Redis）"
    fi
    
    log_success "服务启动完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    # 检查 ufw 是否安装
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw allow 22/tcp     # SSH
        ufw allow 8000/tcp   # API
        ufw allow 80/tcp     # HTTP
        ufw allow 443/tcp    # HTTPS
        log_success "防火墙配置完成"
    else
        log_warning "UFW 未安装，跳过防火墙配置"
    fi
}

# 显示安装结果
show_result() {
    print_banner
    
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo "                      安装完成!"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📋 服务状态:"
    echo "   API:      $(systemctl is-active sellersprite-api)"
    echo "   Celery:   $(systemctl is-active sellersprite-celery)"
    echo ""
    echo "📋 访问地址:"
    echo "   API 文档:    http://localhost:8000/docs"
    echo "   健康检查:    http://localhost:8000/health"
    echo ""
    echo "📋 常用命令:"
    echo "   查看日志:    journalctl -u sellersprite-api -f"
    echo "   重启服务:    systemctl restart sellersprite-api"
    echo "   停止服务:    systemctl stop sellersprite-api"
    echo ""
    echo "📋 安装目录: ${INSTALL_DIR}"
    echo ""
    echo -e "${YELLOW}⚠️  重要提示:${NC}"
    echo "   1. 请确保端口 8000 已开放"
    echo "   2. 数据库连接信息保存在 ${INSTALL_DIR}/.env"
    echo "   3. 首次使用请访问 API 文档进行测试"
    echo ""
}

# 主函数
main() {
    check_root
    check_os
    read_config
    install_system_deps
    setup_database
    setup_redis
    setup_code
    setup_python
    setup_env
    init_database
    setup_services
    start_services
    
    # 可选：配置防火墙
    if [[ "$CONFIGURE_FIREWALL" == "y" ]]; then
        setup_firewall
    fi
    
    show_result
}

#==============================================================================
# 执行主函数
#==============================================================================
main "$@"
