#!/bin/bash
# ============================================================
# AI Resume System - Nginx Configuration
# Run on server AFTER frontend dist is uploaded
# ============================================================
set -e

echo "=========================================="
echo "  Nginx Configuration"
echo "=========================================="

# Write nginx config
cat > /etc/nginx/conf.d/talent-pool.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend static files
    location / {
        root /usr/TalentPool/frontend-dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8001;
    }

    # Chat API (long-running requests)
    location /api/chat {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Test and reload nginx
nginx -t
systemctl reload nginx

echo ""
echo "=========================================="
echo "  Nginx configured on port 80"
echo "=========================================="
