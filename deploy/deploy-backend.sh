#!/bin/bash
# ============================================================
# AI Resume System - Backend Deployment Script
# Run on server AFTER code is uploaded to /usr/TalentPool/backend/
# ============================================================
set -e

PROJECT_DIR="/usr/TalentPool"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "=========================================="
echo "  Backend Deployment"
echo "=========================================="

# ── Step 1: Python virtual environment ─────────
echo "[1/4] Creating Python virtual environment..."
cd "$BACKEND_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "  Dependencies installed"

# ── Step 2: Verify .env exists ──────────────────
echo ""
echo "[2/4] Checking .env configuration..."
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create $BACKEND_DIR/.env with the required settings."
    exit 1
fi
echo "  .env found"

# ── Step 3: Create systemd service ──────────────
echo ""
echo "[3/4] Creating systemd service..."
cat > /etc/systemd/system/talent-pool.service << 'EOF'
[Unit]
Description=AI Talent Pool Backend
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/usr/TalentPool/backend
ExecStart=/usr/TalentPool/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1
Restart=always
RestartSec=5
Environment=PATH=/usr/TalentPool/backend/.venv/bin

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable talent-pool
systemctl start talent-pool
sleep 2
echo "  Service started"

# ── Step 4: Health check ───────────────────────
echo ""
echo "[4/4] Health check..."
for i in $(seq 1 10); do
    if curl -sf http://127.0.0.1:8001/health &>/dev/null; then
        echo "  Backend is running!"
        curl -s http://127.0.0.1:8001/health
        echo ""
        break
    fi
    echo "  Waiting for backend... ($i/10)"
    sleep 2
done

echo ""
echo "=========================================="
echo "  Backend deployed on port 8001"
echo "=========================================="
