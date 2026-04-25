/**
 * 主题 Store — 管理当前主题状态，持久化到 localStorage
 */
import { ref, onMounted } from 'vue'

const STORAGE_KEY = 'app_theme'
const VALID_THEMES = ['business', 'minimal', 'apple', 'tech', 'glass']

// 默认主题
const DEFAULT_THEME = 'business'

// 响应式当前主题
const currentTheme = ref(DEFAULT_THEME)

/**
 * 应用主题到 DOM
 */
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
}

/**
 * 设置主题
 */
function setTheme(theme) {
  if (!VALID_THEMES.includes(theme)) return
  currentTheme.value = theme
  applyTheme(theme)
  localStorage.setItem(STORAGE_KEY, theme)
}

/**
 * 初始化：从 localStorage 恢复主题
 */
function initTheme() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved && VALID_THEMES.includes(saved)) {
    currentTheme.value = saved
    applyTheme(saved)
  } else {
    applyTheme(DEFAULT_THEME)
  }
}

export default {
  currentTheme,
  setTheme,
  initTheme,
  themes: VALID_THEMES,
}
