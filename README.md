# AI 简历人才库系统

> 自动扫描 PDF/DOC/PPT 简历目录，使用 AI 提取结构化信息，存储到 MySQL 数据库，通过 ChromaDB 向量库实现语义搜索，并提供简历管理、岗位匹配分析和 AI 对话功能。支持账号认证、管理员后台和邮箱自动抓取简历。

## 更新记录

### 2026-04-20（三） — 邮箱同步后自动解析 + 全部邮件功能

**Bug 修复：**

- **修复邮箱同步后简历不自动解析**：邮箱同步下载附件完成后，立即触发一次扫描解析（`scan_resume_directory` + `parse_resume`），无需等待定时任务（5 分钟）
- **修复 Scanner 不递归搜索子目录**：`glob` 改为 `rglob`，使 scanner 能发现邮箱同步保存到子目录（`email_xxx/YYYY-MM-DD/`）中的简历文件

**新增功能：**

- **全部邮件列表（管理员专属）**：邮箱管理新增"全部邮件"Tab，通过 IMAP 实时获取邮件列表，支持分页、搜索、已读/未读标识
- **邮件详情查看**：点击邮件行可查看详情弹窗，展示发件人、日期、正文预览和附件列表
- **权限控制**：后端 API 使用 `require_admin` 装饰器，前端 Tab 仅对管理员可见

### 2026-04-20（二） — Tab 切换修复 + 简历卡片布局优化 + 主题切换

**Bug 修复：**

- **修复 Tab 切换后内容为空**：将 `@tab-click` 事件改为 `watch(activeTab)` 监听，解决 Element Plus `el-tabs` 在某些情况下不触发 `@tab-click` 事件导致切换回"全部简历"tab 后数据不加载的问题
- **修复无限滚动**：重写 IntersectionObserver 绑定逻辑，在数据加载完成后才绑定滚动观察器，避免时序问题导致滚动不生效
- **修复简历卡片布局重叠**：候选人姓名与岗位名称重叠、checkbox 与头像堆叠的 CSS 布局问题

**新增功能：**

- **主题切换**：支持亮色/暗色主题切换，新增 ThemeSwitcher 组件和主题样式系统

**代码优化：**

- 新增 `stores/` 目录管理全局状态（主题、认证）
- 新增 `styles/themes.css` 集中管理主题变量
- 新增 `components/ThemeSwitcher.vue` 主题切换组件

### 2026-04-20 — AI 助手候选人推荐 + Markdown 渲染 + 一键启动

**新增功能：**

- **AI 助手候选人推荐**：AI 对话现在能够基于真实人才库数据推荐候选人。当用户提问包含推荐意图时，系统自动检索人才库并将匹配结果注入对话上下文，AI 基于真实数据作答
- **意图识别**：内置推荐意图关键词检测，自动区分"推荐候选人"和"一般咨询"两类问题
- **Markdown 渲染**：AI 回复支持 Markdown 格式（粗体、列表、标题等），提升回复易读性

**新增脚本：**

- `start.bat`：Windows 一键启动脚本，同时启动前后端服务

**AI 对话增强：**

- 推荐意图问题（如"推荐 Java 候选人"）→ 自动检索人才库，AI 基于真实数据推荐
- 一般咨询问题（如"如何面试"）→ 保持原有行为，不触发检索

### 2026-04-17（二） — 邮箱配置下放普通用户 + 首页"我的简历/全部简历"切换

**新增功能：**

- **邮箱配置下放普通用户**：每个已登录用户均可配置自己的 IMAP 邮箱，管理个人邮箱抓取
- **首页 Tab 切换**：默认展示"我的简历"（从个人邮箱同步的简历），可切换"全部简历"查看所有来源
- **用户端邮箱管理页面**：新增 `/email-config` 路由，支持新增/编辑/删除邮箱配置、手动同步、查看同步日志
- **简历归属追踪**：`resume_files` 表新增 `uploader_id` 字段，`resumes` 表通过 `uploaded_by` 关联归属用户
- **邮箱同步路径标识**：同步文件保存到 `resume_dir/email_{user[at]domain}/YYYY-MM-DD/`，scanner 自动识别归属用户

**数据库变更：**

- `email_configs` 表新增 `user_id INT FK → users.id, nullable=True`
- `resume_files` 表新增 `uploader_id INT FK → users.id, nullable=True`

**新增 API：**

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/user/email-configs` | 获取当前用户的邮箱配置 | 需登录 |
| POST | `/api/user/email-configs` | 创建/更新当前用户的邮箱配置 | 需登录 |
| DELETE | `/api/user/email-configs/{id}` | 删除当前用户的邮箱配置 | 需登录 |
| POST | `/api/user/email-sync/{id}` | 手动触发当前用户的邮箱同步 | 需登录 |
| GET | `/api/user/email-sync-logs` | 当前用户的同步日志 | 需登录 |

**修改 API：**

- `GET /api/resumes` 新增 `mine=true` 查询参数，仅返回当前用户的简历
- `POST /api/search` 新增 `mine=true` 查询参数，仅搜索当前用户的简历

### 2026-04-17 — 账号系统 + 管理员端 + 邮箱自动抓取

**新增功能：**

- **账号认证系统**：用户注册/登录，JWT Token 认证，bcrypt 密码加密
- **角色权限分权**：管理员（Admin）和普通用户（User）两种角色
- **管理员面板**：用户管理、登录日志、操作日志、系统状态监控、邮箱配置
- **邮箱自动抓取**：IMAP 定时扫描邮箱，提取附件简历，按日期分类下载至网络路径
- **操作审计**：所有关键操作（上传、删除、恢复、扫描）均记录操作日志
- **登录审计**：所有登录尝试（成功/失败）均记录登录日志

**新增数据库表：** `users`、`login_logs`、`operation_logs`、`email_configs`、`email_sync_logs`

**新增环境变量：** `JWT_SECRET`、`JWT_EXPIRE_HOURS`、`EMAIL_SYNC_INTERVAL`、`EMAIL_ENCRYPTION_KEY`

**新增依赖：** `python-jose[cryptography]`、`bcrypt`、`passlib[bcrypt]`、`cryptography`

### 2026-04-16 — 批量上传 + 软删除/回收站 + 搜索修复

- 批量多选上传简历文件
- 软删除 + 回收站 + 批量恢复
- 修复按技能筛选和最低年限筛选的搜索 bug

---

## 功能特性

- **自动扫描**：定时扫描指定目录（含 UNC 网络路径），自动检测新增/变更的简历文件
- **多格式解析**：支持 PDF、DOC、DOCX、PPT、PPTX 格式的简历文件
- **AI 结构化提取**：使用大语言模型从非结构化简历中提取姓名、技能、教育背景、工作经历等
- **混合搜索**：结合 SQL 关键词匹配与 ChromaDB 向量语义搜索，按加权分数排序
- **岗位匹配分析**：输入岗位需求描述，AI 生成匹配度评分和推荐理由
- **AI 对话**：针对特定候选人进行多轮对话，或让 AI 从人才库中推荐匹配候选人
- **AI 智能推荐**：支持自然语言提问推荐候选人（如"推荐有 Java 经验的候选人"），AI 自动检索人才库并基于真实数据作答
- **Markdown 渲染**：AI 回复支持 Markdown 格式，排版清晰易读
- **多目录支持**：可同时监控多个简历存放目录
- **账号认证**：JWT Token 认证，支持用户名/邮箱登录
- **权限分权**：管理员可管理用户、查看日志、配置邮箱抓取
- **邮箱自动抓取**：IMAP 定时扫描，自动提取邮件附件简历
- **操作审计**：关键操作自动记录日志，支持管理员追溯

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
| uploader_id | INT FK → users.id | 上传者（邮箱同步时设置） |

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

### users（用户账号表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| username | VARCHAR(50) UNIQUE | 用户名 |
| email | VARCHAR(200) UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | bcrypt 加密密码 |
| role | VARCHAR(20) | 角色: admin/user |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 注册时间 |
| updated_at | DATETIME | 更新时间 |

索引: `idx_username`, `idx_email`

### login_logs（登录日志表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| user_id | INT FK → users.id | 关联用户 |
| ip_address | VARCHAR(45) | 登录 IP |
| user_agent | VARCHAR(500) | 浏览器/设备信息 |
| status | VARCHAR(20) | success/failed |
| created_at | DATETIME | 登录时间 |

索引: `idx_user_id`, `idx_created_at`

### operation_logs（操作日志表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| user_id | INT FK → users.id | 操作用户 |
| action | VARCHAR(100) | 操作类型 |
| resource_type | VARCHAR(50) | 资源类型 |
| resource_id | INT | 资源 ID |
| detail | TEXT | 操作详情 JSON |
| created_at | DATETIME | 操作时间 |

索引: `idx_user_id`, `idx_created_at`

### email_configs（邮箱配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| user_id | INT FK → users.id | 关联用户（可选，管理员配置可为空） |
| imap_server | VARCHAR(200) | IMAP 服务器地址 |
| imap_port | INT | IMAP 端口，默认 993 |
| email_address | VARCHAR(200) | 邮箱地址 |
| password_encrypted | VARCHAR(500) | 加密后的授权码 |
| is_enabled | BOOLEAN | 是否启用 |
| download_dir | VARCHAR(512) | 下载目录（UNC 路径备份） |
| last_sync_at | DATETIME | 上次同步时间 |
| created_at | DATETIME | 创建时间 |

### email_sync_logs（邮箱同步日志表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| email_config_id | INT FK → email_configs.id | 关联配置 |
| total_emails | INT | 扫描邮件总数 |
| new_attachments | INT | 新附件数量 |
| downloaded | INT | 成功下载数量 |
| failed | INT | 失败数量 |
| status | VARCHAR(20) | success/failed/partial |
| message | TEXT | 执行详情 |
| created_at | DATETIME | 同步时间 |

---

## API 参考

### 认证

**用户注册**

```
POST /api/auth/register
Content-Type: application/json

{"username": "zhangsan", "email": "zhang@example.com", "password": "123456"}
```

返回: `{"id": 1, "username": "zhangsan", "email": "zhang@example.com", "role": "user"}`

**用户登录**

```
POST /api/auth/login
Content-Type: application/json

{"username_or_email": "zhangsan", "password": "123456"}
```

返回:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {"id": 1, "username": "zhangsan", "email": "zhang@example.com", "role": "user"}
}
```

**获取当前用户**（需 Token）

```
GET /api/auth/me
Authorization: Bearer <token>
```

**退出登录**

```
POST /api/auth/logout
```

### 管理员 API（需 Admin 角色）

**用户列表**

```
GET /api/admin/users?skip=0&limit=20
```

**编辑用户**

```
PATCH /api/admin/users/{id}
Content-Type: application/json

{"is_active": false}  或  {"role": "admin"}
```

**登录日志**

```
GET /api/admin/login-logs?skip=0&limit=50&user_id=1
```

**操作日志**

```
GET /api/admin/operation-logs?skip=0&limit=50&user_id=1&action=upload_resume
```

**系统状态**

```
GET /api/admin/system-status
```

返回:
```json
{
  "database": "connected",
  "total_users": 5,
  "total_resumes": 120,
  "scan_active": false,
  "uptime": "2d 5h 30m"
}
```

**邮箱配置列表**

```
GET /api/admin/email-configs
```

**创建/更新邮箱配置**

```
POST /api/admin/email-configs
Content-Type: application/json

{
  "imap_server": "imap.example.com",
  "imap_port": 993,
  "email_address": "hr@example.com",
  "password": "your_authorization_code",
  "download_dir": "\\\\192.168.3.30\\简历资料夹"
}
```

**手动触发邮箱同步**

```
POST /api/admin/email-sync/{config_id}
```

**同步日志**

```
GET /api/admin/email-sync-logs?skip=0&limit=20
```

### 用户端 API（需登录）

**获取我的邮箱配置**

```
GET /api/user/email-configs
```

**创建/更新我的邮箱配置**

```
POST /api/user/email-configs
Content-Type: application/json

{
  "imap_server": "imap.example.com",
  "imap_port": 993,
  "email_address": "my@example.com",
  "password": "your_authorization_code",
  "download_dir": "\\\\192.168.3.30\\简历资料夹"
}
```

**删除我的邮箱配置**

```
DELETE /api/user/email-configs/{config_id}
```

**手动触发我的邮箱同步**

```
POST /api/user/email-sync/{config_id}
```

**我的同步日志**

```
GET /api/user/email-sync-logs?skip=0&limit=20
```

**获取简历列表**

```
GET /api/resumes?skip=0&limit=20&mine=false
```

参数 `mine=true` 时仅返回当前用户的简历。

**搜索简历**

```
POST /api/search
Content-Type: application/json

{
  "query": "Java后端开发",
  "skills": ["Java", "Spring Boot"],
  "min_years_exp": 3
}
```

查询参数 `?mine=true` 时仅搜索当前用户的简历。

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

**AI 智能推荐功能**：

当用户消息包含候选人推荐意图时（如"推荐 Java 候选人"、"找有前端经验的人"），系统会自动：

1. 使用混合搜索算法检索人才库中匹配的候选人
2. 将匹配结果（最多 10 条）注入对话上下文
3. AI 基于真实数据给出推荐回答

支持的推荐意图关键词：推荐、筛选、找、有哪些、多少人、合适、匹配、人才库、候选人，以及常见技术栈名称（Java、Python、前端、后端等）。

**示例：**

```json
{"session_id": "s1", "messages": [{"role": "user", "content": "推荐有 Java 开发经验的候选人"}]}
```

AI 回复示例：

```
根据您的需求，为您推荐以下候选人：

1. **张三** - Java 开发工程师 - 3年经验
   技能：Java, Spring Boot, MySQL, Redis
   亮点：精通微服务架构，独立负责订单系统重构

2. **李四** - 后端开发工程师 - 5年经验
   技能：Java, Spring Cloud, Docker, K8s
   亮点：有高并发系统经验，日均百万级请求
```

## 快速开始

### 前置要求

- Python 3.11+
- MySQL 8.0+
- Node.js 18+
- AI API 密钥（Claude API 或兼容网关）

### 快速启动

**Windows 一键启动：**

双击项目根目录下的 `start.bat` 脚本，自动同时启动前后端服务。

**手动启动：**

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

> 前端依赖 `markdown-it` 用于渲染 AI 回复的 Markdown 格式内容。

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
| `JWT_SECRET` | `change-me` | JWT 签名密钥（生产环境务必修改） |
| `JWT_EXPIRE_HOURS` | `24` | Token 有效期（小时） |
| `EMAIL_SYNC_INTERVAL` | `86400` | 邮箱同步间隔（秒），默认 24 小时 |
| `EMAIL_ENCRYPTION_KEY` | 自动生成 | Fernet 加密密钥，用于加密邮箱密码 |
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
   - **RAG 增强**：对话时自动检索人才库，将匹配候选人注入上下文，实现基于真实数据的推荐

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

| 路径 | 组件 | 权限 | 说明 |
|------|------|------|------|
| `/login` | LoginView | 访客 | 登录页面 |
| `/register` | RegisterView | 访客 | 注册页面 |
| `/` | HomeView | 需登录 | 首页：我的简历/全部简历 Tab、搜索、上传、批量删除 |
| `/resume/:id` | DetailView | 需登录 | 简历详情、岗位匹配推荐 |
| `/chat` | ChatView | 需登录 | AI 对话界面（支持 Markdown 渲染、人才库智能推荐） |
| `/email-config` | EmailConfigView | 需登录 | 邮箱管理：配置 IMAP、手动同步、同步日志 |
| `/recycle-bin` | RecycleBinView | 需管理员 | 回收站：查看已删除简历、批量恢复 |
| `/admin` | AdminView | 需管理员 | 管理后台：用户管理、日志、系统状态、邮箱配置 |

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

**Q: 默认管理员账号是什么？**

系统首次启动时会自动创建默认管理员账号：
- 用户名: `admin`
- 密码: `admin123`

**请立即修改默认密码。** 启动后使用管理员权限在管理后台修改密码。

**Q: 邮箱抓取不工作**

检查：
- IMAP 服务器地址和端口是否正确
- 邮箱授权码是否有效（非登录密码）
- 邮箱配置是否已启用（`is_enabled = true`）
- 查看 `/api/admin/email-sync-logs` 中的同步日志

**Q: Token 过期怎么办？**

Token 默认有效期 24 小时（可通过 `JWT_EXPIRE_HOURS` 调整）。过期后需重新登录。前端会在收到 401 响应时自动清除 token 并跳转登录页。

**Q: "我的简历"和"全部简历"有什么区别？**

"我的简历" Tab 仅显示从你配置的邮箱中同步抓取到的简历（通过 `uploaded_by` 字段过滤）。"全部简历" Tab 显示系统中所有来源的简历，包括手动上传和其他用户邮箱同步的简历。

**Q: 普通用户如何配置邮箱同步？**

登录后点击顶部导航栏的用户名，选择"邮箱管理"，进入邮箱管理页面。点击"新增邮箱配置"，填写 IMAP 服务器、邮箱地址和授权码，保存后即可手动触发同步。同步后的简历文件会自动出现在"我的简历" Tab 中。

## License

MIT
