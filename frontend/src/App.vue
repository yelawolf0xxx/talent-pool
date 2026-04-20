<template>
  <div id="app-root">
    <el-container>
      <el-header>
        <div class="header-content">
          <router-link to="/" class="logo">
            <el-icon><User /></el-icon>
            <span>AI 人才库</span>
          </router-link>
          <el-menu mode="horizontal" :ellipsis="false" router>
            <el-menu-item index="/">简历搜索</el-menu-item>
            <el-menu-item index="/chat">AI 助手</el-menu-item>
            <el-menu-item index="/recycle-bin">回收站</el-menu-item>
          </el-menu>

          <!-- 右侧用户区域 -->
          <div class="user-area">
            <!-- 主题切换 -->
            <ThemeSwitcher />

            <!-- 管理员可见：更新人才库 -->
            <el-button
              v-if="authStore.isAdmin"
              type="primary"
              :loading="scanning"
              :disabled="scanning"
              @click="handleScan"
            >
              <el-icon><Refresh /></el-icon>
              更新人才库
            </el-button>

            <!-- 未登录：显示登录/注册 -->
            <template v-if="!authStore.isLoggedIn">
              <el-button @click="$router.push('/login')">登录</el-button>
              <el-button type="primary" @click="$router.push('/register')">注册</el-button>
            </template>

            <!-- 已登录：显示用户菜单 -->
            <el-dropdown v-else @command="handleUserCommand">
              <span class="user-name">{{ authStore.user?.username || '用户' }}</span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="email-config">邮箱管理</el-dropdown-item>
                  <el-dropdown-item v-if="authStore.isAdmin" command="admin">管理后台</el-dropdown-item>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>

    <!-- 扫描进度弹窗 -->
    <el-dialog
      v-model="showProgress"
      title="更新人才库"
      width="400px"
      :close-on-click-modal="false"
      :show-close="false"
      :close-on-press-escape="false"
    >
      <div class="scan-progress">
        <el-progress
          :percentage="percent"
          :status="scanDone ? (scanFailed ? 'exception' : 'success') : ''"
          :stroke-width="20"
        />
        <p class="scan-status">{{ scanMessage }}</p>
        <p v-if="scanTotal > 0" class="scan-detail">
          共 {{ scanTotal }} 份，已处理 {{ scanCurrent }} 份
          <span v-if="scanProcessed > 0">（成功 {{ scanProcessed }} 份</span>
          <span v-if="scanFailed > 0">，失败 {{ scanFailed }} 份</span>
          <span v-if="scanProcessed > 0 || scanFailed > 0">）</span>
        </p>
      </div>
      <template #footer>
        <el-button type="primary" :disabled="!scanDone" @click="showProgress = false">
          {{ scanDone ? '完成' : '处理中...' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { manualScan, getScanStatus } from './api'
import { ElMessage } from 'element-plus'
import authStore from './stores/auth'
import ThemeSwitcher from './components/ThemeSwitcher.vue'

const router = useRouter()

const scanning = ref(false)
const showProgress = ref(false)
const scanTotal = ref(0)
const scanCurrent = ref(0)
const scanProcessed = ref(0)
const scanFailedCount = ref(0)
const scanMessage = ref('')
const scanDone = ref(false)

const scanFailed = computed(() => scanFailedCount.value > 0)
const percent = computed(() => {
  if (scanTotal.value === 0) return 0
  return Math.round((scanCurrent.value / scanTotal.value) * 100)
})

let pollTimer = null

/**
 * 处理用户下拉菜单命令
 */
function handleUserCommand(command) {
  if (command === 'admin') {
    router.push('/admin')
  } else if (command === 'email-config') {
    router.push('/email-config')
  } else if (command === 'logout') {
    authStore.logout()
  }
}

/**
 * 处理扫描
 */
async function handleScan() {
  if (scanning.value) return
  scanning.value = true

  try {
    const { data } = await manualScan()
    if (data.status === 'running') {
      ElMessage.info(data.message)
      return
    }

    // 显示进度弹窗，开始轮询
    showProgress.value = true
    scanTotal.value = 0
    scanCurrent.value = 0
    scanProcessed.value = 0
    scanFailedCount.value = 0
    scanMessage.value = data.message
    scanDone.value = false

    startPolling()
  } catch (e) {
    ElMessage.error('启动扫描失败：' + (e.response?.data?.detail || e.message))
  } finally {
    scanning.value = false
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const { data } = await getScanStatus()
      scanTotal.value = data.total || 0
      scanCurrent.value = data.current || 0
      scanProcessed.value = data.processed || 0
      scanFailedCount.value = data.failed || 0
      scanMessage.value = data.message || ''
      scanDone.value = !data.active

      if (scanDone.value) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    } catch {
      // 轮询失败不中断，继续尝试
    }
  }, 1000)
}
</script>

<style>
body {
  margin: 0;
  font-family: var(--font-sans);
  background: var(--bg-page);
  color: var(--text-primary);
  transition: background var(--transition-slow), color var(--transition-slow);
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  gap: 24px;
}

.user-area {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  color: var(--color-primary);
  cursor: pointer;
  font-size: 14px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 700;
  color: var(--logo-color);
  text-decoration: none;
}

.el-header {
  background: var(--bg-surface);
  box-shadow: var(--shadow-header);
  padding: 0 24px;
}

.el-main {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

#app-root {
  min-height: 100vh;
}

.scan-progress {
  text-align: center;
  padding: 12px 0;
}

.scan-status {
  margin: 12px 0 4px;
  font-size: 14px;
  color: var(--text-primary);
}

.scan-detail {
  margin: 4px 0;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
