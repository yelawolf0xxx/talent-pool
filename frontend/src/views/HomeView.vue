<template>
  <div class="home-view">
    <div class="search-hero">
      <h1>AI 简历人才库</h1>
      <p class="subtitle">智能搜索，精准匹配候选人</p>

      <div class="hero-actions">
        <input
          ref="uploadRef"
          type="file"
          accept=".pdf,.doc,.docx,.ppt,.pptx"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />
        <el-button type="primary" @click="uploadRef?.click()">
          <el-icon><Upload /></el-icon> 上传简历
        </el-button>
        <el-button @click="$router.push('/manual')">
          <el-icon><Document /></el-icon> 用户手册
        </el-button>
      </div>

      <el-card class="search-card">
        <el-form :model="form" @submit.prevent="handleSearch">
          <el-row :gutter="16">
            <el-col :span="14">
              <el-input
                v-model="form.query"
                placeholder="输入关键词搜索，如：Python 后端开发 5年"
                size="large"
                clearable
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="6">
              <el-input-number
                v-model="form.minYearsExp"
                :min="0"
                :max="30"
                placeholder="最低年限"
                size="large"
                controls-position="right"
                style="width: 100%"
              />
            </el-col>
            <el-col :span="4">
              <el-button type="primary" size="large" @click="handleSearch" style="width: 100%">
                搜索
              </el-button>
            </el-col>
          </el-row>
          <el-row style="margin-top: 12px">
            <el-col :span="24">
              <el-select
                v-model="form.skills"
                multiple
                filterable
                allow-create
                placeholder="按技能筛选，如 Java, Vue, AWS"
                size="default"
                style="width: 100%"
              />
            </el-col>
          </el-row>
        </el-form>
      </el-card>
    </div>

    <div v-if="loading" class="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else>
      <!-- 简历来源 Tab -->
      <el-tabs v-model="activeTab" type="card">
        <el-tab-pane label="全部简历" name="all">
          <div class="tab-hint">显示系统中所有简历</div>
        </el-tab-pane>
        <el-tab-pane label="我的简历" name="mine">
          <div class="tab-hint">显示从您配置的邮箱中同步的简历</div>
        </el-tab-pane>
      </el-tabs>

      <!-- 批量操作栏 -->
      <div v-if="selectedIds.length > 0" class="batch-actions">
        <el-tag type="info" size="large">已选 {{ selectedIds.length }} 份简历</el-tag>
        <el-button type="danger" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon> 批量删除
        </el-button>
        <el-button text @click="clearSelection">取消选择</el-button>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searched" class="search-results">
        <div class="results-header">
          <h2>搜索结果</h2>
          <span class="result-count">共 {{ displayResumes.length }} 条</span>
          <el-button text type="primary" @click="clearSearch">
            <el-icon><Refresh /></el-icon> 查看全部简历
          </el-button>
        </div>
        <el-empty v-if="displayResumes.length === 0" description="未找到匹配的候选人，请调整搜索条件" />
        <div v-else class="resume-waterfall">
          <el-checkbox-group v-model="selectedIds" class="waterfall-container">
            <div
              v-for="item in displayResumes"
              :key="item.id"
              class="waterfall-item"
            >
              <el-card
                class="resume-card"
                shadow="hover"
                :class="{ selected: selectedIds.includes(item.id) }"
              >
                <div class="card-checkbox">
                  <el-checkbox :value="item.id" @click.stop />
                </div>
                <div
                  class="card-content"
                  @click="$router.push(`/resume/${item.id}`)"
                >
                <div class="card-header">
                  <el-avatar :size="48" style="background: var(--color-primary); color: var(--text-on-primary)">
                    {{ item.name?.charAt(0) || '?' }}
                  </el-avatar>
                  <div class="card-info">
                    <h3>{{ item.name || '未命名' }}</h3>
                    <p class="title">{{ item.current_title || '职位未知' }}</p>
                  </div>
                </div>
                <div class="card-body">
                  <el-tag v-if="item.years_exp" size="small" class="skill-tag">
                    {{ item.years_exp }}年经验
                  </el-tag>
                  <el-tag
                    v-for="skill in (item.skills || []).slice(0, 4)"
                    :key="skill"
                    size="small"
                    class="skill-tag"
                  >
                    {{ skill }}
                  </el-tag>
                </div>
                <div v-if="item.score" class="match-score">
                  <el-progress
                    :percentage="Math.round(item.score * 100)"
                    :color="item.score > 0.6 ? 'var(--color-success)' : 'var(--color-warning)'"
                    :show-text="false"
                    :stroke-width="4"
                  />
                  <span>匹配度 {{ Math.round(item.score * 100) }}%</span>
                </div>
                </div>
              </el-card>
            </div>
          </el-checkbox-group>
        </div>
      </div>

      <!-- 全部简历画廊 -->
      <div v-else class="resume-gallery">
        <div class="gallery-header">
          <h2>{{ activeTab === 'mine' ? '我的简历' : '全部简历' }}</h2>
          <span class="result-count">共 {{ allResumes.length }} 条</span>
        </div>
        <el-empty v-if="allResumes.length === 0" :description="activeTab === 'mine' ? '暂无简历，请在上方邮箱管理中配置邮箱并同步' : '暂无简历，请将 PDF 简历放入简历目录'" />
        <div v-else ref="waterfallContainer" class="resume-waterfall">
          <el-checkbox-group v-model="selectedIds" class="waterfall-container checkbox-grid">
            <div
              v-for="item in allResumes"
              :key="item.id"
              class="waterfall-item"
            >
              <el-card
                class="resume-card"
                shadow="hover"
                :class="{ selected: selectedIds.includes(item.id) }"
              >
                <div class="card-checkbox">
                  <el-checkbox :value="item.id" @click.stop />
                </div>
                <div
                  class="card-content"
                  @click="$router.push(`/resume/${item.id}`)"
                >
                <div class="card-header">
                  <el-avatar :size="48" style="background: var(--color-primary); color: var(--text-on-primary)">
                    {{ item.name?.charAt(0) || '?' }}
                  </el-avatar>
                  <div class="card-info">
                    <h3>{{ item.name || '未命名' }}</h3>
                    <p class="title">{{ item.current_title || '职位未知' }}</p>
                  </div>
                </div>
                <div class="card-body">
                  <el-tag v-if="item.years_exp" size="small" class="skill-tag">
                    {{ item.years_exp }}年经验
                  </el-tag>
                  <el-tag
                    v-for="skill in (item.skills || []).slice(0, 4)"
                    :key="skill"
                    size="small"
                    class="skill-tag"
                  >
                    {{ skill }}
                  </el-tag>
                </div>
                <div v-if="item.summary_text" class="card-summary">
                  {{ item.summary_text }}
                </div>
                </div>
              </el-card>
            </div>
            <!-- 无限滚动哨兵 -->
            <div ref="loadMoreTrigger" style="grid-column: 1 / -1; padding: 36px 0;">
              <div v-if="loadingMore" class="infinite-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载中...</span>
              </div>
              <p v-else-if="!hasMore && allResumes.length > PAGE_SIZE" class="no-more">已全部加载</p>
            </div>
          </el-checkbox-group>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { searchResumes, listResumes, deleteBatch, uploadResume } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const PAGE_SIZE = 20

const activeTab = ref('all')

const form = reactive({
  query: '',
  skills: [],
  minYearsExp: null,
})

const allResumes = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const searched = ref(false)
const hasMore = ref(true)
const selectedIds = ref([])
const uploadRef = ref(null)

// 支持的文件类型
const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.ppt', '.pptx']

// 搜索结果（带分数和匹配原因）
const searchResults = ref([])

// 当前是否为"我的简历"模式
const isMine = computed(() => activeTab.value === 'mine')

// 当前展示的简历列表
const displayResumes = computed(() => {
  if (!searched.value || searchResults.value.length === 0) return []
  return searchResults.value.map(item => ({
    id: item.resume.id,
    name: item.resume.name,
    email: item.resume.email,
    phone: item.resume.phone,
    current_title: item.resume.current_title,
    years_exp: item.resume.years_exp,
    skills: item.resume.skills,
    summary_text: item.resume.summary_text,
    score: item.score,
    match_reasons: item.match_reasons,
  }))
})

/**
 * 加载第一页简历
 */
async function loadFirstPage() {
  loading.value = true
  try {
    const res = await listResumes(0, PAGE_SIZE, isMine.value)
    const resumes = Array.isArray(res.data) ? res.data : (res.data?.items || [])
    allResumes.value = resumes
    hasMore.value = resumes.length >= PAGE_SIZE
  } catch (e) {
    allResumes.value = []
    hasMore.value = false
    if (e.response?.status !== 401) {
      ElMessage.error('加载简历失败：' + (e.response?.data?.detail || e.message))
    }
  } finally {
    loading.value = false
    nextTick(() => setupScrollObserver())
  }
}

/**
 * 加载更多简历
 */
async function loadMore() {
  if (loadingMore.value || !hasMore.value || loading.value) return
  loadingMore.value = true
  try {
    const skip = allResumes.value.length
    const res = await listResumes(skip, PAGE_SIZE, isMine.value)
    const resumes = Array.isArray(res.data) ? res.data : (res.data?.items || [])
    if (resumes.length > 0) {
      allResumes.value = [...allResumes.value, ...resumes]
    }
    hasMore.value = resumes.length >= PAGE_SIZE
  } catch (e) {
    ElMessage.error('加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loadingMore.value = false
  }
}

/**
 * 用容器底部元素触发的简单无限滚动
 */
let scrollObserver = null
const loadMoreTrigger = ref(null)

function setupScrollObserver() {
  if (scrollObserver) scrollObserver.disconnect()
  scrollObserver = new IntersectionObserver(
    entries => {
      if (entries[0].isIntersecting && hasMore.value && !loadingMore.value && !loading.value) {
        loadMore()
      }
    },
    { rootMargin: '400px' }
  )
  nextTick(() => {
    if (loadMoreTrigger.value) {
      scrollObserver.observe(loadMoreTrigger.value)
    }
  })
}

// Tab 切换时重新加载数据
watch(activeTab, () => {
  searched.value = false
  searchResults.value = []
  selectedIds.value = []
  loadingMore.value = false
  hasMore.value = true
  loading.value = true
  allResumes.value = []
  loadFirstPage()
})

onMounted(() => {
  loadFirstPage()
})

async function handleSearch() {
  if (!form.query.trim() && form.skills.length === 0 && form.minYearsExp === null) {
    ElMessage.warning('请输入搜索关键词或选择筛选条件')
    return
  }

  loading.value = true
  searched.value = true
  try {
    const { data } = await searchResumes(form.query, form.skills, form.minYearsExp, isMine.value)
    searchResults.value = data.results || []
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到匹配的候选人，请调整搜索条件')
    }
  } catch (e) {
    ElMessage.error('搜索失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

function clearSearch() {
  form.query = ''
  form.skills = []
  form.minYearsExp = null
  searched.value = false
  searchResults.value = []
}

/**
 * Tab 切换时重新加载数据
 */
watch(activeTab, () => {
  searched.value = false
  searchResults.value = []
  selectedIds.value = []
  loadingMore.value = false
  hasMore.value = true
  loading.value = true
  allResumes.value = []
  loadFirstPage()
})

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定要将 ${selectedIds.value.length} 份简历移入回收站吗？删除后可在回收站中恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const { data } = await deleteBatch(selectedIds.value)
    ElMessage.success(`已删除 ${data.deleted} 份简历`)
    clearSelection()
    loadFirstPage()
    if (searched.value) {
      searched.value = false
      searchResults.value = []
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message))
    }
  }
}

function clearSelection() {
  selectedIds.value = []
}

/**
 * 处理文件选择与上传（支持多文件）
 */
async function handleFileSelect(event) {
  const files = Array.from(event.target.files || [])
  if (files.length === 0) return

  // 过滤有效文件
  const validFiles = []
  const invalidFiles = []
  for (const file of files) {
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      invalidFiles.push(file.name)
    } else {
      validFiles.push(file)
    }
  }

  if (invalidFiles.length > 0) {
    ElMessage.warning(`已忽略 ${invalidFiles.length} 个不支持格式的文件`)
  }
  if (validFiles.length === 0) {
    event.target.value = ''
    return
  }

  try {
    loading.value = true
    const { data } = await uploadResume(validFiles)

    // 构建上传结果摘要
    let msg = `成功上传 ${data.uploaded.length} 份简历`
    if (data.failed?.length > 0) {
      msg += `，失败 ${data.failed.length} 份`
    }

    if (data.uploaded.length > 0) {
      // 弹出提示框询问是否立即更新人才库
      try {
        await ElMessageBox.confirm(
          `${msg}。\n\n是否立即点击"更新人才库"进行解析？`,
          '上传完成',
          { confirmButtonText: '立即解析', cancelButtonText: '稍后处理', type: 'success' }
        )
        const { data: scanData } = await import('../api').then(m => m.manualScan())
        if (scanData.status === 'running') {
          ElMessage.info(scanData.message)
        } else {
          ElMessage.success('扫描已启动，请稍后查看结果')
          loadFirstPage()
        }
      } catch {
        // 用户点击"稍后处理"
      }
    } else {
      ElMessage.error(msg + '，请检查文件格式')
    }
  } catch (e) {
    ElMessage.error('上传失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
    event.target.value = ''
  }
}
</script>

<style scoped>
.search-hero {
  text-align: center;
  margin-bottom: 48px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 18px 24px;
  background: var(--batch-bg);
  border-radius: var(--border-radius-md);
  margin-bottom: 24px;
  box-shadow: var(--batch-shadow);
}

.search-hero h1 {
  font-size: var(--font-size-2xl);
  margin: 0 0 12px;
  color: var(--hero-text);
  font-weight: 600;
}

.subtitle {
  color: var(--hero-subtitle);
  margin: 0 0 36px;
  font-size: var(--font-size-lg);
}

.search-card {
  max-width: 800px;
  margin: 0 auto;
}

.results-header,
.gallery-header {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 30px;
  padding: 0 6px;
}

.results-header h2,
.gallery-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--text-primary);
  font-weight: 600;
}

.result-count {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  margin-left: auto;
}

/* ── 瀑布流容器 ──────────────────────────────────────── */
.waterfall-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  align-items: start;
}

/* el-checkbox-group 默认渲染为 div，需重置浏览器默认样式以匹配 grid 行为 */
.el-checkbox-group.waterfall-container {
  margin: 0;
  padding: 0;
  list-style: none;
}

.waterfall-item {
  width: 100%;
}

/* 无限滚动加载 */
.infinite-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.resume-card {
  position: relative;
  cursor: pointer;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast), background-color var(--transition-fast);
}

.resume-card:hover {
  transform: translateY(-2px);
  background-color: var(--bg-surface-hover);
}

.resume-card.selected {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-card-selected);
}

.card-checkbox {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 1;
}

.card-content {
  cursor: pointer;
  padding: 4px 4px 4px 32px;
}

.card-info h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 600;
  line-height: 1.3;
  word-break: break-word;
}

.card-info .title {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.4;
  word-break: break-word;
}

.card-body {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 18px;
}

.skill-tag {
  background: var(--skill-bg) !important;
  color: var(--skill-text) !important;
  border-color: var(--skill-border) !important;
}

.card-summary {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-top: 8px;
}

.match-score {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin-top: 8px;
}

.match-score .el-progress {
  flex: 1;
}

.no-more {
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  margin: 0;
}

.tab-hint {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  margin-bottom: 8px;
}
</style>

<!-- 毛玻璃主题专属覆盖 -->
<style>
[data-theme="glass"] .search-hero h1 {
  font-size: var(--font-size-3xl) !important;
  font-weight: 300 !important;
  letter-spacing: -0.02em;
}

[data-theme="glass"] .subtitle {
  font-weight: 300 !important;
  letter-spacing: 0.01em;
}

[data-theme="glass"] .search-card .el-card {
  background: rgba(255, 255, 255, 0.35) !important;
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
}

[data-theme="glass"] .waterfall-item .el-card {
  background: rgba(255, 255, 255, 0.30) !important;
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
}

[data-theme="glass"] .resume-card:hover {
  transform: translateY(-8px) scale(1.01);
}

[data-theme="glass"] .card-info h3 {
  font-weight: 500 !important;
}

[data-theme="glass"] .batch-actions {
  background: rgba(255, 255, 255, 0.35) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
</style>
