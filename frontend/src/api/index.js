import axios from 'axios'
import { ElMessage } from 'element-plus'

/**
 * @typedef {import('../types').Resume} Resume
 * @typedef {import('../types').SearchResponse} SearchResponse
 * @typedef {import('../types').Recommendation} Recommendation
 * @typedef {import('../types').ChatResponse} ChatResponse
 * @typedef {import('../types').ScanStatus} ScanStatus
 * @typedef {import('../types').ScanStartResponse} ScanStartResponse
 */

/**
 * Axios 实例配置
 */
const api = axios.create({
  baseURL: '',
  timeout: 30000,
})

// ── 请求拦截器：自动附加 Authorization header ──────────

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── 响应拦截器：401/403 处理 ────────────────────────────

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      window.location.href = '/login'
    }
    if (error.response?.status === 403) {
      ElMessage.error('权限不足，无法执行此操作')
    }
    return Promise.reject(error)
  }
)

// ── 认证 API ──────────────────────────────────────────

/**
 * 用户登录
 * @param {string} usernameOrEmail - 用户名或邮箱
 * @param {string} password - 密码
 */
export function login(usernameOrEmail, password) {
  return api.post('/api/auth/login', { username_or_email: usernameOrEmail, password })
}

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} email - 邮箱
 * @param {string} password - 密码
 */
export function register(username, email, password) {
  return api.post('/api/auth/register', { username, email, password })
}

/**
 * 用户登出
 */
export function logout() {
  return api.post('/api/auth/logout')
}

/**
 * 获取当前用户信息
 */
export function getMe() {
  return api.get('/api/auth/me')
}

// ── 管理员 API ────────────────────────────────────────

/**
 * 获取用户列表
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 */
export function listUsers(skip = 0, limit = 20) {
  return api.get('/api/admin/users', { params: { skip, limit } })
}

/**
 * 更新用户信息
 * @param {number|string} id - 用户 ID
 * @param {object} data - 更新数据
 */
export function updateUser(id, data) {
  return api.patch(`/api/admin/users/${id}`, data)
}

/**
 * 获取登录日志
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 * @param {number|string|null} userId - 按用户筛选
 */
export function listLoginLogs(skip = 0, limit = 50, userId = null) {
  const params = { skip, limit }
  if (userId) params.user_id = userId
  return api.get('/api/admin/login-logs', { params })
}

/**
 * 获取操作日志
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 * @param {number|string|null} userId - 按用户筛选
 * @param {string|null} action - 按操作筛选
 */
export function listOperationLogs(skip = 0, limit = 50, userId = null, action = null) {
  const params = { skip, limit }
  if (userId) params.user_id = userId
  if (action) params.action = action
  return api.get('/api/admin/operation-logs', { params })
}

/**
 * 获取系统状态
 */
export function getSystemStatus() {
  return api.get('/api/admin/system-status')
}

/**
 * 获取邮件配置列表
 */
export function listEmailConfigs() {
  return api.get('/api/admin/email-configs')
}

/**
 * 创建邮件配置
 * @param {object} data - 配置数据
 */
export function createEmailConfig(data) {
  return api.post('/api/admin/email-configs', data)
}

/**
 * 删除邮件配置
 * @param {number|string} id - 配置 ID
 */
export function deleteEmailConfig(id) {
  return api.delete(`/api/admin/email-configs/${id}`)
}

/**
 * 同步邮件配置
 * @param {number|string} id - 配置 ID
 */
export function syncEmailConfig(id) {
  return api.post(`/api/admin/email-sync/${id}`)
}

/**
 * 获取邮件同步日志
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 */
export function listEmailSyncLogs(skip = 0, limit = 20) {
  return api.get('/api/admin/email-sync-logs', { params: { skip, limit } })
}

// ── 管理员：邮件列表 API ──────────────────────────────

/**
 * 获取指定邮箱的邮件列表（实时 IMAP 查询）
 * @param {number} configId - 邮箱配置 ID
 * @param {number} page - 页码
 * @param {number} pageSize - 每页数量
 * @param {string} search - 搜索关键词
 */
export function listAdminEmails(configId, page = 1, pageSize = 20, search = '') {
  return api.get('/api/admin/emails', { params: { config_id: configId, page, page_size: pageSize, search } })
}

/**
 * 获取单封邮件详情（实时 IMAP 查询）
 * @param {number} configId - 邮箱配置 ID
 * @param {string} uid - 邮件 UID
 */
export function getAdminEmailDetail(configId, uid) {
  return api.get(`/api/admin/emails/${uid}`, { params: { config_id: configId } })
}

// ── 用户端：邮箱 API ─────────────────────────────────

/**
 * 获取当前用户的邮箱配置列表
 */
export function listMyEmailConfigs() {
  return api.get('/api/user/email-configs')
}

/**
 * 创建/更新当前用户的邮箱配置
 * @param {object} data - 配置数据
 */
export function createMyEmailConfig(data) {
  return api.post('/api/user/email-configs', data)
}

/**
 * 删除当前用户的邮箱配置
 * @param {number|string} id - 配置 ID
 */
export function deleteMyEmailConfig(id) {
  return api.delete(`/api/user/email-configs/${id}`)
}

/**
 * 手动触发当前用户的邮箱同步
 * @param {number|string} id - 配置 ID
 */
export function syncMyEmailConfig(id) {
  return api.post(`/api/user/email-sync/${id}`)
}

/**
 * 获取当前用户的邮箱同步日志
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 */
export function listMyEmailSyncLogs(skip = 0, limit = 20) {
  return api.get('/api/user/email-sync-logs', { params: { skip, limit } })
}

// ── 简历 API ──────────────────────────────────────────

/**
 * 获取简历列表（分页）
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 * @param {boolean} mine - 仅显示当前用户的简历
 * @returns {Promise<import('axios').AxiosResponse<Resume[]>>}
 */
export function listResumes(skip = 0, limit = 20, mine = false) {
  return api.get('/api/resumes', { params: { skip, limit, mine } })
}

/**
 * 获取简历详情
 * @param {number|string} id - 简历 ID
 * @returns {Promise<import('axios').AxiosResponse<Resume>>}
 */
export function getResume(id) {
  return api.get(`/api/resumes/${id}`)
}

// ── 搜索 API ──────────────────────────────────────────

/**
 * 搜索候选人
 * @param {string} query - 搜索关键词
 * @param {string[]} skills - 技能筛选
 * @param {number|null} minYearsExp - 最低工作年限
 * @param {boolean} mine - 仅搜索当前用户的简历
 * @returns {Promise<import('axios').AxiosResponse<SearchResponse>>}
 */
export function searchResumes(query, skills = [], minYearsExp = null, mine = false) {
  return api.post('/api/search', {
    query,
    skills,
    min_years_exp: minYearsExp,
  }, { params: { mine } })
}

/**
 * 获取 AI 推荐理由
 * @param {number|string} resumeId - 简历 ID
 * @param {string} query - 岗位需求描述
 * @returns {Promise<import('axios').AxiosResponse<Recommendation>>}
 */
export function getRecommendation(resumeId, query) {
  return api.get(`/api/resumes/${resumeId}/recommend`, {
    params: { query },
    timeout: 120000,
  })
}

// ── 对话 API ──────────────────────────────────────────

/**
 * AI 对话
 * @param {{ role: string, content: string }[]} messages - 对话消息列表
 * @param {string} sessionId - 会话标识
 * @param {number|string|null} resumeId - 关联简历 ID
 * @returns {Promise<import('axios').AxiosResponse<ChatResponse>>}
 */
export function chat(messages, sessionId, resumeId = null) {
  return api.post('/api/chat', {
    messages,
    session_id: sessionId,
    resume_id: resumeId,
  })
}

// ── 扫描 API ──────────────────────────────────────────

/**
 * 手动触发简历扫描
 * @returns {Promise<import('axios').AxiosResponse<ScanStartResponse>>}
 */
export function manualScan() {
  return api.post('/api/scan')
}

/**
 * 获取扫描进度
 * @returns {Promise<import('axios').AxiosResponse<ScanStatus>>}
 */
export function getScanStatus() {
  return api.get('/api/scan/status')
}

// ── 上传 / 软删除 / 回收站 API ──────────────────────────

/**
 * 批量上传简历文件
 * @param {File[]} files - 简历文件列表
 * @returns {Promise<import('axios').AxiosResponse<{ uploaded: string[], failed: { filename: string, reason: string }[] }>>}
 */
export function uploadResume(files) {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  return api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

/**
 * 批量软删除简历
 * @param {number[]} ids - 简历 ID 列表
 * @returns {Promise<import('axios').AxiosResponse<{ deleted: number }>>}
 */
export function deleteBatch(ids) {
  return api.post('/api/resumes/delete', { ids })
}

/**
 * 批量恢复已删除的简历
 * @param {number[]} ids - 简历 ID 列表
 * @returns {Promise<import('axios').AxiosResponse<{ restored: number }>>}
 */
export function restoreBatch(ids) {
  return api.post('/api/resumes/restore', { ids })
}

/**
 * 获取回收站中的简历列表
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 * @returns {Promise<import('axios').AxiosResponse<{ total: number, items: any[] }>>}
 */
export function listRecycleBin(skip = 0, limit = 20) {
  return api.get('/api/recycle-bin', { params: { skip, limit } })
}

export default api
