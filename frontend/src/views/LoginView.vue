<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <h2 class="auth-title">登录</h2>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名或邮箱"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        还没有账号？
        <router-link to="/register" class="auth-link">去注册</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import authStore from '../stores/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

onMounted(() => {
  const saved = localStorage.getItem('remembered_username')
  if (saved) {
    form.username = saved
    rememberMe.value = true
  }
})

async function handleLogin() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authStore.login(form.username, form.password)

    if (rememberMe.value) {
      localStorage.setItem('remembered_username', form.username)
    } else {
      localStorage.removeItem('remembered_username')
    }

    ElMessage.success('登录成功')
    // 使用 setTimeout 确保 token 写入 localStorage 后再跳转
    setTimeout(() => {
      router.push('/')
    }, 100)
  } catch (e) {
    ElMessage.error('登录失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px);
}

.auth-card {
  width: 420px;
  max-width: 90vw;
}

.auth-title {
  text-align: center;
  margin: 0 0 24px;
  font-size: var(--font-size-2xl);
  color: var(--text-primary);
}

.auth-footer {
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-base);
}

.auth-link {
  color: var(--text-link);
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}
</style>
