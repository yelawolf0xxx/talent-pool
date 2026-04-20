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
          <div v-if="msg.role === 'user'" class="bubble">{{ msg.content }}</div>
          <div v-else class="bubble markdown-body" v-html="renderMarkdown(msg.content)"></div>
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
import { ref, nextTick, onMounted, computed } from 'vue'
import { chat } from '../api'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: true })

const messages = ref([])
const input = ref('')
const loading = ref(false)
const sessionId = ref('session_' + Date.now())
const chatContainer = ref(null)

const suggestions = [
  '推荐有 Java 开发经验的候选人',
  '人才库里有哪些前端开发？',
  '推荐适合微服务架构的候选人',
  '帮我找有项目管理经验的人',
]

/**
 * 将 Markdown 文本渲染为 HTML
 */
function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

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
  font-size: var(--font-size-lg);
}

.chat-container {
  height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: var(--chat-bg);
  border-radius: var(--border-radius-md);
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
  border-radius: var(--border-radius-md);
  line-height: 1.6;
  font-size: var(--font-size-base);
}

.message.user .bubble {
  background: var(--chat-bubble-user);
  color: var(--chat-bubble-user-text);
  border-bottom-right-radius: 4px;
}

.message.assistant .bubble {
  background: var(--chat-bubble-assistant);
  color: var(--chat-bubble-assistant-text);
  border: 1px solid var(--chat-bubble-assistant-border);
  border-bottom-left-radius: 4px;
}

.thinking {
  color: var(--text-muted);
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
  color: var(--text-muted);
  font-size: var(--font-size-xs);
}

.guide-card {
  margin-top: 16px;
}

.guide-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* ── Markdown 渲染样式 ─────────────────────────────── */
.bubble :deep(p) {
  margin: 0 0 8px;
}
.bubble :deep(p:last-child) {
  margin-bottom: 0;
}
.bubble :deep(strong) {
  color: var(--text-primary);
  font-weight: 600;
}
.bubble :deep(ul) {
  margin: 4px 0;
  padding-left: 20px;
}
.bubble :deep(li) {
  margin-bottom: 4px;
  line-height: 1.5;
}
.bubble :deep(h1),
.bubble :deep(h2),
.bubble :deep(h3) {
  margin: 12px 0 6px;
  font-weight: 600;
}
.bubble :deep(h1) { font-size: 1.2em; }
.bubble :deep(h2) { font-size: 1.1em; }
.bubble :deep(h3) { font-size: 1.05em; }
.bubble :deep(hr) {
  border: none;
  border-top: 1px solid var(--chat-bubble-assistant-border);
  margin: 12px 0;
}
.bubble :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: monospace;
}
.bubble :deep(pre) {
  background: rgba(0, 0, 0, 0.04);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}
.bubble :deep(pre code) {
  background: none;
  padding: 0;
}
</style>
