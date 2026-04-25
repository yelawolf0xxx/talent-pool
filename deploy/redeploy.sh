#!/bin/bash
# ============================================================
# AI Talent Pool - Redeploy Script (After Code Changes)
# Run on the Ubuntu server after new code has been uploaded
# Usage: sudo bash redeploy.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="/opt/talent-pool"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIST="$PROJECT_DIR/frontend-dist"
BACKEND_PORT=8001

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }

if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[ERROR] 请使用 sudo 运行${NC}"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Backend ─────────────────────────────────────
echo -e "${BLUE}[1/3] 更新后端代码${NC}"
if [ -d "$SCRIPT_DIR/../backend" ]; then
    rsync -a --exclude='.env' --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
        "$SCRIPT_DIR/../backend/" "$BACKEND_DIR/"
    log_ok "后端代码已同步"
else
    echo "  未找到 backend 目录，跳过"
fi

# ── Frontend ────────────────────────────────────
echo -e "${BLUE}[2/3] 重新构建前端${NC}"
if [ -d "$SCRIPT_DIR/../frontend" ]; then
    cd "$SCRIPT_DIR/../frontend"
    npm install --silent 2>/dev/null || true
    npm run build 2>&1 | tail -3
    rsync -a dist/ "$FRONTEND_DIST/"
    log_ok "前端构建完成"
else
    echo "  未找到 frontend 目录，跳过"
fi

# ── Restart ─────────────────────────────────────
echo -e "${BLUE}[3/3] 重启服务${NC}"
systemctl restart talent-pool
sleep 3

if curl -sf http://127.0.0.1:$BACKEND_PORT/health &>/dev/null; then
    log_ok "后端服务重启成功"
else
    echo -e "${RED}[ERROR] 后端启动失败，查看日志: journalctl -u talent-pool -n 50${NC}"
    exit 1
fi

nginx -t && systemctl reload nginx
log_ok "Nginx 重载成功"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  重新部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
