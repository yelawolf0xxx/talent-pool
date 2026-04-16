<template>
  <div class="chat-view">
    <el-card class="chat-card">
      <template #header>
        <div class="header">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 人事助手</span>
          <el-tag type="info" size="small" style="margin-left: auto">
            可随时提问关于候选人的问题
          </el-tag>
        </div>
      </template>

      <div ref="chatContainer" class="chat-container">
        <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
          <el-avatar :size="32" :style="{ background: msg.role === 'user' ? '#409eff' : '#67c23a' }">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><Service /></el-icon>
          </el-avatar>
          <div class="bubble">{{ msg.content }}</div>
        </div>

        <div v-if="loading" class="message assistant">
          <el-avatar :size="32" style="background: #67c23a">
            <el-icon><Service /></el-icon>
          </el-avatar>
          <div class="bubble thinking">思考中...</div>
        </div>
      </div>

      <div class="input-area">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题，如：'这个候选人适合高级开发岗位吗？'"
          @keydown.ctrl.enter="sendMessage"
        />
        <div class="input-actions">
          <span class="hint">Ctrl+Enter 发送</span>
          <el-button type="primary" :loading="loading" @click="sendMessage">
            发送
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 欢迎引导 -->
    <el-card v-if="messages.length === 0" class="guide-card">
      <template #header>
        <span>快速开始</span>
      </template>
      <div class="guide-items">
        <el-button v-for="q in suggestions" :key="q" text @click="quickAsk(q)">
          <el-tag type="info" effect="plain">{{ q }}</el-tag>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chat } from '../api'
import { ElMessage } from 'element-plus'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const sessionId = ref('session_' + Date.now())
const chatContainer = ref(null)

const suggestions = [
  '如何快速筛选合适的候选人？',
  '这个岗位需要哪些核心技能？',
  '如何评估候选人的技术能力？',
  '人才库里有多少人做过微服务？',
]

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function quickAsk(q) {
  input.value = q
  sendMessage()
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const { data } = await chat(
      [{ role: 'user', content: text }],
      sessionId.value,
    )
    messages.value.push({ role: 'assistant', content: data.reply })
  } catch (e) {
    ElMessage.error('对话失败：' + (e.response?.data?.detail || e.message))
    messages.value.push({
      role: 'assistant',
      content: '抱歉，服务暂时不可用，请稍后再试。',
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-view {
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.chat-container {
  height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
}

.message.user .bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.assistant .bubble {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 4px;
}

.thinking {
  color: #999;
  font-style: italic;
}

.input-area {
  margin-top: 16px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hint {
  color: #999;
  font-size: 12px;
}

.guide-card {
  margin-top: 16px;
}

.guide-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
