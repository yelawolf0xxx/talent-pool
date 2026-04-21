<template>
  <div class="email-config-view">
    <div class="view-header">
      <h2 class="view-title">邮箱管理</h2>
      <el-button text type="primary" @click="$router.push('/email-tutorial')">
        配置帮助
      </el-button>
    </div>

    <el-tabs v-model="activeTab" type="card">
      <!-- Tab 1: 邮箱配置 -->
      <el-tab-pane label="邮箱配置" name="configs">
        <div class="config-header">
          <el-button type="primary" @click="showEmailDialog">
            新增邮箱配置
          </el-button>
          <el-button @click="loadEmailConfigs">
            刷新
          </el-button>
        </div>

        <el-table :data="emailConfigs" v-loading="emailLoading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="imap_server" label="IMAP 服务器" width="200" />
          <el-table-column prop="email_address" label="邮箱地址" width="220" />
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
          <el-table-column label="操作" min-width="220">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="editEmailConfig(row)">
                编辑
              </el-button>
              <el-button size="small" type="success" @click="syncEmail(row)" :loading="row.syncing">
                同步
              </el-button>
              <el-button size="small" type="danger" @click="deleteEmail(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!emailLoading && emailConfigs.length === 0" description="暂无邮箱配置，请点击上方按钮添加" />

        <!-- 新增/编辑对话框 -->
        <el-dialog
          v-model="emailDialogVisible"
          :title="emailDialogTitle"
          width="500px"
        >
          <el-form :model="emailForm" label-width="100px">
            <el-form-item label="IMAP 服务器">
              <el-input v-model="emailForm.imap_server" placeholder="例如：imap.example.com" />
            </el-form-item>
            <el-form-item label="IMAP 端口">
              <el-input-number v-model="emailForm.imap_port" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="邮箱地址">
              <el-input v-model="emailForm.email_address" placeholder="user@example.com" @input="onEmailAddressChange" />
            </el-form-item>
            <el-form-item label="密码/授权码">
              <el-input v-model="emailForm.password" type="password" show-password placeholder="请输入邮箱密码或授权码" />
            </el-form-item>
            <el-form-item label="下载目录">
              <el-input v-model="emailForm.download_dir" placeholder="默认: \\\\192.168.3.30\\简历资料夹" />
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

      <!-- Tab 2: 同步日志 -->
      <el-tab-pane label="同步日志" name="sync-logs">
        <el-table :data="emailSyncLogs" v-loading="emailSyncLoading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="total_emails" label="扫描邮件" width="100" />
          <el-table-column prop="new_attachments" label="新附件" width="100" />
          <el-table-column prop="downloaded" label="已下载" width="100" />
          <el-table-column prop="failed" label="失败" width="80" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
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

      <!-- Tab 3: 全部邮件（仅管理员） -->
      <el-tab-pane v-if="authStore.isAdmin" label="全部邮件" name="all-emails">
        <div class="email-list-header">
          <el-select
            v-model="selectedEmailConfigId"
            placeholder="选择邮箱配置"
            style="width: 280px"
            @change="onEmailConfigChange"
          >
            <el-option
              v-for="cfg in emailConfigs"
              :key="cfg.id"
              :label="cfg.email_address"
              :value="cfg.id"
            />
          </el-select>
          <el-input
            v-model="emailSearch"
            placeholder="搜索主题或发件人"
            clearable
            style="width: 240px"
            @keyup.enter="loadAdminEmails"
          />
          <el-button type="primary" :disabled="!selectedEmailConfigId" @click="loadAdminEmails">
            刷新
          </el-button>
        </div>

        <el-table
          :data="adminEmails"
          v-loading="emailListLoading"
          stripe
          @row-click="openEmailDetail"
          style="cursor: pointer"
        >
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <span v-if="!row.is_read" class="unread-dot unread" title="未读"></span>
              <span v-else class="unread-dot read" title="已读"></span>
            </template>
          </el-table-column>
          <el-table-column prop="from" label="发件人" width="220" show-overflow-tooltip />
          <el-table-column prop="subject" label="主题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="date" label="日期" width="180">
            <template #default="{ row }">
              {{ formatDate(row.date) }}
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!emailListLoading && adminEmails.length === 0" :description="selectedEmailConfigId ? '暂无邮件' : '请先选择邮箱配置'" />

        <el-pagination
          v-if="adminEmailTotal > emailListPageSize"
          :current-page="emailListPage"
          :page-size="emailListPageSize"
          :total="adminEmailTotal"
          layout="total, prev, pager, next"
          style="margin-top: 16px; justify-content: center"
          @current-change="loadAdminEmails"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 邮件详情弹窗 -->
    <el-dialog
      v-model="emailDetailVisible"
      :title="emailDetail?.subject || '邮件详情'"
      width="700px"
    >
      <div v-if="emailDetail" class="email-detail">
        <div class="email-detail-header">
          <div class="email-meta">
            <span class="meta-label">发件人：</span>
            <span class="meta-value">{{ emailDetail.from }}</span>
          </div>
          <div class="email-meta">
            <span class="meta-label">日期：</span>
            <span class="meta-value">{{ formatDate(emailDetail.date) }}</span>
          </div>
          <div class="email-meta">
            <span class="meta-label">状态：</span>
            <el-tag :type="emailDetail.is_read ? 'info' : 'danger'" size="small">
              {{ emailDetail.is_read ? '已读' : '未读' }}
            </el-tag>
          </div>
        </div>

        <!-- 附件列表 -->
        <div v-if="emailDetail.attachments && emailDetail.attachments.length > 0" class="email-attachments">
          <h4 class="attachment-title">附件（{{ emailDetail.attachments.length }}）</h4>
          <el-table :data="emailDetail.attachments" size="small" border>
            <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column label="大小" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.size) }}
              </template>
            </el-table-column>
            <el-table-column prop="content_type" label="类型" width="150" />
          </el-table>
        </div>

        <!-- 正文预览 -->
        <div class="email-body">
          <h4 class="body-title">正文预览</h4>
          <pre class="body-content">{{ emailDetail.body_text }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="emailDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listMyEmailConfigs,
  createMyEmailConfig,
  deleteMyEmailConfig,
  syncMyEmailConfig,
  listMyEmailSyncLogs,
  listAdminEmails,
  getAdminEmailDetail,
} from '../api'
import authStore from '../stores/auth'

const activeTab = ref('configs')

onMounted(() => {
  loadEmailConfigs()
  loadEmailSyncLogs()
})

// ── 日期格式化 ──────────────────────────────────────

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// ── 邮箱配置 ────────────────────────────────────────

const emailConfigs = ref([])
const emailLoading = ref(false)
const emailDialogVisible = ref(false)
const emailSaving = ref(false)
const emailDialogTitle = computed(() => editingEmailId.value ? '编辑邮箱配置' : '新增邮箱配置')
const editingEmailId = ref(null)

const emailForm = reactive({
  imap_server: '',
  imap_port: 993,
  email_address: '',
  password: '',
  download_dir: '',
})

async function loadEmailConfigs() {
  emailLoading.value = true
  try {
    const { data } = await listMyEmailConfigs()
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
  emailForm.imap_port = 993
  emailForm.email_address = ''
  emailForm.password = ''
  emailForm.download_dir = ''
  emailDialogVisible.value = true
}

/**
 * 根据邮箱地址提取用户名部分（@ 之前的内容）
 */
function extractUsername(emailAddress) {
  if (!emailAddress || !emailAddress.includes('@')) return ''
  return emailAddress.split('@')[0]
}

/**
 * 邮箱地址变化时自动填充默认下载目录
 */
function onEmailAddressChange() {
  if (!editingEmailId.value) {
    const username = extractUsername(emailForm.email_address)
    if (username) {
      emailForm.download_dir = `\\\\192.168.3.30\\${username}`
    } else {
      emailForm.download_dir = ''
    }
  }
}

function editEmailConfig(config) {
  editingEmailId.value = config.id
  emailForm.imap_server = config.imap_server
  emailForm.imap_port = config.imap_port || 993
  emailForm.email_address = config.email_address
  emailForm.password = ''
  emailForm.download_dir = config.download_dir || ''
  emailDialogVisible.value = true
}

async function saveEmailConfig() {
  if (!emailForm.imap_server || !emailForm.email_address || !emailForm.password) {
    ElMessage.warning('请填写 IMAP 服务器、邮箱地址和密码')
    return
  }

  emailSaving.value = true
  try {
    await createMyEmailConfig({
      imap_server: emailForm.imap_server,
      imap_port: emailForm.imap_port,
      email_address: emailForm.email_address,
      password: emailForm.password,
      download_dir: emailForm.download_dir || undefined,
    })
    ElMessage.success(editingEmailId.value ? '更新成功' : '创建成功')
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
    await deleteMyEmailConfig(config.id)
    ElMessage.success('删除成功')
    loadEmailConfigs()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message))
    }
  }
}

async function syncEmail(config) {
  config.syncing = true
  try {
    await syncMyEmailConfig(config.id)
    ElMessage.success('同步已启动')
    loadEmailConfigs()
    loadEmailSyncLogs()
  } catch (e) {
    ElMessage.error('同步失败：' + (e.response?.data?.detail || e.message))
  } finally {
    config.syncing = false
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
    const { data } = await listMyEmailSyncLogs(skip, emailSyncPageSize)
    emailSyncLogs.value = data.items || data
    emailSyncTotal.value = data.total || emailSyncLogs.value.length
  } catch (e) {
    ElMessage.error('加载同步日志失败：' + (e.response?.data?.detail || e.message))
  } finally {
    emailSyncLoading.value = false
  }
}

function getStatusType(status) {
  const map = { success: 'success', failed: 'danger', partial: 'warning' }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = { success: '成功', failed: '失败', partial: '部分成功' }
  return map[status] || status
}

// ── 全部邮件（仅管理员）────────────────────────────────

const selectedEmailConfigId = ref(null)
const emailSearch = ref('')
const adminEmails = ref([])
const emailListLoading = ref(false)
const emailListPage = ref(1)
const emailListPageSize = 20
const adminEmailTotal = ref(0)
const emailDetailVisible = ref(false)
const emailDetail = ref(null)
const emailDetailLoading = ref(false)

function onEmailConfigChange() {
  emailListPage.value = 1
  emailSearch.value = ''
  loadAdminEmails()
}

async function loadAdminEmails(page = 1) {
  if (!selectedEmailConfigId.value) return

  emailListPage.value = page
  emailListLoading.value = true
  try {
    const { data } = await listAdminEmails(
      selectedEmailConfigId.value,
      page,
      emailListPageSize,
      emailSearch.value,
    )
    adminEmails.value = data.items || []
    adminEmailTotal.value = data.total || 0
  } catch (e) {
    ElMessage.error('加载邮件列表失败：' + (e.response?.data?.detail || e.message))
    adminEmails.value = []
  } finally {
    emailListLoading.value = false
  }
}

async function openEmailDetail(row) {
  emailDetailLoading.value = true
  emailDetailVisible.value = true
  emailDetail.value = null
  try {
    const { data } = await getAdminEmailDetail(
      selectedEmailConfigId.value,
      row.uid,
    )
    emailDetail.value = data
  } catch (e) {
    ElMessage.error('加载邮件详情失败：' + (e.response?.data?.detail || e.message))
  } finally {
    emailDetailLoading.value = false
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.email-config-view {
  background: var(--bg-surface);
  border-radius: var(--border-radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
}

.view-title {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.config-header {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.email-list-header {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
}

.unread-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.unread-dot.unread {
  background: var(--color-primary, #409eff);
}

.unread-dot.read {
  background: #c0c4cc;
}

.email-detail-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.email-meta {
  font-size: var(--font-size-sm);
}

.meta-label {
  color: var(--text-muted);
  margin-right: 4px;
}

.meta-value {
  color: var(--text-primary);
}

.email-attachments {
  margin-bottom: 16px;
}

.attachment-title,
.body-title {
  margin: 0 0 8px;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: 600;
}

.email-body {
  margin-top: 16px;
}

.body-content {
  background: var(--bg-surface-hover, #f5f7fa);
  border: 1px solid var(--border-color, #ebeef5);
  border-radius: 4px;
  padding: 12px 16px;
  font-size: var(--font-size-sm);
  line-height: 1.6;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text-primary);
  margin: 0;
}
</style>
