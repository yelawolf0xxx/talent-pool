/**
 * @typedef {Object} EducationItem
 * @property {string} school - 学校名称
 * @property {string} degree - 学历
 * @property {string} major - 专业
 * @property {string} [year] - 毕业年份
 */

/**
 * @typedef {Object} WorkExperienceItem
 * @property {string} company - 公司名称
 * @property {string} title - 职位
 * @property {string} start - 开始时间
 * @property {string|null} [end] - 结束时间，null 表示至今
 * @property {string} [description] - 工作描述
 */

/**
 * @typedef {Object} Resume
 * @property {number} id - 主键
 * @property {string|null} [name] - 姓名
 * @property {string|null} [email] - 邮箱
 * @property {string|null} [phone] - 电话
 * @property {string|null} [current_title] - 当前职位
 * @property {number|null} [years_exp] - 工作年限
 * @property {EducationItem[]} education - 教育背景
 * @property {string[]} skills - 技能列表
 * @property {WorkExperienceItem[]} work_experience - 工作经历
 * @property {string|null} [summary_text] - AI 摘要
 * @property {string|null} [file_path] - PDF 路径
 */

/**
 * @typedef {Object} SearchResultItem
 * @property {Resume} resume - 简历对象
 * @property {number} score - 匹配度 0-1
 * @property {string[]} match_reasons - 匹配原因
 */

/**
 * @typedef {Object} SearchResponse
 * @property {number} total - 结果总数
 * @property {SearchResultItem[]} results - 搜索结果
 */

/**
 * @typedef {Object} Recommendation
 * @property {number} resume_id - 简历 ID
 * @property {string} query - 原始查询
 * @property {boolean} suitable - 是否适合
 * @property {number} score - 匹配度 0-100
 * @property {string} conclusion - 一句话结论
 * @property {string} reason - 详细分析
 */

/**
 * @typedef {Object} ChatMessage
 * @property {'user'|'assistant'} role - 角色
 * @property {string} content - 消息内容
 */

/**
 * @typedef {Object} ChatResponse
 * @property {string} session_id - 会话标识
 * @property {string} reply - AI 回复
 */

/**
 * @typedef {Object} ScanStatus
 * @property {boolean} active - 是否正在扫描
 * @property {number} total - 待处理总数
 * @property {number} current - 已处理数量
 * @property {number} processed - 成功数量
 * @property {number} failed - 失败数量
 * @property {string} message - 状态描述
 */

/**
 * @typedef {Object} ScanStartResponse
 * @property {'started'|'running'} status - 状态
 * @property {string} message - 提示消息
 */

/**
 * @typedef {Object} ApiError
 * @property {string} detail - 错误描述
 */

export {}
