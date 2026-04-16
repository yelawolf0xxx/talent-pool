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
      <div v-else class="resume-grid">
        <el-row :gutter="16">
          <el-col v-for="item in items" :key="item.id" :xs="24" :sm="12" :md="8">
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
              <div class="card-content">
                <div class="card-header">
                  <el-avatar :size="48" style="background: #909399">
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
                <div class="deleted-info">
                  <el-icon><Clock /></el-icon>
                  <span>删除于 {{ formatDate(item.deleted_at) }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && items.length > 0" class="load-more">
        <el-button :loading="loadingMore" @click="loadMore">
          {{ loadingMore ? '加载中...' : '加载更多' }}
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listRecycleBin, restoreBatch } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const PAGE_SIZE = 20

const items = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const hasMore = ref(true)
const selectedIds = ref([])

onMounted(loadFirstPage)

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
  font-size: 32px;
  margin: 0 0 8px;
  color: #1a1a2e;
}

.subtitle {
  color: #909399;
  margin: 0 0 24px;
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

.resume-grid {
  margin-bottom: 24px;
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

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
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

.deleted-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 12px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.load-more {
  text-align: center;
  margin-top: 24px;
}
</style>
