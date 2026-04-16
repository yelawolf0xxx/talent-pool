import axios from 'axios'

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

// ── 简历 API ──────────────────────────────────────────

/**
 * 获取简历列表（分页）
 * @param {number} skip - 偏移量
 * @param {number} limit - 每页数量
 * @returns {Promise<import('axios').AxiosResponse<Resume[]>>}
 */
export function listResumes(skip = 0, limit = 20) {
  return api.get('/api/resumes', { params: { skip, limit } })
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
 * @returns {Promise<import('axios').AxiosResponse<SearchResponse>>}
 */
export function searchResumes(query, skills = [], minYearsExp = null) {
  return api.post('/api/search', {
    query,
    skills,
    min_years_exp: minYearsExp,
  })
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
 * 上传简历文件
 * @param {File} file - 简历文件
 * @returns {Promise<import('axios').AxiosResponse<{ filename: string, path: string }>>}
 */
export function uploadResume(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
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
