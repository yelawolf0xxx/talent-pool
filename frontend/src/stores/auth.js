import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, logout as apiLogout, getMe as apiGetMe } from '../api'

const STORAGE_KEY = 'auth_token'
const USER_KEY = 'auth_user'

// 状态
const token = ref(localStorage.getItem(STORAGE_KEY) || null)
const user = ref(localStorage.getItem(USER_KEY) ? JSON.parse(localStorage.getItem(USER_KEY)) : null)

// 计算属性
const isLoggedIn = computed(() => !!token.value)
const isAdmin = computed(() => user.value?.role === 'admin')

/**
 * 用户登录
 */
async function login(usernameOrEmail, password) {
  const res = await apiLogin(usernameOrEmail, password)
  const data = res.data
  token.value = data.access_token
  user.value = data.user
  localStorage.setItem(STORAGE_KEY, data.access_token)
  localStorage.setItem(USER_KEY, JSON.stringify(data.user))
  return data
}

/**
 * 用户注册
 */
async function register(username, email, password) {
  const res = await apiRegister(username, email, password)
  return res.data
}

/**
 * 用户登出
 */
function logout() {
  apiLogout().catch(() => {})
  token.value = null
  user.value = null
  localStorage.removeItem(STORAGE_KEY)
  localStorage.removeItem(USER_KEY)
  window.location.href = '/login'
}

/**
 * 获取当前用户信息（刷新）
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
  token,
  user,
  isLoggedIn,
  isAdmin,
  login,
  register,
  logout,
  fetchMe,
}
