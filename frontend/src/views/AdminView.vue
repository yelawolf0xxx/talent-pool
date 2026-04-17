<template>
  <div class="admin-view">
    <h2 class="admin-title">管理后台</h2>

    <el-tabs v-model="activeTab" type="card">
      <!-- Tab 1: 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <el-table :data="users" v-loading="usersLoading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="username" label="用户名" width="140" />
          <el-table-column prop="email" label="邮箱" width="200" />
          <el-table-column prop="role" label="角色" width="80">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
                {{ row.role === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" width="170">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="180">
            <template #default="{ row }">
              <el-button
                size="small"
                :type="row.role === 'admin' ? 'warning' : 'primary'"
                @click="toggleRole(row)"
              >
                {{ row.role === 'admin' ? '降级为普通用户' : '设为管理员' }}
              </el-button>
              <el-button
                size="small"
                :type="row.is_active ? 'danger' : 'success'"
                @click="toggleActive(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="userTotal > userPageSize"
          :current-page="userPage"
          :page-size="userPageSize"
          :total="userTotal"
          layout="total, prev, pager, next"
          style="margin-top: 16px; justify-content: center"
          @current-change="loadUsers"
        />
      </el-tab-pane>

      <!-- Tab 2: 登录日志 -->
      <el-tab-pane label="登录日志" name="login-logs">
        <el-table :data="loginLogs" v-loading="loginLogsLoading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="用户名" width="140">
            <template #default="{ row }">
              {{ row.username || '未知' }}
            </template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP 地址" width="150" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="170">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="loginLogsTotal > loginLogsPageSize"
          :current-page="loginLogsPage"
          :page-size="loginLogsPageSize"
          :total="loginLogsTotal"
          layout="total, prev, pager, next"
          style="margin-top: 16px; justify-content: center"
          @current-change="loadLoginLogs"
        />
      </el-tab-pane>

      <!-- Tab 3: 操作日志 -->
      <el-tab-pane label="操作日志" name="operation-logs">
        <el-table :data="operationLogs" v-loading="operationLogsLoading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="用户名" width="140">
            <template #default="{ row }">
              {{ row.username || '未知' }}
            </template>
          </el-table-column>
          <el-table-column prop="action" label="操作" width="160" />
          <el-table-column prop="resource_type" label="资源类型" width="120" />
          <el-table-column prop="created_at" label="时间" width="170">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="operationLogsTotal > operationLogsPageSize"
          :current-page="operationLogsPage"
          :page-size="operationLogsPageSize"
          :total="operationLogsTotal"
          layout="total, prev, pager, next"
          style="margin-top: 16px; justify-content: center"
          @current-change="loadOperationLogs"
        />
      </el-tab-pane>

      <!-- Tab 4: 系统状态 -->
      <el-tab-pane label="系统状态" name="system-status">
        <el-row :gutter="16" v-loading="systemStatusLoading">
          <el-col :xs="12" :sm="8" v-for="item in statusCards" :key="item.label">
            <el-card shadow="hover" class="status-card">
              <div class="status-icon" :style="{ background: item.color }">
                <el-icon :size="24"><component :is="item.icon" /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-label">{{ item.label }}</div>
                <div class="status-value">{{ item.value }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Tab 5: 邮箱配置 -->
      <el-tab-pane label="邮箱配置" name="email-config">
        <div class="email-config-header">
          <el-button type="primary" @click="showEmailDialog">
            新增邮箱配置
          </el-button>
          <el-button @click="activeEmailSubTab = 'sync-logs'">
            查看同步日志
          </el-button>
        </div>

        <el-table :data="emailConfigs" v-loading="emailLoading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="imap_server" label="IMAP 服务器" width="200" />
          <el-table-column prop="email_address" label="邮箱地址" width="200" />
          <el-table-column prop="is_enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_enabled ? 'success' : 'info'">
                {{ row.is_enabled ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_sync_at" label="最近同步" width="170">
            <template #default="{ row }">
              {{ row.last_sync_at ? formatDate(row.last_sync_at) : '未同步' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="200">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="editEmailConfig(row)">
                编辑
              </el-button>
              <el-button size="small" type="success" @click="syncEmail(row)">
                同步
              </el-button>
              <el-button size="small" type="danger" @click="deleteEmail(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 同步日志子 Tab -->
        <el-tabs v-model="activeEmailSubTab" style="margin-top: 20px">
          <el-tab-pane label="同步日志" name="sync-logs">
            <el-table :data="emailSyncLogs" v-loading="emailSyncLoading" stripe>
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="email_address" label="邮箱" width="200" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                    {{ row.status === 'success' ? '成功' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="message" label="消息" min-width="200" />
              <el-table-column prop="created_at" label="时间" width="170">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>

            <el-pagination
              v-if="emailSyncTotal > emailSyncPageSize"
              :current-page="emailSyncPage"
              :page-size="emailSyncPageSize"
              :total="emailSyncTotal"
              layout="total, prev, pager, next"
              style="margin-top: 16px; justify-content: center"
              @current-change="loadEmailSyncLogs"
            />
          </el-tab-pane>
        </el-tabs>

        <!-- 新增/编辑对话框 -->
        <el-dialog
          v-model="emailDialogVisible"
          :title="emailDialogTitle"
          width="500px"
        >
          <el-form ref="emailFormRef" :model="emailForm" label-width="100px">
            <el-form-item label="IMAP 服务器" prop="imap_server">
              <el-input v-model="emailForm.imap_server" placeholder="例如：imap.example.com" />
            </el-form-item>
            <el-form-item label="邮箱地址" prop="email_address">
              <el-input v-model="emailForm.email_address" placeholder="user@example.com" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="emailForm.password" type="password" show-password />
            </el-form-item>
            <el-form-item label="启用">
              <el-switch v-model="emailForm.is_enabled" />
            </el-form-item>
          </el-form>

          <template #footer>
            <el-button @click="emailDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="emailSaving" @click="saveEmailConfig">
              保存
            </el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listUsers,
  updateUser,
  listLoginLogs,
  listOperationLogs,
  getSystemStatus,
  listEmailConfigs,
  createEmailConfig,
  deleteEmailConfig,
  syncEmailConfig,
  listEmailSyncLogs,
} from '../api'
import authStore from '../stores/auth'

const router = useRouter()
const activeTab = ref('users')
const activeEmailSubTab = ref('sync-logs')

// 管理员权限检查
onMounted(() => {
  if (!authStore.isAdmin) {
    ElMessage.error('权限不足，需要管理员权限')
    router.push('/')
  }
  loadUsers()
  loadLoginLogs()
  loadOperationLogs()
  loadSystemStatus()
  loadEmailConfigs()
  loadEmailSyncLogs()
})

// ── 日期格式化 ──────────────────────────────────────

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// ── 用户管理 ────────────────────────────────────────

const users = ref([])
const usersLoading = ref(false)
const userPage = ref(1)
const userPageSize = 20
const userTotal = ref(0)

async function loadUsers(page = 1) {
  userPage.value = page
  usersLoading.value = true
  try {
    const skip = (page - 1) * userPageSize
    const { data } = await listUsers(skip, userPageSize)
    // 支持 { items, total } 或数组直接返回
    users.value = data.items || data
    userTotal.value = data.total || users.value.length
  } catch (e) {
    ElMessage.error('加载用户列表失败：' + (e.response?.data?.detail || e.message))
  } finally {
    usersLoading.value = false
  }
}

async function toggleRole(user) {
  const newRole = user.role === 'admin' ? 'user' : 'admin'
  const action = newRole === 'admin' ? '设为管理员' : '降级为普通用户'
  try {
    await ElMessageBox.confirm(
      `确定要将 ${user.username} ${action}吗？`,
      '确认操作',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await updateUser(user.id, { role: newRole })
    ElMessage.success('操作成功')
    loadUsers(userPage.value)
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败：' + (e.response?.data?.detail || e.message))
    }
  }
}

async function toggleActive(user) {
  const newActive = !user.is_active
  const action = newActive ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.username} 吗？`,
      '确认操作',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await updateUser(user.id, { is_active: newActive })
    ElMessage.success('操作成功')
    loadUsers(userPage.value)
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败：' + (e.response?.data?.detail || e.message))
    }
  }
}

// ── 登录日志 ────────────────────────────────────────

const loginLogs = ref([])
const loginLogsLoading = ref(false)
const loginLogsPage = ref(1)
const loginLogsPageSize = 20
const loginLogsTotal = ref(0)

async function loadLoginLogs(page = 1) {
  loginLogsPage.value = page
  loginLogsLoading.value = true
  try {
    const skip = (page - 1) * loginLogsPageSize
    const { data } = await listLoginLogs(skip, loginLogsPageSize)
    loginLogs.value = data.items || data
    loginLogsTotal.value = data.total || loginLogs.value.length
  } catch (e) {
    ElMessage.error('加载登录日志失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loginLogsLoading.value = false
  }
}

// ── 操作日志 ────────────────────────────────────────

const operationLogs = ref([])
const operationLogsLoading = ref(false)
const operationLogsPage = ref(1)
const operationLogsPageSize = 20
const operationLogsTotal = ref(0)

async function loadOperationLogs(page = 1) {
  operationLogsPage.value = page
  operationLogsLoading.value = true
  try {
    const skip = (page - 1) * operationLogsPageSize
    const { data } = await listOperationLogs(skip, operationLogsPageSize)
    operationLogs.value = data.items || data
    operationLogsTotal.value = data.total || operationLogs.value.length
  } catch (e) {
    ElMessage.error('加载操作日志失败：' + (e.response?.data?.detail || e.message))
  } finally {
    operationLogsLoading.value = false
  }
}

// ── 系统状态 ────────────────────────────────────────

const systemStatusData = ref(null)
const systemStatusLoading = ref(false)

const statusCards = computed(() => {
  if (!systemStatusData.value) return []
  const s = systemStatusData.value
  return [
    { label: '数据库状态', value: s.db_status === 'healthy' ? '正常' : '异常', icon: 'Cpu', color: s.db_status === 'healthy' ? '#67c23a' : '#f56c6c' },
    { label: '用户总数', value: s.user_count ?? '-', icon: 'User', color: '#409eff' },
    { label: '简历总数', value: s.resume_count ?? '-', icon: 'Document', color: '#e6a23c' },
    { label: '扫描状态', value: s.scan_status ?? '-', icon: 'Loading', color: s.scan_status === 'idle' ? '#909399' : '#409eff' },
    { label: '系统运行时长', value: s.uptime ?? '-', icon: 'Timer', color: '#67c23a' },
  ]
})

async function loadSystemStatus() {
  systemStatusLoading.value = true
  try {
    const { data } = await getSystemStatus()
    systemStatusData.value = data
  } catch (e) {
    ElMessage.error('加载系统状态失败：' + (e.response?.data?.detail || e.message))
  } finally {
    systemStatusLoading.value = false
  }
}

// ── 邮箱配置 ────────────────────────────────────────

const emailConfigs = ref([])
const emailLoading = ref(false)
const emailDialogVisible = ref(false)
const emailSaving = ref(false)
const emailDialogTitle = computed(() => editingEmailId.value ? '编辑邮箱配置' : '新增邮箱配置')
const editingEmailId = ref(null)
const emailFormRef = ref(null)

const emailForm = reactive({
  imap_server: '',
  email_address: '',
  password: '',
  is_enabled: true,
})

async function loadEmailConfigs() {
  emailLoading.value = true
  try {
    const { data } = await listEmailConfigs()
    emailConfigs.value = data.items || data
  } catch (e) {
    ElMessage.error('加载邮箱配置失败：' + (e.response?.data?.detail || e.message))
  } finally {
    emailLoading.value = false
  }
}

function showEmailDialog() {
  editingEmailId.value = null
  emailForm.imap_server = ''
  emailForm.email_address = ''
  emailForm.password = ''
  emailForm.is_enabled = true
  emailDialogVisible.value = true
}

function editEmailConfig(config) {
  editingEmailId.value = config.id
  emailForm.imap_server = config.imap_server
  emailForm.email_address = config.email_address
  emailForm.password = ''
  emailForm.is_enabled = config.is_enabled
  emailDialogVisible.value = true
}

async function saveEmailConfig() {
  emailSaving.value = true
  try {
    if (editingEmailId.value) {
      // 编辑模式需要 update API，此处使用 patch（需后端支持）
      // 当前 API 仅提供了 create/delete，编辑通过先删后建或扩展后端实现
      ElMessage.warning('编辑功能需要后端支持 update 接口')
    } else {
      await createEmailConfig({
        imap_server: emailForm.imap_server,
        email_address: emailForm.email_address,
        password: emailForm.password,
        is_enabled: emailForm.is_enabled,
      })
      ElMessage.success('创建成功')
    }
    emailDialogVisible.value = false
    loadEmailConfigs()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  } finally {
    emailSaving.value = false
  }
}

async function deleteEmail(config) {
  try {
    await ElMessageBox.confirm(
      `确定要删除邮箱配置 ${config.email_address} 吗？`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteEmailConfig(config.id)
    ElMessage.success('删除成功')
    loadEmailConfigs()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message))
    }
  }
}

async function syncEmail(config) {
  try {
    await syncEmailConfig(config.id)
    ElMessage.success('同步已启动')
    loadEmailConfigs()
    loadEmailSyncLogs()
  } catch (e) {
    ElMessage.error('同步失败：' + (e.response?.data?.detail || e.message))
  }
}

// ── 同步日志 ────────────────────────────────────────

const emailSyncLogs = ref([])
const emailSyncLoading = ref(false)
const emailSyncPage = ref(1)
const emailSyncPageSize = 20
const emailSyncTotal = ref(0)

async function loadEmailSyncLogs(page = 1) {
  emailSyncPage.value = page
  emailSyncLoading.value = true
  try {
    const skip = (page - 1) * emailSyncPageSize
    const { data } = await listEmailSyncLogs(skip, emailSyncPageSize)
    emailSyncLogs.value = data.items || data
    emailSyncTotal.value = data.total || emailSyncLogs.value.length
  } catch (e) {
    ElMessage.error('加载同步日志失败：' + (e.response?.data?.detail || e.message))
  } finally {
    emailSyncLoading.value = false
  }
}
</script>

<style scoped>
.admin-view {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.admin-title {
  margin: 0 0 20px;
  font-size: 20px;
  color: #1a1a2e;
}

.email-config-header {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.status-card {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  padding: 8px;
}

.status-card .el-card__body {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.status-info {
  flex: 1;
}

.status-label {
  font-size: 13px;
  color: #909399;
}

.status-value {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin-top: 4px;
}
</style>
