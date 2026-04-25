#!/bin/bash
# ============================================================
# AI Talent Pool - One-Click Deploy for Ubuntu 24.04 LTS
# Usage: chmod +x deploy.sh && sudo bash deploy.sh
# ============================================================
set -euo pipefail

# ── Config ──────────────────────────────────────
PROJECT_DIR="/opt/talent-pool"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIST="$PROJECT_DIR/frontend-dist"
RESUME_DIR="$PROJECT_DIR/resumes"
CHROMA_DIR="$PROJECT_DIR/data/chroma_db"
BACKEND_PORT=8001
DB_NAME="talent_pool"
DB_USER="talent_pool"
DB_PASS="Tp_$(openssl rand -hex 16)"
PYTHON_VERSION="3.12"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Pre-flight checks ───────────────────────────
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  AI Talent Pool - One-Click Deploy (Ubuntu 24.04 LTS)${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

if [[ $EUID -ne 0 ]]; then
    log_error "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

if ! grep -q "24.04" /etc/os-release 2>/dev/null; then
    log_warn "此脚本专为 Ubuntu 24.04 LTS 设计，当前系统可能不匹配"
    read -p "是否继续？(y/N): " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 1
fi

TOTAL_STEPS=8
STEP=0

step() {
    STEP=$((STEP + 1))
    echo ""
    echo -e "${BLUE}[$STEP/$TOTAL_STEPS] $1${NC}"
    echo "────────────────────────────────────────────────"
}

# ── Step 1: System dependencies ─────────────────
step "安装系统依赖"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
    mysql-server mysql-client \
    python3 python3-dev python3-pip python3-venv \
    nodejs npm \
    nginx \
    git curl wget openssl \
    build-essential libmysqlclient-dev \
    > /dev/null 2>&1
log_ok "系统依赖安装完成"

# ── Step 2: MySQL setup ─────────────────────────
step "配置 MySQL 数据库"

systemctl enable mysql
systemctl start mysql

log_info "等待数据库就绪..."
for i in $(seq 1 15); do
    if mysql -u root -e "SELECT 1" &>/dev/null; then
        log_ok "数据库连接成功"
        break
    fi
    if [ "$i" -eq 15 ]; then
        log_error "数据库启动超时，请检查 MySQL 状态"
        exit 1
    fi
    sleep 2
done

mysql -u root -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';"
mysql -u root -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"
log_ok "数据库 $DB_NAME 已创建"

# ── Step 3: Create directories ──────────────────
step "创建部署目录"
mkdir -p "$BACKEND_DIR" "$FRONTEND_DIST" "$RESUME_DIR" "$CHROMA_DIR"
chown -R root:root "$PROJECT_DIR"
log_ok "部署目录已创建: $PROJECT_DIR"

# ── Step 4: Deploy backend code ─────────────────
step "部署后端代码"

# 如果脚本所在目录有 backend 文件夹，则复制过去
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/backend" ]; then
    rsync -a --exclude='.env' --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
        "$SCRIPT_DIR/backend/" "$BACKEND_DIR/"
    log_ok "后端代码已同步"
else
    log_warn "未找到 backend 目录，跳过代码同步"
    log_info "请手动将代码复制到 $BACKEND_DIR"
fi

# ── Step 5: Python virtualenv + dependencies ───
step "安装 Python 依赖"

cd "$BACKEND_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>&1 | tail -5
log_ok "Python 依赖安装完成"

# ── Step 6: Generate .env ───────────────────────
step "生成后端配置 (.env)"

JWT_SECRET="$(openssl rand -hex 32)"

if [ -f "$BACKEND_DIR/.env" ]; then
    log_warn ".env 已存在，跳过生成"
    log_info "如需更新请手动编辑 $BACKEND_DIR/.env"
else
    cat > "$BACKEND_DIR/.env" << ENVEOF
# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
DB_NAME=$DB_NAME

# AI 配置
ANTHROPIC_AUTH_TOKEN=
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
ANTHROPIC_MODEL=qwen3.6-plus

# 简历目录路径
RESUME_DIR=$RESUME_DIR

# 扫描间隔（秒）
SCAN_INTERVAL=300

# JWT 密钥
JWT_SECRET=$JWT_SECRET
ENVEOF
    log_ok ".env 已生成: $BACKEND_DIR/.env"
fi

# ── Step 7: Build frontend ──────────────────────
step "构建前端"

if [ -d "$SCRIPT_DIR/frontend" ]; then
    cd "$SCRIPT_DIR/frontend"
    npm install --silent 2>/dev/null
    npm run build 2>&1 | tail -3
    rsync -a dist/ "$FRONTEND_DIST/"
    log_ok "前端构建完成"
else
    log_warn "未找到 frontend 目录，跳过前端构建"
    log_info "请手动将 dist 文件复制到 $FRONTEND_DIST"
fi

# ── Step 8: Nginx + systemd service ─────────────
step "配置 Nginx 和系统服务"

# Nginx config
cat > /etc/nginx/sites-available/talent-pool << 'NGINXEOF'
server {
    listen 80 default_server;
    server_name _;

    # Frontend static files
    location / {
        root FRONTEND_DIST_PLACEHOLDER;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:BACKEND_PORT_PLACEHOLDER;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:BACKEND_PORT_PLACEHOLDER;
    }

    # Chat API (long-running requests)
    location /api/chat {
        proxy_pass http://127.0.0.1:BACKEND_PORT_PLACEHOLDER;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
NGINXEOF

# 替换占位符
sed -i "s|FRONTEND_DIST_PLACEHOLDER|$FRONTEND_DIST|g" /etc/nginx/sites-available/talent-pool
sed -i "s|BACKEND_PORT_PLACEHOLDER|$BACKEND_PORT|g" /etc/nginx/sites-available/talent-pool

# 启用站点
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/talent-pool /etc/nginx/sites-enabled/
nginx -t
systemctl enable nginx
systemctl restart nginx
log_ok "Nginx 配置完成"

# systemd service
cat > /etc/systemd/system/talent-pool.service << SVCEOF
[Unit]
Description=AI Talent Pool Backend
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
ExecStart=$BACKEND_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --workers 1
Restart=always
RestartSec=5
Environment=PATH=$BACKEND_DIR/.venv/bin

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable talent-pool
systemctl start talent-pool
log_ok "系统服务已启动"

# ── Health check ────────────────────────────────
echo ""
echo -e "${BLUE}[HEALTH] 等待后端启动...${NC}"
for i in $(seq 1 15); do
    if curl -sf http://127.0.0.1:$BACKEND_PORT/health &>/dev/null; then
        log_ok "后端服务运行正常"
        break
    fi
    if [ "$i" -eq 15 ]; then
        log_error "后端启动超时，请检查日志: journalctl -u talent-pool -n 50"
        exit 1
    fi
    sleep 2
done

# ── Firewall ────────────────────────────────────
if command -v ufw &>/dev/null; then
    ufw_status=$(ufw status 2>/dev/null || echo "inactive")
    if echo "$ufw_status" | grep -q "Status: active"; then
        ufw allow 80/tcp > /dev/null 2>&1
        log_ok "防火墙已放行 80 端口"
    fi
fi

# ── Summary ─────────────────────────────────────
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  访问地址:  http://$(hostname -I | awk '{print $1}' || echo 'YOUR_SERVER_IP')"
echo -e "  后端 API:  http://localhost:$BACKEND_PORT"
echo -e "  健康检查:  http://localhost:$BACKEND_PORT/health"
echo ""
echo -e "${YELLOW}  ⚠ 请保存以下数据库密码：${NC}"
echo -e "  数据库:    $DB_NAME"
echo -e "  用户名:    $DB_USER"
echo -e "  密码:      $DB_PASS"
echo ""
echo -e "${YELLOW}  ⚠ 请编辑 .env 填入 AI 配置：${NC}"
echo -e "  文件:      $BACKEND_DIR/.env"
echo -e "  必填项:    ANTHROPIC_AUTH_TOKEN"
echo -e ""
echo -e "${YELLOW}  ⚠ 简历存放路径：${NC}"
echo -e "  目录:      $RESUME_DIR"
echo ""
echo -e "  常用命令:"
echo -e "    查看状态:  systemctl status talent-pool"
echo -e "    查看日志:  journalctl -u talent-pool -f"
echo -e "    重启服务:  systemctl restart talent-pool"
echo -e "    重新加载:  systemctl reload nginx"
echo ""
echo -e "${GREEN}============================================================${NC}"
