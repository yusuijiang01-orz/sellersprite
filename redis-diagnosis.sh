#!/bin/bash

#==============================================================================
# Redis 诊断和修复工具
# 用于快速诊断 Redis 连接问题
#==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo "                  Redis 诊断工具"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo ""
}

check_redis_installed() {
    echo -e "${YELLOW}1. 检查 Redis 是否安装...${NC}"
    
    if command -v redis-server &> /dev/null; then
        echo -e "${GREEN}✓ Redis 已安装${NC}"
        redis-server --version
        echo ""
    else
        echo -e "${RED}✗ Redis 未安装${NC}"
        echo "请运行: sudo apt install -y redis-server redis-tools"
        echo ""
        return 1
    fi
    return 0
}

check_redis_executable() {
    echo -e "${YELLOW}2. 检查 Redis 可执行文件...${NC}"
    
    if [[ -f /usr/bin/redis-server ]]; then
        echo -e "${GREEN}✓ 文件存在: /usr/bin/redis-server${NC}"
        
        if [[ -x /usr/bin/redis-server ]]; then
            echo -e "${GREEN}✓ 文件有执行权限${NC}"
        else
            echo -e "${RED}✗ 文件没有执行权限${NC}"
            echo "尝试修复: sudo chmod +x /usr/bin/redis-server"
        fi
    else
        echo -e "${RED}✗ /usr/bin/redis-server 不存在${NC}"
    fi
    
    ls -la /usr/bin/redis-* 2>/dev/null || echo "未找到 redis 相关文件"
    echo ""
}

check_redis_config() {
    echo -e "${YELLOW}3. 检查 Redis 配置文件...${NC}"
    
    if [[ -f /etc/redis/redis.conf ]]; then
        echo -e "${GREEN}✓ 配置文件存在: /etc/redis/redis.conf${NC}"
        
        # 检查关键配置
        echo ""
        echo "关键配置项:"
        grep -E "^(port|bind|dir|logfile)" /etc/redis/redis.conf || echo "未找到关键配置"
    else
        echo -e "${RED}✗ 配置文件不存在: /etc/redis/redis.conf${NC}"
    fi
    echo ""
}

check_redis_directories() {
    echo -e "${YELLOW}4. 检查 Redis 目录和权限...${NC}"
    
    # 检查数据目录
    if [[ -d /var/lib/redis ]]; then
        echo -e "${GREEN}✓ 数据目录存在: /var/lib/redis${NC}"
        ls -ld /var/lib/redis
    else
        echo -e "${RED}✗ 数据目录不存在: /var/lib/redis${NC}"
    fi
    
    echo ""
    
    # 检查日志目录
    if [[ -d /var/log/redis ]]; then
        echo -e "${GREEN}✓ 日志目录存在: /var/log/redis${NC}"
        ls -ld /var/log/redis
    else
        echo -e "${YELLOW}⚠ 日志目录不存在: /var/log/redis${NC}"
    fi
    
    echo ""
}

check_redis_service_status() {
    echo -e "${YELLOW}5. 检查 Redis 服务状态...${NC}"
    
    if systemctl is-active --quiet redis-server; then
        echo -e "${GREEN}✓ Redis 服务正在运行${NC}"
    else
        echo -e "${RED}✗ Redis 服务未运行${NC}"
        echo "尝试启动: sudo systemctl start redis-server"
    fi
    
    echo ""
    systemctl status redis-server --no-pager -l 2>/dev/null | head -10
    echo ""
}

check_redis_connection() {
    echo -e "${YELLOW}6. 测试 Redis 连接...${NC}"
    
    if redis-cli ping &>/dev/null; then
        echo -e "${GREEN}✓ Redis 连接成功${NC}"
        echo "Ping 响应:"
        redis-cli ping
    else
        echo -e "${RED}✗ Redis 连接失败${NC}"
        echo "尝试手动连接的输出:"
        redis-cli ping 2>&1 || echo "连接失败"
    fi
    
    echo ""
}

check_redis_info() {
    echo -e "${YELLOW}7. 获取 Redis 信息...${NC}"
    
    if redis-cli ping &>/dev/null; then
        echo "Redis 基本信息:"
        redis-cli info server | head -10
        echo ""
        echo "内存使用:"
        redis-cli info memory | grep "used_memory"
        echo ""
        echo "连接数:"
        redis-cli info clients | grep "connected_clients"
    else
        echo -e "${YELLOW}⚠ 无法连接到 Redis，跳过此步骤${NC}"
    fi
    
    echo ""
}

check_ports() {
    echo -e "${YELLOW}8. 检查端口占用...${NC}"
    
    echo "监听端口 6379 的进程:"
    if command -v ss &>/dev/null; then
        ss -tlnp | grep 6379 || echo "未找到监听 6379 的进程"
    elif command -v netstat &>/dev/null; then
        netstat -tlnp | grep 6379 || echo "未找到监听 6379 的进程"
    elif command -v lsof &>/dev/null; then
        lsof -i :6379 || echo "未找到监听 6379 的进程"
    else
        echo "未安装 ss/netstat/lsof，无法检查端口"
    fi
    
    echo ""
}

check_redis_logs() {
    echo -e "${YELLOW}9. 查看 Redis 日志...${NC}"
    
    LOG_FILE="/var/log/redis/redis-server.log"
    
    if [[ -f $LOG_FILE ]]; then
        echo "Redis 日志文件最后 10 行:"
        tail -10 "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠ 日志文件不存在: $LOG_FILE${NC}"
        echo "尝试从 systemd 日志查看:"
        sudo journalctl -xe -u redis-server.service -n 10 2>/dev/null || echo "无法访问 systemd 日志"
    fi
    
    echo ""
}

auto_fix_redis() {
    echo -e "${YELLOW}10. 自动修复建议...${NC}"
    echo ""
    
    local issues=0
    
    # 检查各种问题
    if ! command -v redis-server &> /dev/null; then
        echo -e "${YELLOW}问题: Redis 未安装${NC}"
        echo "修复: sudo apt update && sudo apt install -y redis-server redis-tools"
        ((issues++))
    fi
    
    if [[ -f /usr/bin/redis-server ]] && [[ ! -x /usr/bin/redis-server ]]; then
        echo -e "${YELLOW}问题: Redis 可执行文件权限不对${NC}"
        echo "修复: sudo chmod +x /usr/bin/redis-server"
        ((issues++))
    fi
    
    if ! systemctl is-active --quiet redis-server; then
        echo -e "${YELLOW}问题: Redis 服务未运行${NC}"
        echo "修复: sudo systemctl start redis-server"
        ((issues++))
    fi
    
    if [[ -d /var/lib/redis ]] && [[ $(stat -c %U /var/lib/redis 2>/dev/null || echo "unknown") != "redis" ]]; then
        echo -e "${YELLOW}问题: Redis 数据目录权限不对${NC}"
        echo "修复: sudo chown -R redis:redis /var/lib/redis && sudo chmod 755 /var/lib/redis"
        ((issues++))
    fi
    
    echo ""
    if [[ $issues -eq 0 ]]; then
        echo -e "${GREEN}✓ 未发现需要修复的问题${NC}"
    else
        echo -e "${YELLOW}发现 $issues 个问题，请按照上面的修复建议操作${NC}"
    fi
    
    echo ""
}

show_quick_fix() {
    echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
    echo "                  快速修复命令"
    echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "如果遇到 Redis 连接问题，按顺序尝试以下命令："
    echo ""
    echo "1. 重新安装 Redis:"
    echo "   sudo apt remove -y redis-server redis-tools"
    echo "   sudo apt autoclean && sudo apt autoremove"
    echo "   sudo apt update && sudo apt install -y redis-server redis-tools"
    echo ""
    echo "2. 修复权限:"
    echo "   sudo chown -R redis:redis /var/lib/redis"
    echo "   sudo chown -R redis:redis /var/log/redis"
    echo "   sudo chmod 755 /var/lib/redis /var/log/redis"
    echo ""
    echo "3. 重启 Redis:"
    echo "   sudo systemctl daemon-reload"
    echo "   sudo systemctl restart redis-server"
    echo ""
    echo "4. 测试连接:"
    echo "   redis-cli ping"
    echo "   # 应该输出: PONG"
    echo ""
}

main() {
    print_header
    
    check_redis_installed || return 1
    check_redis_executable
    check_redis_config
    check_redis_directories
    check_redis_service_status
    check_redis_connection
    check_redis_info
    check_ports
    check_redis_logs
    auto_fix_redis
    show_quick_fix
    
    echo -e "${GREEN}诊断完成${NC}"
}

# 检查是否为 root
if [[ $EUID -ne 0 ]]; then
    # 某些命令需要 root 权限，但诊断可以运行
    echo -e "${YELLOW}⚠ 建议使用 root 权限运行此脚本以获得完整诊断${NC}"
    echo "建议: sudo bash $0"
    echo ""
fi

main
