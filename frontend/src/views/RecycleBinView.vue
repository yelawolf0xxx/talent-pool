<template>
  <div class="recycle-bin-view">
    <div class="page-header">
      <h1>回收站</h1>
      <p class="subtitle">已删除的简历可在 30 天内恢复</p>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-actions">
      <el-tag type="info" size="large">已选 {{ selectedIds.length }} 份简历</el-tag>
      <el-button type="primary" @click="handleBatchRestore">
        <el-icon><RefreshLeft /></el-icon> 批量恢复
      </el-button>
      <el-button text @click="clearSelection">取消选择</el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 回收站内容 -->
    <template v-else>
      <el-empty v-if="items.length === 0" description="回收站为空" />
      <div v-else class="waterfall-container">
        <div
          v-for="item in items"
          :key="item.id"
          class="waterfall-item"
        >
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
              >
                <span style="display:none">{{ item.id }}</span>
              </el-checkbox>
            </div>
            <div class="card-content">
              <div class="card-header">
                <el-avatar :size="48" style="background: var(--text-muted); color: var(--text-on-primary)">
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
              <div class="deleted-info">
                <el-icon><Clock /></el-icon>
                <span>删除于 {{ formatDate(item.deleted_at) }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 无限滚动哨兵 -->
      <div ref="scrollSentinel" class="scroll-sentinel">
        <div v-if="loadingMore" class="infinite-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { listRecycleBin, restoreBatch } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const PAGE_SIZE = 20

const items = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const hasMore = ref(true)
const selectedIds = ref([])
const scrollSentinel = ref(null)

onMounted(() => {
  loadFirstPage()
  initInfiniteScroll()
})

async function loadFirstPage() {
  loading.value = true
  try {
    const { data } = await listRecycleBin(0, PAGE_SIZE)
    items.value = data.items || []
    hasMore.value = data.total > PAGE_SIZE
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  try {
    const skip = items.value.length
    const { data } = await listRecycleBin(skip, PAGE_SIZE)
    items.value = [...items.value, ...(data.items || [])]
    hasMore.value = (skip + (data.items?.length || 0)) < data.total
  } catch (e) {
    ElMessage.error('加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loadingMore.value = false
  }
}

// IntersectionObserver 无限滚动
let sentinelObserver = null

function initInfiniteScroll() {
  if (sentinelObserver) sentinelObserver.disconnect()
  sentinelObserver = new IntersectionObserver(
    entries => {
      if (entries[0].isIntersecting && !loadingMore.value && hasMore.value) {
        loadMore()
      }
    },
    { threshold: 0.1, rootMargin: '200px' }
  )
  nextTick(() => {
    if (scrollSentinel.value) {
      sentinelObserver.observe(scrollSentinel.value)
    }
  })
}

async function handleBatchRestore() {
  if (selectedIds.value.length === 0) return
  try {
    const { data } = await restoreBatch(selectedIds.value)
    ElMessage.success(`已恢复 ${data.restored} 份简历`)
    clearSelection()
    loadFirstPage()
  } catch (e) {
    ElMessage.error('恢复失败：' + (e.response?.data?.detail || e.message))
  }
}

function clearSelection() {
  selectedIds.value = []
}

function formatDate(dateStr) {
  if (!dateStr) return '未知'
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.recycle-bin-view {
  max-width: 1200px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: var(--font-size-2xl);
  margin: 0 0 8px;
  color: var(--hero-text);
}

.subtitle {
  color: var(--text-muted);
  margin: 0 0 24px;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--batch-bg);
  border-radius: var(--border-radius-md);
  margin-bottom: 16px;
  box-shadow: var(--batch-shadow);
}

/* ── 瀑布流容器 ──────────────────────────────────────── */
.waterfall-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  align-items: start;
}

.waterfall-item {
  width: 100%;
}

.scroll-sentinel {
  padding: 36px 0;
}

.infinite-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
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
  top: 8px;
  left: 8px;
  z-index: 1;
}

.card-content {
  cursor: pointer;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.card-info h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.card-info .title {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
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

.deleted-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}
</style>
