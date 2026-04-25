# Deployment Scripts for AI Resume System

## 一键部署 (推荐)

将 `deploy/` 整个目录上传到 Ubuntu 24.04 服务器后执行：

```bash
cd /path/to/deploy
sudo bash deploy.sh
```

自动完成：系统依赖安装 → MySQL 配置 → 后端部署 → 前端构建 → Nginx 配置 → 服务启动。

## 日常重新部署 (代码变更后)

将整个项目上传到服务器后执行：

```bash
cd /path/to/deploy
sudo bash redeploy.sh
```

自动完成：同步后端代码 → 重新构建前端 → 重启服务 → 重载 Nginx。

## 分步部署 (传统方式)

### 1. Setup Server Environment
SSH 到服务器 `ssh root@192.168.3.84`，然后执行：
```bash
chmod +x server-setup.sh && bash server-setup.sh
```
自动安装 MySQL、Python 3.11、Node.js、Nginx，创建数据库和部署目录。

### 2. Create Backend .env
在服务器上创建 `/usr/TalentPool/backend/.env`：
```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=talent_pool
DB_PASSWORD=<server-setup 输出的密码>
DB_NAME=talent_pool
ANTHROPIC_AUTH_TOKEN=<你的 API Token>
ANTHROPIC_BASE_URL=<你的 API 地址>
ANTHROPIC_MODEL=qwen3.6-plus
RESUME_DIR=/usr/TalentPool/resumes
SCAN_INTERVAL=300
JWT_SECRET=<生成一个随机密钥>
```

### 3. Deploy Backend
```bash
chmod +x deploy-backend.sh && bash deploy-backend.sh
```

### 4. Deploy Frontend
在本机运行 `deploy.bat`（构建前端并上传到服务器）。

### 5. Setup Nginx
```bash
chmod +x setup-nginx.sh && bash setup-nginx.sh
```

## Daily Deploy (After code changes)
本机直接运行 `deploy.bat`，自动构建前端 + 同步代码 + 重启后端。

## Files
| File | Purpose |
|------|---------|
| `deploy.sh` | Ubuntu 24.04 一键部署（环境+后端+前端+Nginx） |
| `redeploy.sh` | 代码变更后快速重新部署 |
| `server-setup.sh` | 首次运行在服务器上安装环境 |
| `deploy-backend.sh` | 服务器上部署后端服务 |
| `setup-nginx.sh` | 配置 Nginx 反向代理 |
| `deploy.bat` | 本机日常部署（构建+同步+重启） |

## Directory Structure on Server
```
/opt/talent-pool/                  # 新部署路径 (deploy.sh)
├── backend/              # FastAPI 代码
│   ├── .venv/            # Python 虚拟环境
│   ├── .env              # 生产配置（不同步）
│   └── app/
├── frontend-dist/        # 前端构建产物（npm run build）
├── resumes/              # PDF 简历存储
├── data/chroma_db/       # ChromaDB 向量数据
└── deploy/               # 部署脚本
```
