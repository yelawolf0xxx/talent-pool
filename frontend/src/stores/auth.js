import { readonly, ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, logout as apiLogout, getMe as apiGetMe } from '../api'

const STORAGE_KEY = 'auth_token'
const USER_KEY = 'auth_user'

/**
 * 认证状态 Store（轻量级单例，不依赖 Pinia）
 */

// 状态
const token = ref(localStorage.getItem(STORAGE_KEY) || null)
const user = ref(localStorage.getItem(USER_KEY) ? JSON.parse(localStorage.getItem(USER_KEY)) : null)

// 计算属性
const isLoggedIn = computed(() => !!token.value)
const isAdmin = computed(() => user.value?.role === 'admin')

/**
 * 用户登录
 * @param {string} usernameOrEmail - 用户名或邮箱
 * @param {string} password - 密码
 * @returns {Promise<{ token: string, user: object }>}
 */
async function login(usernameOrEmail, password) {
  const res = await apiLogin(usernameOrEmail, password)
  const { token: newToken, user: userData } = res.data
  token.value = newToken
  user.value = userData
  localStorage.setItem(STORAGE_KEY, newToken)
  localStorage.setItem(USER_KEY, JSON.stringify(userData))
  return res.data
}

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} email - 邮箱
 * @param {string} password - 密码
 * @returns {Promise<object>}
 */
async function register(username, email, password) {
  const res = await apiRegister(username, email, password)
  return res.data
}

/**
 * 用户登出
 */
function logout() {
  // 异步通知后端，不等待结果
  apiLogout().catch(() => {})
  token.value = null
  user.value = null
  localStorage.removeItem(STORAGE_KEY)
  localStorage.removeItem(USER_KEY)
  window.location.href = '/login'
}

/**
 * 获取当前用户信息（刷新）
 * @returns {Promise<object|null>}
 */
async function fetchMe() {
  if (!token.value) return null
  try {
    const res = await apiGetMe()
    user.value = res.data
    localStorage.setItem(USER_KEY, JSON.stringify(res.data))
    return res.data
  } catch {
    token.value = null
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export default {
  token: readonly(token),
  user: readonly(user),
  isLoggedIn,
  isAdmin,
  login,
  register,
  logout,
  fetchMe,
}
