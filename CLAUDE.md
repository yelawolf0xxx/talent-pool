# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

AI 简历人才库系统：自动扫描 PDF 简历目录，使用 Claude AI 提取结构化信息，存储到 MySQL 数据库，并通过 ChromaDB 向量库实现语义搜索。前端提供简历搜索、详情查看和 AI 对话功能。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11+, FastAPI, SQLAlchemy, PyMuPDF, ChromaDB, APScheduler |
| 前端 | Vue 3, Vite, Element Plus, Vue Router, Axios |
| AI | Anthropic Claude API |
| 数据库 | MySQL (关系型), ChromaDB (向量) |

## 目录结构

```
talent-pool/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，启动时初始化 DB + 定时扫描
│   │   ├── config.py            # Pydantic Settings 配置
│   │   ├── models/
│   │   │   ├── db.py            # SQLAlchemy 引擎/会话管理
│   │   │   ├── resume_models.py # ORM 模型 (ResumeFile, Resume, ChatSession)
│   │   │   └── schemas.py       # Pydantic 请求/响应模型
│   │   ├── routes/
│   │   │   ├── api.py           # REST API: 简历列表/详情/搜索/推荐理由
│   │   │   └── chat.py          # AI 对话 API
│   │   └── services/
│   │       ├── ai.py            # Claude API 封装 (提取/推荐/对话)
│   │       ├── parser.py        # PDF/DOCX/PPTX 解析 + AI 结构化提取
│   │       ├── preprocessor.py  # 简历文本预处理 (噪音清理 + 段落提取)
│   │       ├── scanner.py       # 定时扫描简历目录检测新 PDF/DOCX/PPTX
│   │       ├── search.py        # 混合搜索 (关键词 + 语义)
│   │       └── vector.py        # ChromaDB 向量索引
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.js              # Vue 入口，注册 Element Plus
│   │   ├── App.vue              # 根布局 (Header + RouterView)
│   │   ├── api/index.js         # Axios API 封装
│   │   ├── router/index.js      # 路由: /, /resume/:id, /chat
│   │   └── views/
│   │       ├── HomeView.vue     # 首页: 搜索 + 简历列表
│   │       ├── DetailView.vue   # 简历详情 + AI 推荐理由
│   │       └── ChatView.vue     # AI 对话界面
│   └── vite.config.js           # 前端代理: /api → http://127.0.0.1:8000
├── scripts/
│   └── reprocess.py             # 手动重处理失败简历脚本
├── data/chroma_db/              # ChromaDB 持久化向量数据
└── resumes/                     # PDF 简历存放目录
```

## 开发命令

### 后端

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 ANTHROPIC_API_KEY 等

# 启动开发服务器（局域网可访问）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器 (自动代理到后端 8000 端口)
npm run dev

# 构建生产版本
npm run build
```

### 其他

```bash
# 重处理失败的简历
python scripts/reprocess.py
```

## 核心架构

### 简历处理流水线

1. **扫描** (`scanner.py`): APScheduler 定时扫描 `resumes/` 目录 (支持多目录，逗号分隔)，通过 SHA256 校验和识别新增/变更的 PDF/DOC/DOCX/PPT/PPTX 文件
2. **预处理** (`preprocessor.py`): 轻量整理提取文本 (清理噪音/页码，合并短行，提取关键段落如教育/工作/技能)
3. **解析** (`parser.py`): PyMuPDF/python-docx/python-pptx 提取原始文本 → 预处理 → Claude AI 提取结构化信息 (姓名/技能/经历等)
4. **存储** (`resume_models.py`): 写入 MySQL 的 `resume_files` 和 `resumes` 表
5. **索引** (`vector.py`): 为简历构建搜索文本并写入 ChromaDB 向量集合

### 扫描机制

- **定时扫描**: APScheduler 按 `SCAN_INTERVAL` 间隔自动触发 (默认 300 秒)
- **手动扫描**: POST `/api/scan` 异步触发，可通过 GET `/api/scan/status` 查询进度
- **并发控制**: 全局 `threading.Lock` 防止定时/手动扫描竞争
- **文件去重**: 通过 `ResumeFile` 表记录路径 + SHA256 校验和，避免重复处理

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/scan` | 手动触发扫描 (异步) |
| GET | `/api/scan/status` | 查询扫描进度 |
| GET | `/api/resumes` | 分页列出所有简历 |
| GET | `/api/resumes/{id}` | 获取简历详情 |
| POST | `/api/search` | 搜索简历 (关键词 + 技能/年限筛选) |
| GET | `/api/resumes/{id}/recommend?query=...` | AI 生成岗位匹配推荐理由 |
| POST | `/api/chat` | AI 对话 (非流式) |

### 数据库模型

- **ResumeFile**: 文件追踪 (路径/校验和/状态: pending/processing/done/failed)
- **Resume**: 解析后的结构化数据 (基本信息/教育/技能/工作经历/AI 摘要)
- **ChatSession**: 对话记录 (session_id/角色/内容/关联简历)

## 关键注意事项

- 后端启动时自动创建数据库表 (`init_db()`)，MySQL 需预先创建 `talent_pool` 数据库
- ChromaDB 使用持久化模式，数据存储在 `data/chroma_db/`
- 前端通过 Vite 代理将 `/api` 请求转发到后端 8000 端口，开发时已配置 CORS 允许所有来源
- 后端已启用 `CORSMiddleware` (allow_origins=["*"])
- AI 调用默认使用 `claude-sonnet-4-6-20251014` 模型，通过 `ANTHROPIC_MODEL` 环境变量切换
- `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN` 支持通过网关代理访问 AI 服务 (如 DashScope)
- `RESUME_DIR` 支持多目录 (逗号分隔)，包括 UNC 网络路径 (`\\\\server\\share`)
- 项目未配置测试框架，无现有单元测试或集成测试
- 支持的简历文件格式: PDF, DOC, DOCX, PPT, PPTX
