<template>
  <el-dropdown @command="handleThemeChange">
    <el-button text>
      <el-icon><Brush /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="business" :disabled="themeStore.currentTheme === 'business'">
          <span class="theme-option">
            <span class="theme-dot" style="background: #3b82f6"></span>
            柔和商务风
          </span>
        </el-dropdown-item>
        <el-dropdown-item command="minimal" :disabled="themeStore.currentTheme === 'minimal'">
          <span class="theme-option">
            <span class="theme-dot" style="background: #475569"></span>
            企业极简风
          </span>
        </el-dropdown-item>
        <el-dropdown-item command="apple" :disabled="themeStore.currentTheme === 'apple'">
          <span class="theme-option">
            <span class="theme-dot" style="background: #0071e3"></span>
            苹果极简风
          </span>
        </el-dropdown-item>
        <el-dropdown-item command="tech" :disabled="themeStore.currentTheme === 'tech'">
          <span class="theme-option">
            <span class="theme-dot" style="background: #6366f1"></span>
            科技深色风
          </span>
        </el-dropdown-item>
        <el-dropdown-item command="glass" :disabled="themeStore.currentTheme === 'glass'">
          <span class="theme-option">
            <span class="theme-dot" style="background: linear-gradient(135deg, #7a8fb5, #b5a8c4)"></span>
            毛玻璃风
          </span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import themeStore from '../stores/theme'

function handleThemeChange(theme) {
  themeStore.setTheme(theme)
}
</script>

<style scoped>
.theme-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.theme-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}
</style>
