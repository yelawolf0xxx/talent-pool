# API 接口契约

> 本文档定义 AI 简历人才库系统前后端之间的 API 接口契约。
> 由 Backend Agent 与 Frontend Agent 共同确认。

---

## 统一响应信封

所有 API 响应遵循统一信封格式（列表类接口除外，见各端点说明）：

```json
{
  "success": true,
  "data": { ... },
  "message": null
}
```

错误响应：

```json
{
  "success": false,
  "data": null,
  "message": "错误描述"
}
```

分页元数据（`meta`）附加在列表响应的 `data` 对象中。

---

## 数据模型

### Resume（简历）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 简历唯一标识 |
| name | string \| null | 否 | 姓名 |
| email | string \| null | 否 | 邮箱 |
| phone | string \| null | 否 | 电话 |
| current_title | string \| null | 否 | 当前/最近职位 |
| years_exp | int \| null | 否 | 工作年限 |
| education | EducationItem[] | 是（默认 []） | 教育背景 |
| skills | string[] | 是（默认 []） | 技能列表 |
| work_experience | WorkExperienceItem[] | 是（默认 []） | 工作经历 |
| summary_text | string \| null | 否 | AI 生成的简历摘要 |
| file_path | string \| null | 否 | 原始 PDF 文件路径 |

### EducationItem

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| school | string | 是 | 学校名称 |
| degree | string | 是 | 学位 |
| major | string | 是 | 专业 |
| year | string \| null | 否 | 毕业年份 |

### WorkExperienceItem

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| company | string | 是 | 公司名称 |
| title | string | 是 | 职位 |
| start | string | 是 | 开始时间 |
| end | string \| null | 否 | 结束时间 |
| description | string \| null | 否 | 工作描述 |

### ChatMessage

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role | string | 是 | 角色："user" 或 "assistant" |
| content | string | 是 | 消息内容 |

---

## 端点定义

### 1. 健康检查

```
GET /health
```

**响应 200：**
```json
{ "status": "ok" }
```

---

### 2. 获取简历列表（分页）

```
GET /api/resumes?skip=0&limit=20
```

**查询参数：**

| 参数 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| skip | int | 0 | >= 0 | 偏移量 |
| limit | int | 20 | 1-100 | 每页数量 |

**响应 200：** ResumeListResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| items | Resume[] | 当前页简历列表 |
| total | int | 简历总数 |
| skip | int | 当前偏移量 |
| limit | int | 当前每页数量 |

```json
{
  "items": [Resume, ...],
  "total": 100,
  "skip": 0,
  "limit": 20
}
```

---

### 3. 获取简历详情

```
GET /api/resumes/{resume_id}
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| resume_id | int | 简历 ID |

**响应 200：** Resume 对象（直接使用数据模型，无信封包装）
```json
Resume
```

**响应 404：**
```json
{ "detail": "简历不存在" }
```

---

### 4. 搜索简历

```
POST /api/search
```

**请求体：** SearchRequest

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索关键词 |
| skills | string[] | 否 | [] | 技能筛选 |
| min_years_exp | int \| null | 否 | null | 最低工作年限 |

**响应 200：** SearchResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| total | int | 匹配总数 |
| results | SearchResultItem[] | 搜索结果列表 |

**SearchResultItem：**

| 字段 | 类型 | 说明 |
|------|------|------|
| resume | Resume | 简历数据 |
| score | float | 匹配度分数（0-1） |
| match_reasons | string[] | 匹配原因说明 |

---

### 5. AI 岗位匹配度分析

```
GET /api/resumes/{resume_id}/recommend?query=...
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| resume_id | int | 简历 ID |

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 岗位需求描述 |

**响应 200：** RecommendationResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| resume_id | int | 简历 ID |
| query | string | 原始岗位需求 |
| suitable | bool | 是否适合该岗位 |
| score | int | 匹配度分数（0-100） |
| conclusion | string | 一句话总结 |
| reason | string | 详细分析说明 |

---

### 6. AI 对话

```
POST /api/chat
```

**请求体：** ChatRequest

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| session_id | string | 是 | - | 会话标识 |
| messages | ChatMessage[] | 是 | - | 对话消息列表 |
| resume_id | int \| null | 否 | null | 关联的候选人 ID |

**响应 200：**
```json
{
  "session_id": "string",
  "reply": "string"
}
```

---

### 7. 手动触发简历扫描

```
POST /api/scan
```

**请求体：** 无

**响应 200：**
```json
{ "status": "started", "message": "扫描任务已启动" }
```

**响应 200（扫描进行中）：**
```json
{ "status": "running", "message": "扫描任务正在进行中" }
```

---

### 8. 获取扫描进度

```
GET /api/scan/status
```

**响应 200：** ScanProgress

| 字段 | 类型 | 说明 |
|------|------|------|
| active | bool | 是否有扫描任务在进行 |
| total | int | 待处理文件总数 |
| current | int | 当前处理进度 |
| processed | int | 已成功处理数量 |
| failed | int | 失败数量 |
| message | string | 状态描述信息 |

---

## 错误码约定

| HTTP 状态码 | 含义 |
|-------------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 请求体验证失败（Pydantic validation） |
| 500 | 服务器内部错误 |

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1 | 2026-04-15 | 初始契约，基于现有后端实现整理 |
