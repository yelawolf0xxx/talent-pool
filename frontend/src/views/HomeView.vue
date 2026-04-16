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
        <div v-else class="resume-grid">
          <el-row :gutter="16">
            <el-col v-for="item in displayResumes" :key="item.id" :xs="24" :sm="12" :md="8">
              <el-card
                class="resume-card"
                shadow="hover"
                :class="{ selected: selectedIds.includes(item.id) }"
              >
                <div class="card-checkbox">
                  <el-checkbox
                    v-model="selectedIds"
                    :label="item.id"
                    @click.stop
                  />
                </div>
                <div
                  class="card-content"
                  @click="$router.push(`/resume/${item.id}`)"
                >
                <div class="card-header">
                  <el-avatar :size="48" style="background: #409eff">
                    {{ item.name?.charAt(0) || '?' }}
                  </el-avatar>
                  <div class="card-info">
                    <h3>{{ item.name || '未命名' }}</h3>
                    <p class="title">{{ item.current_title || '职位未知' }}</p>
                  </div>
                </div>
                <div class="card-body">
                  <el-tag v-if="item.years_exp" size="small">
                    {{ item.years_exp }}年经验
                  </el-tag>
                  <el-tag
                    v-for="skill in (item.skills || []).slice(0, 4)"
                    :key="skill"
                    size="small"
                    type="info"
                    style="margin-left: 4px"
                  >
                    {{ skill }}
                  </el-tag>
                </div>
                <div v-if="item.score" class="match-score">
                  <el-progress
                    :percentage="Math.round(item.score * 100)"
                    :color="item.score > 0.6 ? '#67c23a' : '#e6a23c'"
                    :show-text="false"
                    :stroke-width="4"
                  />
                  <span>匹配度 {{ Math.round(item.score * 100) }}%</span>
                </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 全部简历画廊 -->
      <div v-else class="resume-gallery">
        <div class="gallery-header">
          <h2>全部简历</h2>
          <span class="result-count">共 {{ allResumes.length }} 条</span>
        </div>
        <el-empty v-if="allResumes.length === 0" description="暂无简历，请将 PDF 简历放入简历目录" />
        <div v-else class="resume-grid">
          <el-row :gutter="16">
            <el-col v-for="item in allResumes" :key="item.id" :xs="24" :sm="12" :md="8">
              <el-card
                class="resume-card"
                shadow="hover"
                :class="{ selected: selectedIds.includes(item.id) }"
              >
                <div class="card-checkbox">
                  <el-checkbox
                    v-model="selectedIds"
                    :label="item.id"
                    @click.stop
                  />
                </div>
                <div
                  class="card-content"
                  @click="$router.push(`/resume/${item.id}`)"
                >
                <div class="card-header">
                  <el-avatar :size="48" style="background: #409eff">
                    {{ item.name?.charAt(0) || '?' }}
                  </el-avatar>
                  <div class="card-info">
                    <h3>{{ item.name || '未命名' }}</h3>
                    <p class="title">{{ item.current_title || '职位未知' }}</p>
                  </div>
                </div>
                <div class="card-body">
                  <el-tag v-if="item.years_exp" size="small">
                    {{ item.years_exp }}年经验
                  </el-tag>
                  <el-tag
                    v-for="skill in (item.skills || []).slice(0, 4)"
                    :key="skill"
                    size="small"
                    type="info"
                    style="margin-left: 4px"
                  >
                    {{ skill }}
                  </el-tag>
                </div>
                <div v-if="item.summary_text" class="card-summary">
                  {{ item.summary_text }}
                </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- 加载更多 -->
        <div v-if="hasMore" class="load-more">
          <el-button :loading="loadingMore" @click="loadMore">
            {{ loadingMore ? '加载中...' : '加载更多' }}
          </el-button>
        </div>
        <p v-else-if="allResumes.length > PAGE_SIZE" class="no-more">已全部加载</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { searchResumes, listResumes, deleteBatch, uploadResume } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const PAGE_SIZE = 20

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
    const { data } = await listResumes(0, PAGE_SIZE)
    allResumes.value = data
    hasMore.value = data.length >= PAGE_SIZE
  } catch {
    allResumes.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 加载更多简历
 */
async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  try {
    const skip = allResumes.value.length
    const { data } = await listResumes(skip, PAGE_SIZE)
    allResumes.value = [...allResumes.value, ...data]
    hasMore.value = data.length >= PAGE_SIZE
  } catch (e) {
    ElMessage.error('加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loadingMore.value = false
  }
}

onMounted(loadFirstPage)

async function handleSearch() {
  if (!form.query.trim() && form.skills.length === 0 && form.minYearsExp === null) {
    ElMessage.warning('请输入搜索关键词或选择筛选条件')
    return
  }

  loading.value = true
  searched.value = true
  try {
    const { data } = await searchResumes(form.query, form.skills, form.minYearsExp)
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
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.search-hero h1 {
  font-size: 32px;
  margin: 0 0 8px;
  color: #1a1a2e;
}

.subtitle {
  color: #666;
  margin: 0 0 24px;
}

.search-card {
  max-width: 800px;
  margin: 0 auto;
}

.results-header,
.gallery-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 0 4px;
}

.results-header h2,
.gallery-header h2 {
  margin: 0;
  font-size: 20px;
  color: #1a1a2e;
}

.result-count {
  color: #909399;
  font-size: 14px;
  margin-left: auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.resume-card {
  position: relative;
  cursor: pointer;
  transition: transform 0.15s;
}

.resume-card:hover {
  transform: translateY(-2px);
}

.resume-card.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.card-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 1;
}

.card-content {
  cursor: pointer;
}

.card-info h3 {
  margin: 0;
  font-size: 16px;
}

.card-info .title {
  margin: 4px 0 0;
  color: #666;
  font-size: 13px;
}

.card-body {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}

.card-summary {
  color: #909399;
  font-size: 12px;
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
  font-size: 12px;
  color: #666;
  margin-top: 8px;
}

.match-score .el-progress {
  flex: 1;
}

.load-more {
  text-align: center;
  margin-top: 24px;
}

.no-more {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-top: 16px;
}
</style>
