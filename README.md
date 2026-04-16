# AI 简历人才库系统

> 自动扫描 PDF/DOC/PPT 简历目录，使用 AI 提取结构化信息，存储到 MySQL 数据库，通过 ChromaDB 向量库实现语义搜索，并提供简历管理、岗位匹配分析和 AI 对话功能。

## 功能特性

- **自动扫描**：定时扫描指定目录（含 UNC 网络路径），自动检测新增/变更的简历文件
- **多格式解析**：支持 PDF、DOC、DOCX、PPT、PPTX 格式的简历文件
- **AI 结构化提取**：使用大语言模型从非结构化简历中提取姓名、技能、教育背景、工作经历等
- **混合搜索**：结合 SQL 关键词匹配与 ChromaDB 向量语义搜索，按加权分数排序
- **岗位匹配分析**：输入岗位需求描述，AI 生成匹配度评分和推荐理由
- **AI 对话**：针对特定候选人进行多轮对话，深入了解候选人背景
- **多目录支持**：可同时监控多个简历存放目录

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11+, FastAPI, SQLAlchemy, PyMuPDF, python-docx, python-pptx, ChromaDB, APScheduler |
| 前端 | Vue 3, Vite, Element Plus, Vue Router, Axios |
| AI | Claude API (兼容 OpenAI 协议网关，如 DashScope) |
| 数据库 | MySQL 8.0+ (关系型存储), ChromaDB (向量语义索引) |

## 系统架构

### 整体架构图

```
┌─────────────────┐     定时扫描      ┌──────────────────┐
│  简历目录(PDF)   │ ──────────────►  │  Scanner 服务     │
│  本地/网络共享    │                 │  (SHA256 去重)     │
└─────────────────┘                 └────────┬─────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │  Parser 服务              │
                              │  ├─ PyMuPDF 提取 PDF 文本  │
                              │  ├─ python-docx 提取 DOCX  │
                              │  ├─ python-pptx 提取 PPTX  │
                              │  └─ LibreOffice 转 DOC/PPT │
                              └────────────┬─────────────┘
                                           │
                                           ▼
                              ┌──────────────────────────┐
                              │  Preprocessor 预处理       │
                              │  ├─ 清理噪音/页码           │
                              │  ├─ 合并短行               │
                              │  └─ 提取关键段落           │
                              └────────────┬─────────────┘
                                           │
                                           ▼
                              ┌──────────────────────────┐
                              │  AI 结构化提取 (Claude)    │
                              │  提取: 姓名/技能/教育/经历  │
                              └────────────┬─────────────┘
                                           │
                          ┌────────────────┼────────────────┐
                          ▼                ▼                ▼
                   ┌────────────┐  ┌────────────┐  ┌────────────┐
                   │   MySQL    │  │  ChromaDB  │  │  文件状态   │
                   │  结构化数据 │  │  向量索引   │  │  追踪表     │
                   └────────────┘  └────────────┘  └────────────┘
```

### 简历处理流水线

```
扫描目录 ─► 检测新文件(SHA256去重) ─► 文本提取 ─► 预处理 ─► AI提取 ─► 存储+向量索引
```

1. **扫描阶段**：遍历配置的简历目录，通过 SHA256 校验和识别新增或变更的文件
2. **文本提取阶段**：根据文件扩展名路由到对应的提取器（PyMuPDF/python-docx/python-pptx）
3. **预处理阶段**：清理页码等噪音、合并短行、提取关键段落（教育/工作/技能等）
4. **AI 提取阶段**：双层文本策略（原始文本保底 + 整理文本辅助），调用 AI 提取结构化信息
5. **存储阶段**：写入 MySQL 简历表和文件追踪表，同时建立 ChromaDB 向量索引

### 后端分层架构

```
app/
├── main.py              # FastAPI 应用工厂、启动初始化、定时调度器
├── config.py            # Pydantic Settings 配置管理
├── models/
│   ├── db.py            # SQLAlchemy 引擎/会话/基类
│   ├── resume_models.py # ORM 模型 (ResumeFile/Resume/ChatSession)
│   └── schemas.py       # Pydantic 请求/响应数据模型
├── routes/
│   ├── api.py           # REST API (简历CRUD/搜索/扫描/推荐理由)
│   └── chat.py          # AI 对话 API
└── services/
    ├── scanner.py       # 目录扫描 + SHA256 文件去重
    ├── parser.py        # 多格式文本提取 + AI 解析编排
    ├── preprocessor.py  # 简历文本预处理 (噪音清理 + 段落提取)
    ├── ai.py            # Claude API 封装 (提取/推荐/对话)
    ├── search.py        # 混合搜索 (关键词 40% + 语义 60%)
    └── vector.py        # ChromaDB 向量索引管理
```

## 数据库设计

### resume_files（文件追踪表）

追踪简历文件状态，避免重复处理。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| file_path | VARCHAR(512) UNIQUE | 文件绝对路径 |
| file_hash | VARCHAR(64) | SHA256 校验和 |
| status | VARCHAR(20) | 状态: pending/processing/done/failed |
| created_at | DATETIME | 发现时间 |
| processed_at | DATETIME | 处理完成时间 |

### resumes（简历数据表）

存储 AI 提取的结构化简历信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| file_id | INT | 关联 resume_files.id |
| name | VARCHAR(100) | 姓名 |
| email | VARCHAR(200) | 邮箱 |
| phone | VARCHAR(50) | 电话 |
| current_title | VARCHAR(200) | 当前/最近职位 |
| years_exp | VARCHAR(20) | 工作年限 |
| education_json | TEXT | 教育背景 JSON 数组 |
| skills_json | TEXT | 技能 JSON 数组 |
| work_exp_json | TEXT | 工作经历 JSON 数组 |
| summary_text | TEXT | AI 生成的简历摘要 |
| is_deleted | BOOLEAN | 是否已删除（软删除），默认 FALSE |
| deleted_at | DATETIME | 删除时间 |
| created_at | DATETIME | 创建时间 |

索引: `idx_name`, `idx_title`

### chat_sessions（对话记录表）

存储用户与 AI 的对话记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| session_id | VARCHAR(64) | 会话标识 (索引) |
| role | VARCHAR(20) | 角色: user/assistant |
| content | TEXT | 消息内容 |
| resume_id | INT | 关联的简历 ID |
| created_at | DATETIME | 创建时间 |

## API 参考

### 健康检查

```
GET /health
```

返回: `{"status": "ok"}`

### 扫描管理

**手动触发扫描**

```
POST /api/scan
```

返回: `{"status": "started", "message": "扫描任务已启动"}`

**查询扫描进度**

```
GET /api/scan/status
```

返回:

```json
{
  "active": true,
  "total": 10,
  "current": 3,
  "processed": 2,
  "failed": 0,
  "message": "正在处理第 3/10 份简历..."
}
```

### 简历管理

**上传简历文件**

```
POST /api/upload
Content-Type: multipart/form-data

file: <简历文件>
```

限制：仅支持 PDF/DOC/DOCX/PPT/PPTX 格式，最大 20MB。

返回:
```json
{
  "filename": "20260416_172025_resume.pdf",
  "path": "D:/talent-pool/resumes/20260416_172025_resume.pdf"
}
```

**获取简历列表**

```
GET /api/resumes?skip=0&limit=20
```

**获取简历详情**

```
GET /api/resumes/{id}
```

返回示例:

```json
{
  "id": 1,
  "name": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "current_title": "高级Java工程师",
  "years_exp": "5",
  "education": [
    {"school": "某某大学", "degree": "本科", "major": "计算机科学与技术", "year": 2019}
  ],
  "skills": ["Java", "Spring Boot", "MySQL", "Redis", "Docker"],
  "work_experience": [
    {
      "company": "某某科技有限公司",
      "title": "高级Java工程师",
      "start": "2021.06",
      "end": "至今",
      "description": "负责核心业务系统开发..."
    }
  ],
  "summary_text": "具有高级Java工程师经验，5年工作经验，擅长Java、Spring Boot、MySQL等技术。"
}
```

### 搜索

```
POST /api/search
Content-Type: application/json

{
  "query": "Java后端开发",
  "skills": ["Java", "Spring Boot"],
  "min_years_exp": 3
}
```

返回:

```json
{
  "total": 5,
  "results": [
    {
      "resume": { ... },
      "score": 0.856,
      "match_reasons": ["职位「高级Java工程师」与搜索相关", "技能匹配: Java, Spring Boot"]
    }
  ]
}
```

搜索算法采用混合排序：`综合分 = 关键词得分 × 0.4 + 语义得分 × 0.6`。当向量库不可用时自动降级为纯关键词搜索。

### 岗位匹配推荐

```
GET /api/resumes/{id}/recommend?query=需要3年以上Java经验的后端开发工程师
```

返回:

```json
{
  "resume_id": 1,
  "query": "需要3年以上Java经验的后端开发工程师",
  "suitable": true,
  "score": 85,
  "conclusion": "该候选人基本符合岗位要求",
  "reason": "候选人具有5年Java开发经验，技术栈与岗位需求高度匹配..."
}
```

### 软删除 / 回收站

**批量软删除简历**

```
POST /api/resumes/delete
Content-Type: application/json

{"ids": [1, 2, 3]}
```

返回: `{"deleted": 3}`

**批量恢复已删除简历**

```
POST /api/resumes/restore
Content-Type: application/json

{"ids": [1, 2, 3]}
```

返回: `{"restored": 3}`

**获取回收站列表**

```
GET /api/recycle-bin?skip=0&limit=20
```

返回:
```json
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "name": "张三",
      "skills": ["Java", "Spring Boot"],
      "deleted_at": "2026-04-16T17:20:25",
      ...
    }
  ]
}
```

### AI 对话

```
POST /api/chat
Content-Type: application/json

{
  "session_id": "session_001",
  "resume_id": 1,
  "messages": [
    {"role": "user", "content": "这个候选人的技术深度如何？"}
  ]
}
```

返回:

```json
{
  "session_id": "session_001",
  "reply": "从简历来看，该候选人在Java领域有5年经验..."
}
```

## 快速开始

### 前置要求

- Python 3.11+
- MySQL 8.0+
- Node.js 18+
- AI API 密钥（Claude API 或兼容网关）

### 后端部署

1. **安装依赖**

```bash
cd backend
pip install -r requirements.txt
```

或使用 `pyproject.toml`：

```bash
cd backend
pip install .
```

2. **创建数据库**

```sql
CREATE DATABASE talent_pool CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=talent_pool

# AI 配置
ANTHROPIC_AUTH_TOKEN=your_api_key
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
ANTHROPIC_MODEL=qwen3.6-plus

# 简历目录（多个路径用逗号分隔，支持 UNC 网络路径）
RESUME_DIR=D:/path/to/resumes,\\\\192.168.x.x\简历资料夹

# 扫描间隔（秒）
SCAN_INTERVAL=300
```

4. **启动后端服务**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后会自动：
- 创建数据库表结构
- 启动定时扫描器（按 `SCAN_INTERVAL` 间隔自动扫描）

### 前端部署

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器默认运行在 `http://localhost:3000`，`/api` 请求自动代理到后端 `http://127.0.0.1:8000`。

生产构建：

```bash
npm run build
```

### 访问应用

- 前端界面: `http://localhost:3000`
- 后端 API: `http://localhost:8000`
- API 文档 (Swagger): `http://localhost:8000/docs`
- API 文档 (ReDoc): `http://localhost:8000/redoc`

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_HOST` | `127.0.0.1` | MySQL 主机地址 |
| `DB_PORT` | `3306` | MySQL 端口 |
| `DB_USER` | `root` | MySQL 用户名 |
| `DB_PASSWORD` | `""` | MySQL 密码 |
| `DB_NAME` | `talent_pool` | 数据库名 |
| `ANTHROPIC_AUTH_TOKEN` | `""` | AI API 密钥 |
| `ANTHROPIC_BASE_URL` | `""` | AI 网关基础 URL（留空使用官方 API） |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6-20251014` | AI 模型名称 |
| `RESUME_DIR` | `./resumes` | 简历目录路径（逗号分隔支持多目录） |
| `SCAN_INTERVAL` | `300` | 定时扫描间隔（秒） |
| `log_level` | `INFO` | 日志级别 |
| `log_format` | `%(asctime)s - ...` | 日志格式 |

### 多目录配置

`RESUME_DIR` 支持配置多个简历目录，逗号分隔：

```ini
RESUME_DIR=D:/简历资料,A:/备份简历,\\\\fileserver\hr\简历
```

- 本地路径：自动解析为绝对路径
- UNC 网络路径（`\\server\share`）：保持原始格式，不做路径解析

### AI 网关配置

支持通过网关代理访问 AI 服务，例如阿里云 DashScope：

```ini
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
ANTHROPIC_AUTH_TOKEN=your_dashscope_token
ANTHROPIC_MODEL=qwen3.6-plus
```

留空 `ANTHROPIC_BASE_URL` 则直接调用 Anthropic 官方 API。

## 核心模块详解

### 扫描服务 (scanner.py)

扫描指定目录下的简历文件，通过 SHA256 校验和识别文件变更。

- 支持格式：PDF、DOC、DOCX、PPT、PPTX
- 去重策略：路径唯一索引 + SHA256 内容哈希
- 状态流转：pending → processing → done / failed
- 失败重试：failed 状态的文件会在下次扫描时重新处理
- 内容变更检测：done 状态的文件如果内容变更（哈希不同），会标记为 pending 重新处理
- 并发控制：全局 `threading.Lock` 防止定时扫描和手动扫描竞争

### 解析服务 (parser.py)

多格式文本提取 + AI 解析编排。

**文本提取器：**

| 格式 | 提取方式 | 依赖 |
|------|----------|------|
| PDF | PyMuPDF 直接提取 | pymupdf |
| DOCX | python-docx 提取（含表格结构标记） | python-docx |
| DOC | LibreOffice 转为 DOCX 后提取 | libreoffice (系统级) |
| PPTX | python-pptx 提取 | python-pptx |
| PPT | LibreOffice 转为 PPTX 后提取 | libreoffice (系统级) |

**表格结构保留：**

DOCX/PPTX 中的表格文本使用 `[表格N]` 和 `[表格N 行M]` 标记保留结构信息，帮助 AI 识别智联招聘等模板中的工作经历、联系方式等表格区块。

### 预处理服务 (preprocessor.py)

轻量整理策略，核心原则：**宁可保留噪音，不可丢失信息**。

处理步骤：
1. **噪音清理**：仅删除明确的无信息内容（页码标记、纯空行、"个人简历"标题行）
2. **短行合并**：仅合并连续短行（<50字符），保留完整句子和关键段落标题
3. **段落提取**：尝试识别教育背景、工作经历、技能、自我评价等关键段落

### AI 服务 (ai.py)

封装 Claude API 调用，提供三种能力：

1. **结构化信息提取** (`extract_structured_info`)
   - 双层文本策略：原始文本保底 + 整理文本辅助
   - 表格结构识别：识别智联招聘等模板的单列/多列表格
   - 智能补全：从原始文本兜底推断缺失字段
   - 技能标准化：合并同义技能变体（如 "python3" → "Python"）

2. **岗位匹配推荐** (`generate_recommendation`)
   - 返回结构化 JSON：suitable / score / conclusion / reason
   - AI 被要求客观分析，不匹配时直接说"不合适"

3. **AI 对话** (`chat_completion`)
   - 支持传入简历上下文作为 system prompt 补充
   - 人事客服角色设定

### 搜索服务 (search.py)

混合搜索算法，结合关键词匹配和向量语义搜索。

**排序公式**：`综合分 = 关键词得分 × 0.4 + 语义得分 × 0.6`

- **关键词得分**：基于 SQL LIKE 匹配，姓名(0.5) + 职位(0.3) + 摘要(0.2) + 技能(0.3)
- **语义得分**：基于 ChromaDB 向量相似度排名
- **降级策略**：向量库不可用时自动降级为纯关键词搜索
- **筛选支持**：按技能列表筛选 + 按最低工作年限筛选

### 向量服务 (vector.py)

ChromaDB 向量索引管理。

- 持久化存储：数据保存在 `data/chroma_db/` 目录
- 搜索文本构建：组合姓名、职位、摘要、技能、教育、工作经历等字段
- 相似度度量：余弦相似度 (cosine)
- 异常处理：向量库不可用时返回空列表，搜索服务自动降级

## 前端页面

### 路由

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | HomeView | 首页：简历列表、搜索、筛选、批量删除、上传简历 |
| `/resume/:id` | DetailView | 简历详情、岗位匹配推荐 |
| `/chat` | ChatView | AI 对话界面 |
| `/recycle-bin` | RecycleBinView | 回收站：查看已删除简历、批量恢复 |

### 代理配置

Vite 开发服务器配置了 API 代理：

```js
server: {
  port: 3000,
  host: '0.0.0.0',
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
}
```

## 脚本工具

### 重处理失败的简历

```bash
python scripts/reprocess.py
```

该脚本会查找状态为 `failed` 的简历文件，重新执行解析流程。

## 开发指南

### 目录结构

```
talent-pool/
├── backend/                    # 后端 Python 项目
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 配置管理
│   │   ├── models/             # 数据模型 (ORM + Pydantic)
│   │   ├── routes/             # API 路由
│   │   └── services/           # 业务服务
│   ├── requirements.txt        # pip 依赖
│   ├── pyproject.toml          # 项目元数据
│   └── .env.example            # 环境变量模板
├── frontend/                   # 前端 Vue 3 项目
│   ├── src/
│   │   ├── main.js             # 应用入口
│   │   ├── App.vue             # 根组件
│   │   ├── api/index.js        # Axios API 封装
│   │   ├── router/index.js     # 路由配置
│   │   ├── types.js            # JSDoc 类型定义
│   │   └── views/              # 页面组件
│   ├── package.json
│   └── vite.config.js          # Vite 配置
├── scripts/                    # 工具脚本
│   └── reprocess.py            # 重处理失败简历
├── data/chroma_db/             # ChromaDB 向量数据 (git 忽略)
├── resumes/                    # 示例简历目录 (git 忽略)
├── .gitignore
└── CLAUDE.md                   # 项目开发指南
```

### 添加新的简历格式

1. 在 `parser.py` 中添加对应的文本提取函数
2. 在 `extract_text_by_extension` 的 `extractors` 字典中注册新格式
3. 在 `scanner.py` 的 `SUPPORTED_EXTENSIONS` 集合中添加扩展名

### 自定义 AI 提取提示词

编辑 `ai.py` 中的 `SYSTEM_EXTRACT_PROMPT` 常量，调整字段提取指南和输出格式。

### 调整搜索权重

编辑 `search.py` 中的 `SEMANTIC_WEIGHT` 和 `KEYWORD_WEIGHT` 常量，调整语义搜索和关键词搜索的权重比例。

## 常见问题

**Q: 向量搜索不可用的警告**

ChromaDB 需要下载 embedding 模型，首次运行时会自动下载。如果网络受限导致下载失败，搜索会自动降级为纯关键词模式，不影响核心功能。

**Q: DOC/PPT 格式无法解析**

旧版 `.doc` 和 `.ppt` 文件需要系统安装 LibreOffice 进行格式转换。确保 `libreoffice` 命令在 PATH 中可用。

**Q: AI 提取结果为 null**

可能原因：
- 简历文本过短（少于 50 字符）
- AI API 调用失败（检查网络和密钥配置）
- 简历格式特殊，AI 无法识别关键信息

**Q: 扫描不生效**

检查：
- `RESUME_DIR` 配置的路径是否正确
- 目录中是否有 PDF/DOCX/PPTX 文件
- 文件是否已被处理过（SHA256 哈希未变更）
- 查看后端日志输出

## License

MIT
