<template>
  <div v-if="resume" class="detail-view">
    <el-page-header @back="$router.back()" :title="'候选人详情'">
      <template #content>
        <span class="page-title">{{ resume.name || '未命名' }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="24" style="margin-top: 24px">
      <!-- 基本信息 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>基本信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="姓名">{{ resume.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="职位">{{ resume.current_title || '-' }}</el-descriptions-item>
            <el-descriptions-item label="工作年限">{{ resume.years_exp || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ resume.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="电话">{{ resume.phone || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 工作经历 -->
        <el-card style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <el-icon><Briefcase /></el-icon>
              <span>工作经历</span>
            </div>
          </template>
          <el-timeline v-if="workExperience.length > 0">
            <el-timeline-item
              v-for="(w, i) in workExperience"
              :key="i"
              :timestamp="`${w.start} ~ ${w.end || '至今'}`"
              placement="top"
            >
              <h4>{{ w.title }} @ {{ w.company }}</h4>
              <p v-if="w.description" class="desc">{{ w.description }}</p>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无工作经历" :image-size="60" />
        </el-card>

        <!-- 教育背景 -->
        <el-card style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <el-icon><School /></el-icon>
              <span>教育背景</span>
            </div>
          </template>
          <el-timeline v-if="education.length > 0">
            <el-timeline-item
              v-for="(e, i) in education"
              :key="i"
              :timestamp="e.year || ''"
              placement="top"
            >
              <h4>{{ e.school }}</h4>
              <p>{{ e.degree }} - {{ e.major }}</p>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无教育背景" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 右侧栏 -->
      <el-col :span="8">
        <!-- 技能标签 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Star /></el-icon>
              <span>技能</span>
            </div>
          </template>
          <el-tag
            v-for="skill in resume.skills"
            :key="skill"
            class="skill-tag"
            effect="plain"
          >
            {{ skill }}
          </el-tag>
          <p v-if="!resume.skills || resume.skills.length === 0" class="empty-text">暂无技能信息</p>
        </el-card>

        <!-- AI评价 -->
        <el-card style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <el-icon><MagicStick /></el-icon>
              <span>AI评价</span>
            </div>
          </template>
          <div v-if="resume.summary_text" class="ai-evaluation">
            <div class="eval-section">
              <h4>综合评价</h4>
              <p class="eval-text">{{ resume.summary_text }}</p>
            </div>
            <el-divider />
            <div class="eval-section">
              <h4>核心技能</h4>
              <div class="skill-grid">
                <el-tag
                  v-for="skill in resume.skills"
                  :key="skill"
                  class="eval-skill-tag"
                  effect="plain"
                  type="primary"
                >
                  {{ skill }}
                </el-tag>
                <span v-if="!resume.skills || resume.skills.length === 0" class="empty-text">暂无技能信息</span>
              </div>
            </div>
            <el-divider v-if="workExperience.length > 0" />
            <div v-if="workExperience.length > 0" class="eval-section">
              <h4>工作经历概览</h4>
              <div class="exp-brief">
                <div v-for="(w, i) in workExperience" :key="i" class="exp-brief-item">
                  <span class="exp-period">{{ w.start }} ~ {{ w.end || '至今' }}</span>
                  <span class="exp-role">{{ w.title }} @ {{ w.company }}</span>
                </div>
              </div>
            </div>
            <el-divider v-if="education.length > 0" />
            <div v-if="education.length > 0" class="eval-section">
              <h4>教育背景</h4>
              <div class="edu-list">
                <div v-for="(e, i) in education" :key="i" class="edu-item">
                  <span class="edu-school">{{ e.school }}</span>
                  <span class="edu-detail">{{ e.degree }} · {{ e.major }}{{ e.year ? ' · ' + e.year : '' }}</span>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无AI评价" :image-size="60" />
        </el-card>

        <!-- AI 匹配分析 -->
        <el-card style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <el-icon><MagicStick /></el-icon>
              <span>AI 匹配分析</span>
            </div>
          </template>
          <el-input
            v-model="recommendQuery"
            placeholder="输入岗位需求或疑问，如：需要一位钳工 / 适合做前台吗？"
            type="textarea"
            :rows="3"
            resize="none"
          />
          <el-button
            type="primary"
            :loading="loadingRec"
            @click="fetchRecommendation"
            style="margin-top: 12px; width: 100%"
          >
            生成分析
          </el-button>
          <div v-if="recommendation" class="recommendation">
            <el-divider />
            <div class="recommend-header">
              <el-tag
                :type="recommendation.suitable ? 'success' : 'danger'"
                size="large"
                effect="dark"
              >
                {{ recommendation.suitable ? '✓ 适合' : '✗ 不合适' }}
              </el-tag>
              <el-progress
                :percentage="recommendation.score"
                :color="recommendation.score >= 70 ? '#67c23a' : recommendation.score >= 40 ? '#e6a23c' : '#f56c6c'"
                :stroke-width="8"
                style="margin-left: 12px; flex: 1"
              />
            </div>
            <p class="conclusion">{{ recommendation.conclusion }}</p>
            <p class="detail">{{ recommendation.reason }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <div v-else-if="loading" style="padding: 40px">
    <el-skeleton :rows="10" animated />
  </div>

  <el-empty v-else description="简历不存在" />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getResume, getRecommendation } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const resume = ref(null)
const loading = ref(true)
const loadingRec = ref(false)
const recommendQuery = ref('')
const recommendation = ref(null)

const workExperience = computed(() => resume.value?.work_experience || [])
const education = computed(() => resume.value?.education || [])

onMounted(async () => {
  const id = route.params.id
  try {
    const { data } = await getResume(id)
    resume.value = data
  } catch (e) {
    ElMessage.error('获取简历失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
})

async function fetchRecommendation() {
  if (!recommendQuery.value.trim()) {
    ElMessage.warning('请输入岗位需求描述')
    return
  }
  loadingRec.value = true
  try {
    const { data } = await getRecommendation(route.params.id, recommendQuery.value)
    recommendation.value = data
  } catch (e) {
    ElMessage.error('生成推荐理由失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loadingRec.value = false
  }
}
</script>

<style scoped>
.page-title {
  font-size: 18px;
  font-weight: 600;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.skill-tag {
  margin: 4px;
}

.empty-text {
  color: #999;
  font-size: 13px;
  text-align: center;
}

.desc {
  color: #666;
  font-size: 13px;
  margin: 4px 0 0;
}

.recommendation p {
  color: #409eff;
  line-height: 1.6;
}

.recommend-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.conclusion {
  font-weight: 600;
  font-size: 14px;
  margin: 8px 0;
  color: #303133;
}

.detail {
  color: #606266;
  font-size: 13px;
  line-height: 1.8;
  margin: 8px 0;
}

/* AI评价 */
.ai-evaluation {
  padding: 4px 0;
}

.eval-section {
  margin: 8px 0;
}

.eval-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.eval-text {
  color: #409eff;
  line-height: 1.8;
  font-size: 14px;
  margin: 0;
}

.skill-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.eval-skill-tag {
  margin: 2px;
}

.exp-brief {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.exp-brief-item {
  display: flex;
  gap: 12px;
  font-size: 13px;
  padding: 4px 0;
  border-bottom: 1px dashed #ebeef5;
}

.exp-brief-item:last-child {
  border-bottom: none;
}

.exp-period {
  color: #909399;
  white-space: nowrap;
  min-width: 120px;
}

.exp-role {
  color: #606266;
}

.edu-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.edu-item {
  display: flex;
  gap: 12px;
  font-size: 13px;
  padding: 4px 0;
}

.edu-school {
  color: #303133;
  font-weight: 600;
  white-space: nowrap;
}

.edu-detail {
  color: #606266;
}
</style>
