#!/bin/bash

#==============================================================================
# SellerSprite Clone - 改进的一键安装脚本 v2.0
# 
# 改进点：
# 1. 增强的 Redis 启动和修复机制
# 2. 详细的错误诊断和日志
# 3. 自动重试和恢复机制
# 4. 健康检查和验证
# 
# 使用方法:
#   chmod +x install-improved.sh && sudo ./install-improved.sh
#==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="sellersprite-clone"
GIT_REPO=""
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_USER="www-data"
PYTHON_VERSION="3.11"
LOG_FILE="/var/log/sellersprite-install.log"

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
        log_error "请使用 root 用户运行此脚本"
        log_info "使用方法: sudo bash install-improved.sh"
        exit 1
    fi
}

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
        log_warning "检测到操作系统: $OS $VER (不是标准的 Debian/Ubuntu)"
    else
        log_info "检测到操作系统: $OS $VER"
    fi
}

#==============================================================================
# Redis 专项修复函数
#==============================================================================

diagnose_redis() {
    log_info "诊断 Redis..."
    
    # 检查 Redis 可执行文件
    if [[ ! -f /usr/bin/redis-server ]]; then
        log_error "Redis 可执行文件不存在: /usr/bin/redis-server"
        return 1
    fi
    
    # 检查可执行权限
    if [[ ! -x /usr/bin/redis-server ]]; then
        log_error "Redis 可执行文件没有执行权限"
        chmod +x /usr/bin/redis-server
        log_success "已修复 Redis 执行权限"
    fi
    
    # 检查配置文件
    if [[ ! -f /etc/redis/redis.conf ]]; then
        log_error "Redis 配置文件不存在: /etc/redis/redis.conf"
        return 1
    fi
    
    # 检查数据目录
    if [[ ! -d /var/lib/redis ]]; then
        log_warning "Redis 数据目录不存在，正在创建..."
        mkdir -p /var/lib/redis
        chown redis:redis /var/lib/redis
        chmod 755 /var/lib/redis
    fi
    
    # 检查日志目录
    if [[ ! -d /var/log/redis ]]; then
        log_warning "Redis 日志目录不存在，正在创建..."
        mkdir -p /var/log/redis
        chown redis:redis /var/log/redis
        chmod 755 /var/log/redis
    fi
    
    return 0
}

fix_redis_config() {
    log_info "修复 Redis 配置..."
    
    # 备份原配置
    if [[ ! -f /etc/redis/redis.conf.bak ]]; then
        cp /etc/redis/redis.conf /etc/redis/redis.conf.bak
    fi
    
    # 修复关键配置
    sed -i 's/^# bind 127.0.0.1/bind 127.0.0.1/' /etc/redis/redis.conf
    sed -i 's/^port 6379/port 6379/' /etc/redis/redis.conf
    sed -i 's/^# logfile ""/logfile "\/var\/log\/redis\/redis-server.log"/' /etc/redis/redis.conf
    sed -i 's/^logfile ""/logfile "\/var\/log\/redis\/redis-server.log"/' /etc/redis/redis.conf
    sed -i 's/^dir \.\//dir \/var\/lib\/redis\//' /etc/redis/redis.conf
    
    # 确保权限正确
    chown redis:redis /etc/redis/redis.conf
    chmod 644 /etc/redis/redis.conf
    
    log_success "Redis 配置已修复"
}

fix_redis_permissions() {
    log_info "修复 Redis 权限..."
    
    # 检查 redis 用户是否存在
    if ! id "redis" &>/dev/null; then
        log_warning "redis 用户不存在，正在创建..."
        useradd -r -s /bin/false redis || true
    fi
    
    # 修复目录权限
    chown -R redis:redis /var/lib/redis
    chmod 755 /var/lib/redis
    
    chown -R redis:redis /var/log/redis
    chmod 755 /var/log/redis
    
    log_success "Redis 权限已修复"
}

fix_redis_socket() {
    log_info "检查 Redis socket..."
    
    # 移除旧的 socket 文件
    if [[ -S /var/run/redis/redis-server.sock ]]; then
        rm -f /var/run/redis/redis-server.sock
    fi
    
    # 确保 socket 目录存在
    mkdir -p /var/run/redis
    chown redis:redis /var/run/redis
    chmod 755 /var/run/redis
    
    log_success "Redis socket 已检查"
}

test_redis_connection() {
    log_info "测试 Redis 连接..."
    
    local max_attempts=5
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if redis-cli ping &>/dev/null; then
            log_success "Redis 连接成功"
            return 0
        fi
        
        log_warning "Redis 连接失败 (第 $attempt/$max_attempts 次尝试)"
        sleep 2
        ((attempt++))
    done
    
    log_error "Redis 连接失败，已重试 $max_attempts 次"
    return 1
}

setup_redis() {
    log_info "=================================================="
    log_info "设置 Redis..."
    log_info "=================================================="
    
    # 安装 Redis（如果未安装）
    if ! command -v redis-server &> /dev/null; then
        log_info "安装 Redis..."
        apt update
        apt install -y redis-server redis-tools
        if [[ $? -ne 0 ]]; then
            log_error "Redis 安装失败"
            return 1
        fi
        log_success "Redis 已安装"
    else
        log_success "Redis 已存在"
    fi
    
    # 诊断和修复
    if ! diagnose_redis; then
        log_error "Redis 诊断失败"
        return 1
    fi
    
    fix_redis_config
    fix_redis_permissions
    fix_redis_socket
    
    # 重新加载 systemd
    systemctl daemon-reload
    
    # 停止旧进程
    systemctl stop redis-server 2>/dev/null || true
    sleep 1
    
    # 启动 Redis
    log_info "启动 Redis..."
    if ! systemctl start redis-server; then
        log_error "Redis 启动失败"
        log_info "详细错误信息:"
        journalctl -xe --unit=redis-server.service -n 30 | tee -a "$LOG_FILE"
        return 1
    fi
    
    # 等待 Redis 就绪
    sleep 3
    
    # 测试连接
    if ! test_redis_connection; then
        log_error "无法连接到 Redis"
        log_info "systemctl 状态:"
        systemctl status redis-server | tee -a "$LOG_FILE"
        log_info "redis-cli ping 输出:"
        redis-cli ping 2>&1 | tee -a "$LOG_FILE" || true
        return 1
    fi
    
    # 启用开机自启
    systemctl enable redis-server
    
    # 显示 Redis 信息
    log_info "Redis 配置信息:"
    log_info "  - 主机: localhost"
    log_info "  - 端口: 6379"
    log_info "  - 状态: $(systemctl is-active redis-server)"
    log_info "  - 进程: $(ps aux | grep redis-server | grep -v grep | awk '{print $2}' || echo 'N/A')"
    
    log_success "Redis 设置完成"
    return 0
}

#==============================================================================
# 其他安装函数
#==============================================================================

install_system_deps() {
    log_info "=================================================="
    log_info "安装系统依赖..."
    log_info "=================================================="
    
    apt update
    apt install -y \
        curl wget git vim build-essential software-properties-common \
        apt-transport-https ca-certificates gnupg lsb-release uuid-runtime \
        python3 python3-venv python3-pip
    
    log_success "系统依赖安装完成"
}

setup_database() {
    log_info "=================================================="
    log_info "设置数据库..."
    log_info "=================================================="
    
    if ! command -v psql &> /dev/null; then
        log_info "安装 PostgreSQL..."
        apt install -y postgresql postgresql-contrib
    fi
    
    systemctl start postgresql
    systemctl enable postgresql
    sleep 2
    
    log_success "数据库设置完成"
}

setup_code() {
    log_info "=================================================="
    log_info "设置代码..."
    log_info "=================================================="
    
    mkdir -p ${INSTALL_DIR}
    
    if [[ -n "$GIT_REPO" ]]; then
        if [[ -d "${INSTALL_DIR}/.git" ]]; then
            log_info "更新代码..."
            cd ${INSTALL_DIR}
            git pull
        else
            log_info "克隆代码仓库..."
            git clone ${GIT_REPO} ${INSTALL_DIR}
        fi
    else
        log_info "复制当前目录代码..."
        cp -r ${SCRIPT_DIR}/* ${INSTALL_DIR}/
    fi
    
    if ! id "${SERVICE_USER}" &>/dev/null; then
        useradd -r -s /bin/false ${SERVICE_USER}
    fi
    
    chown -R ${SERVICE_USER}:${SERVICE_USER} ${INSTALL_DIR}
    chmod 755 ${INSTALL_DIR}
    
    log_success "代码设置完成"
}

setup_python() {
    log_info "=================================================="
    log_info "设置 Python 环境..."
    log_info "=================================================="
    
    cd ${INSTALL_DIR}
    
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    
    deactivate
    
    log_success "Python 环境设置完成"
}

setup_env() {
    log_info "=================================================="
    log_info "设置环境变量..."
    log_info "=================================================="
    
    cd ${INSTALL_DIR}
    
    # 生成 API 密钥
    API_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 64 | head -n 1)
    
    cat > .env << EOF
# SellerSprite Clone - 环境配置
# 自动生成于 $(date)

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/sellersprite
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:password@localhost:5432/sellersprite

# Redis 配置
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

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
    
    chmod 600 .env
    chown ${SERVICE_USER}:${SERVICE_USER} .env
    
    log_success "环境变量设置完成"
}

setup_services() {
    log_info "=================================================="
    log_info "创建系统服务..."
    log_info "=================================================="
    
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable sellersprite-api
    systemctl enable sellersprite-celery
    
    log_success "系统服务创建完成"
}

start_services() {
    log_info "=================================================="
    log_info "启动服务..."
    log_info "=================================================="
    
    systemctl start sellersprite-api
    sleep 2
    
    systemctl start sellersprite-celery
    sleep 2
    
    # 检查状态
    if systemctl is-active --quiet sellersprite-api; then
        log_success "API 服务已启动"
    else
        log_error "API 服务启动失败"
        journalctl -u sellersprite-api --no-pager -n 20 | tee -a "$LOG_FILE"
    fi
    
    if systemctl is-active --quiet sellersprite-celery; then
        log_success "Celery 服务已启动"
    else
        log_warning "Celery 服务启动失败（可能需要等待 Redis）"
    fi
}

show_result() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo "                      安装完成!"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📋 服务状态:"
    echo "   Redis:   $(systemctl is-active redis-server)"
    echo "   API:     $(systemctl is-active sellersprite-api)"
    echo "   Celery:  $(systemctl is-active sellersprite-celery)"
    echo ""
    echo "📋 访问地址:"
    echo "   API 文档: http://localhost:8000/docs"
    echo "   健康检查: http://localhost:8000/health"
    echo ""
    echo "📋 常用命令:"
    echo "   查看 API 日志:    journalctl -u sellersprite-api -f"
    echo "   查看 Celery 日志: journalctl -u sellersprite-celery -f"
    echo "   查看 Redis 日志:  tail -f /var/log/redis/redis-server.log"
    echo "   重启 API:        systemctl restart sellersprite-api"
    echo "   停止 API:        systemctl stop sellersprite-api"
    echo ""
    echo "📋 诊断命令:"
    echo "   Redis 测试:      redis-cli ping"
    echo "   服务状态:        systemctl status redis-server"
    echo "   安装日志:        tail -f $LOG_FILE"
    echo ""
    echo -e "${YELLOW}⚠️  注意:${NC}"
    echo "   1. Redis 必须正常运行，否则 API 无法使用"
    echo "   2. 如果 Redis 连接仍然失败，查看日志: journalctl -xe -u redis-server"
    echo "   3. 确保端口 8000 已开放"
    echo ""
}

#==============================================================================
# 主函数
#==============================================================================

main() {
    echo "日志文件: $LOG_FILE"
    
    check_root
    check_os
    install_system_deps
    setup_database
    
    # Redis 是关键，必须成功
    if ! setup_redis; then
        log_error "Redis 设置失败，无法继续部署"
        exit 1
    fi
    
    setup_code
    setup_python
    setup_env
    setup_services
    start_services
    
    show_result
    
    log_success "所有步骤完成"
}

main "$@"
