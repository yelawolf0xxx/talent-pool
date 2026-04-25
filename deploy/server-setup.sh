#!/bin/bash
# ============================================================
# AI Resume System - Server Setup Script
# Supports CentOS 7 (EOL fixed), Ubuntu, Debian, Fedora
# ============================================================

echo "=========================================="
echo "  AI Resume System - Server Setup"
echo "=========================================="

# ── Step 0: Detect OS ──────────────────────────
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS="$ID"
    OS_VERSION="${VERSION_ID%%.*}"
else
    echo "ERROR: Cannot detect OS"
    exit 1
fi
echo "[0/6] Detected OS: $OS $VERSION_ID"

# ── Fix CentOS 7 EOL repo ──────────────────────
if [ "$OS" = "centos" ] && [ "$OS_VERSION" = "7" ]; then
    echo "[1/6] Fixing CentOS 7 yum repositories (EOL)..."
    cd /etc/yum.repos.d/
    mkdir -p /etc/yum.repos.d.bak
    cp -f CentOS-*.repo /etc/yum.repos.d.bak/ 2>/dev/null || true

    # Remove broken repos
    rm -f CentOS-*.repo 2>/dev/null || true

    # Create vault-based repos
    cat > CentOS-Base.repo << 'REPO'
[base]
name=CentOS-7 - Base
baseurl=https://vault.centos.org/7.9.2009/os/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=1

[updates]
name=CentOS-7 - Updates
baseurl=https://vault.centos.org/7.9.2009/updates/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=1

[extras]
name=CentOS-7 - Extras
baseurl=https://vault.centos.org/7.9.2009/extras/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=1
REPO

    yum clean all 2>/dev/null
    yum makecache 2>/dev/null
    echo "  CentOS 7 repos fixed"
    cd /
fi

# ── Step 2: Install MariaDB/MySQL ──────────────
echo ""
echo "[2/6] Installing database..."
if command -v mysql &>/dev/null; then
    echo "  Already installed: $(mysql --version)"
else
    if [ "$OS" = "centos" ] && [ "$OS_VERSION" = "7" ]; then
        yum install -y mariadb-server mariadb
        DB_SERVICE="mariadb"
    else
        apt-get update 2>/dev/null
        apt-get install -y mysql-server mysql-client 2>/dev/null || {
            dnf install -y mysql-server 2>/dev/null || {
                yum install -y mariadb-server mariadb 2>/dev/null
            }
        }
        DB_SERVICE="mysql"
    fi
fi

# Start service
if [ "$OS" = "centos" ] && [ "$OS_VERSION" = "7" ]; then
    DB_SERVICE="mariadb"
fi

systemctl start "$DB_SERVICE" 2>/dev/null || service "$DB_SERVICE" start 2>/dev/null || true
systemctl enable "$DB_SERVICE" 2>/dev/null || true

# Wait for database
echo "  Waiting for database..."
for i in $(seq 1 15); do
    if mysql -u root -e "SELECT 1" &>/dev/null; then
        echo "  Database is ready"
        break
    fi
    sleep 2
done

# Create database and user
mysql -u root -e "CREATE DATABASE IF NOT EXISTS talent_pool CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
APP_DB_PASS="TalentPool_$(date +%s)_Secure"
mysql -u root -e "CREATE USER IF NOT EXISTS 'talent_pool'@'localhost' IDENTIFIED BY '$APP_DB_PASS';"
mysql -u root -e "GRANT ALL PRIVILEGES ON talent_pool.* TO 'talent_pool'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"
echo ""
echo "  *** DATABASE PASSWORD: $APP_DB_PASS ***"
echo "  *** SAVE THIS PASSWORD for .env file! ***"
echo ""

# ── Step 3: Install Python ─────────────────────
echo "[3/6] Installing Python..."
if python3 --version 2>/dev/null | grep -qE "3\.(1[1-9]|[2-9])"; then
    echo "  OK: $(python3 --version)"
elif [ "$OS" = "centos" ] && [ "$OS_VERSION" = "7" ]; then
    yum install -y epel-release 2>/dev/null || true
    yum install -y python3 python3-devel python3-pip 2>/dev/null || true
    # If python3 not available, try python36/python38 from SCL
    if ! python3 --version &>/dev/null; then
        yum install -y centos-release-scl 2>/dev/null || true
        yum install -y rh-python38 2>/dev/null || true
        if [ -f /opt/rh/rh-python38/enable ]; then
            source /opt/rh/rh-python38/enable
            ln -sf /opt/rh/rh-python38/root/usr/bin/python3 /usr/local/bin/python3 2>/dev/null || true
            ln -sf /opt/rh/rh-python38/root/usr/bin/pip3 /usr/local/bin/pip3 2>/dev/null || true
        fi
    fi
    python3 --version 2>/dev/null || echo "  WARNING: python3 not found, trying alternatives..."
else
    apt-get update 2>/dev/null
    apt-get install -y python3 python3-pip python3-venv 2>/dev/null || {
        dnf install -y python3 python3-pip 2>/dev/null
    }
    python3 --version 2>/dev/null || echo "  WARNING: python3 not found"
fi

# ── Step 4: Install Node.js ────────────────────
echo "[4/6] Installing Node.js..."
if command -v node &>/dev/null && node --version | grep -qE "v(1[89]|2[0-9])"; then
    echo "  OK: $(node --version)"
else
    if [ "$OS" = "centos" ] && [ "$OS_VERSION" = "7" ]; then
        yum install -y epel-release 2>/dev/null || true
        curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - 2>/dev/null || true
        yum install -y nodejs 2>/dev/null || {
            yum install -y nodejs npm 2>/dev/null
        }
    else
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>/dev/null || true
        apt-get install -y nodejs 2>/dev/null || {
            dnf install -y nodejs 2>/dev/null || {
                yum install -y nodejs 2>/dev/null
            }
        }
    fi
fi
node --version 2>/dev/null || echo "  WARNING: node not found"
npm --version 2>/dev/null || echo "  WARNING: npm not found"

# ── Step 5: Install Nginx ──────────────────────
echo "[5/6] Installing Nginx..."
if command -v nginx &>/dev/null; then
    echo "  OK: $(nginx -v 2>&1)"
else
    if [ "$OS" = "centos" ] && [ "$OS_VERSION" = "7" ]; then
        yum install -y epel-release 2>/dev/null || true
        yum install -y nginx
    else
        apt-get install -y nginx 2>/dev/null || dnf install -y nginx 2>/dev/null || yum install -y nginx 2>/dev/null
    fi
    systemctl enable nginx 2>/dev/null || true
    systemctl start nginx 2>/dev/null || service nginx start 2>/dev/null || true
fi

# ── Step 6: Create directories ─────────────────
echo "[6/6] Creating deployment directories..."
mkdir -p /usr/TalentPool/backend
mkdir -p /usr/TalentPool/frontend-dist
mkdir -p /usr/TalentPool/resumes
mkdir -p /usr/TalentPool/data/chroma_db
echo "  Created /usr/TalentPool/{backend,frontend-dist,resumes,data/chroma_db}"

# ── Summary ────────────────────────────────────
echo ""
echo "=========================================="
echo "  Environment Setup Complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: Save this database password:"
echo "  $APP_DB_PASS"
echo ""
echo "Next steps:"
echo "  1. Create /usr/TalentPool/backend/.env"
echo "  2. Upload code to /usr/TalentPool/backend/"
echo "  3. Run deploy-backend.sh on server"
echo ""
