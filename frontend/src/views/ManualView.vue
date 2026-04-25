<template>
  <div class="manual-view">
    <div class="view-header">
      <h2 class="view-title">用户手册</h2>
      <el-button text @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
    </div>

    <div class="manual-content" v-html="renderedManual" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: true, linkify: true, typographer: true })

const renderedManual = ref('')

const userManualContent = `# 用户手册

## 目录

1. [系统简介](#1-系统简介)
2. [快速开始](#2-快速开始)
3. [账号管理](#3-账号管理)
4. [首页：搜索与浏览](#4-首页搜索与浏览)
5. [简历详情与岗位匹配](#5-简历详情与岗位匹配)
6. [AI 助手对话](#6-ai-助手对话)
7. [上传简历](#7-上传简历)
8. [邮箱自动抓取简历](#8-邮箱自动抓取简历)
9. [常见问题](#9-常见问题)

---

## 1. 系统简介

AI 简历人才库系统是一款智能化的候选人管理工具，具备以下核心能力：

- **简历自动解析**：支持 PDF、DOC、DOCX、PPT、PPTX 格式，AI 自动提取姓名、技能、教育背景、工作经历等结构化信息
- **智能搜索**：关键词 + 语义搜索混合算法，按技能、年限筛选
- **AI 岗位匹配**：输入岗位需求，AI 生成匹配度评分和推荐理由
- **AI 对话**：自然语言提问，AI 基于真实人才库数据推荐候选人
- **邮箱自动抓取**：配置 IMAP 邮箱后，系统自动扫描邮件附件中的简历并解析

---

## 2. 快速开始

### 2.1 登录系统

1. 打开浏览器，访问系统地址
2. 输入用户名和密码登录
3. 如果没有账号，请联系管理员创建账号

### 2.2 系统界面概览

登录后，顶部导航栏包含以下入口：

| 入口 | 说明 |
|------|------|
| **简历搜索** | 首页，搜索和浏览人才库 |
| **AI 助手** | 与 AI 对话，智能推荐候选人 |
| **用户名菜单** | 邮箱管理、退出登录 |

---

## 3. 账号管理

### 3.1 注册账号

1. 在登录页面点击 **注册**
2. 填写用户名、邮箱地址和密码
3. 点击 **注册** 完成账号创建

### 3.2 登录 / 退出

- **登录**：输入用户名或邮箱 + 密码
- **退出**：点击顶部导航栏的用户名 → **退出登录**

### 3.3 密码修改

如需修改密码，请联系管理员操作。

### 3.4 Token 过期

系统登录 Token 默认有效期为 **24 小时**。过期后系统会自动清除 Token 并跳转至登录页，重新登录即可。

---

## 4. 首页：搜索与浏览

### 4.1 简历来源 Tab

首页顶部有两个 Tab 切换：

| Tab | 说明 |
|-----|------|
| **全部简历** | 显示系统中所有来源的简历（手动上传 + 所有用户邮箱同步） |
| **我的简历** | 仅显示从你配置的邮箱中同步抓取的简历 |

### 4.2 关键词搜索

在搜索框中输入关键词，例如：

- \`Java 后端开发\`
- \`前端工程师 Vue React\`
- \`产品经理\`

点击 **搜索** 按钮或按 **Enter** 键执行搜索。

### 4.3 技能筛选

在技能选择下拉框中，可以选择多个技能进行精确筛选：

- 输入技能名称（如 \`Python\`、\`AWS\`）
- 支持多选
- 支持手动输入新技能标签

### 4.4 年限筛选

在"最低年限"输入框中设置年限要求，例如输入 \`3\` 则只显示 3 年及以上经验的候选人。

### 4.5 搜索结果

搜索结果按匹配度排序，每条结果展示：

- 候选人姓名和头像
- 当前职位
- 工作年限和技能标签
- 匹配度百分比（搜索结果中显示）

点击任意简历卡片可进入详情页。

### 4.6 查看全部简历

搜索后点击 **查看全部简历** 按钮，可退出搜索模式，回到简历画廊。

### 4.7 无限滚动

简历列表支持无限滚动，滚动到底部自动加载下一页，无需手动翻页。

---

## 5. 简历详情与岗位匹配

### 5.1 查看简历详情

点击首页任意简历卡片，进入简历详情页，展示：

- 基本信息（姓名、邮箱、电话）
- 当前职位和工作年限
- 教育背景
- 技能列表
- 工作经历（公司、职位、时间、描述）
- AI 生成的简历摘要

### 5.2 岗位匹配推荐

在详情页底部，可以输入岗位需求描述：

1. 在输入框中填写岗位要求，例如：
   > 需要 3 年以上 Java 开发经验，熟悉 Spring Boot 和 MySQL，有微服务架构经验
2. 点击 **分析匹配度**
3. AI 会生成以下分析结果：
   - **是否适合**：适合 / 不适合
   - **匹配度分数**：0-100 分
   - **一句话总结**
   - **详细分析说明**

> 岗位匹配分析需要调用 AI，请耐心等待，通常 10-30 秒内完成。

---

## 6. AI 助手对话

### 6.1 基本对话

进入 AI 助手页面后，可以直接向 AI 提问，例如：

- \`如何评估候选人的技术深度？\`
- \`面试后端工程师应该关注哪些方面？\`
- \`如何编写一份好的 JD？\`

### 6.2 候选人推荐（核心功能）

AI 助手能够基于**真实人才库数据**推荐候选人。当你的问题包含推荐意图时，系统会自动检索人才库并将匹配结果注入对话。

**支持的提问方式：**

| 提问示例 | 效果 |
|----------|------|
| \`推荐有 Java 开发经验的候选人\` | AI 检索 Java 相关候选人并推荐 |
| \`人才库里有前端开发经验的人有哪些？\` | 列出前端相关候选人 |
| \`帮我找 3 年以上 Python 经验的人\` | 筛选并推荐 Python 候选人 |
| \`推荐适合微服务架构的候选人\` | 推荐有微服务经验的人选 |

**AI 的回复基于真实数据**，会包含候选人的姓名、职位、年限、技能和亮点信息。

### 6.3 针对特定候选人对话

在简历详情页点击 **与 AI 对话**，AI 会自动关联该候选人的简历信息，你可以针对该候选人提问：

- \`这个候选人的技术深度如何？\`
- \`他和我们岗位匹配吗？\`
- \`有什么需要进一步了解的地方？\`

---

## 7. 上传简历

### 7.1 手动上传

1. 在首页点击 **上传简历** 按钮
2. 选择简历文件（支持多选）
3. 支持格式：**PDF、DOC、DOCX、PPT、PPTX**
4. 单文件最大 **20MB**

### 7.2 上传后解析

上传完成后，系统会弹窗询问是否立即解析：

- **立即解析**：触发扫描，AI 开始解析上传的简历
- **稍后处理**：简历文件已保存，等下次自动扫描时解析（默认每 5 分钟一次）

---

## 8. 邮箱自动抓取简历

### 8.1 功能说明

系统支持通过 IMAP 协议连接邮箱，自动扫描邮件附件中的简历文件并解析到人才库。配置后：

- **自动扫描**：系统每隔一段时间自动扫描邮箱中的未读邮件
- **附件提取**：自动提取 PDF、DOC、DOCX、PPT、PPTX 格式的附件
- **归属追踪**：从你邮箱抓取的简历会标记为你所有，在"我的简历"Tab 中可见

### 8.2 获取邮箱授权码

大多数邮箱服务（如 QQ、163、Gmail）不支持直接使用登录密码连接 IMAP，需要使用**授权码**。

#### QQ 邮箱

1. 登录 QQ 邮箱网页版
2. 进入 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务**
4. 开启 **IMAP/SMTP 服务**
5. 按提示生成并记录 **授权码**

#### 163 邮箱

1. 登录 163 邮箱网页版
2. 进入 **设置** → **POP3/SMTP/IMAP**
3. 开启 **IMAP 服务**
4. 按提示生成并记录 **授权码**

#### Gmail

1. 登录 Google 账号
2. 进入 **管理您的 Google 账号** → **安全性**
3. 开启 **两步验证**
4. 生成 **应用专用密码**

### 8.3 配置邮箱

1. 点击顶部导航栏的用户名 → **邮箱管理**
2. 点击 **新增邮箱配置**
3. 填写以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| IMAP 服务器 | 邮箱的 IMAP 服务器地址 | \`imap.qq.com\` |
| IMAP 端口 | IMAP 端口，默认 993 | \`993\` |
| 邮箱地址 | 你的邮箱地址 | \`hr@company.com\` |
| 密码/授权码 | 邮箱密码或 IMAP 授权码 | \`授权码\` |
| 下载目录 | 附件本地保存路径（可选） | \`\\\\\\\\192.168.3.30\\\\\\\\简历资料夹\` |

4. 点击 **保存**

### 8.4 常用 IMAP 服务器地址

| 邮箱 | IMAP 服务器 | 端口 |
|------|-------------|------|
| QQ 邮箱 | \`imap.qq.com\` | 993 |
| 163 邮箱 | \`imap.163.com\` | 993 |
| 126 邮箱 | \`imap.126.com\` | 993 |
| Gmail | \`imap.gmail.com\` | 993 |
| Outlook | \`outlook.office365.com\` | 993 |
| 企业邮箱（腾讯） | \`imap.exmail.qq.com\` | 993 |

### 8.5 手动同步

配置完成后，点击对应邮箱配置行的 **同步** 按钮，立即触发一次邮箱扫描。系统会：

1. 连接 IMAP 获取未读邮件
2. 提取简历格式附件并保存到简历目录
3. **自动触发解析**，将新简历录入人才库

### 8.6 同步日志

切换到 **同步日志** Tab，可以查看每次同步的执行情况：

- 扫描邮件数量
- 新附件数量
- 成功下载数量
- 失败数量和原因
- 同步时间

### 8.7 注意事项

- 已同步的邮件会被标记为已读，避免重复处理
- 单封邮件最多提取 **20 个** 简历附件
- 附件保存到简历目录后**立即触发解析**，无需等待定时扫描

---

## 9. 常见问题

### Q: AI 解析简历失败怎么办？

可能原因：
- 简历文本过短（少于 50 字符），无法提取有效信息
- AI API 调用失败（检查网络和密钥配置）
- 简历格式特殊（如图片型 PDF），AI 无法识别文字

**解决方案**：确保简历为文字型 PDF，内容完整。图片型 PDF 需要 OCR 处理。

### Q: 搜索结果为空怎么办？

- 检查关键词是否过于具体，尝试使用更通用的关键词
- 确认技能标签格式是否正确（如 \`Java\` vs \`java\`）
- 检查是否设置了过高的年限筛选条件

### Q: AI 推荐的候选人不准确？

- AI 的推荐基于人才库中的真实数据，推荐质量取决于简历解析的准确性
- 尝试更具体的岗位描述，包含关键技能要求
- 在 AI 对话中可以追问具体候选人的详细信息

### Q: 邮箱同步不工作？

检查清单：
1. IMAP 服务器地址和端口是否正确
2. 使用的是**授权码**而非登录密码
3. 邮箱配置是否已启用
4. 查看同步日志中的错误信息
5. 确认邮箱中有未读邮件（系统只扫描未读邮件）

### Q: 上传的文件格式不支持？

当前支持：**PDF、DOC、DOCX、PPT、PPTX**。其他格式（如图片、TXT）暂不支持。

旧版 \`.doc\` 和 \`.ppt\` 文件需要服务器安装 **LibreOffice** 进行格式转换。

### Q: "我的简历"和"全部简历"有什么区别？

| Tab | 内容 |
|-----|------|
| **我的简历** | 仅显示从你配置的邮箱中同步抓取的简历 |
| **全部简历** | 显示系统中所有来源的简历（手动上传 + 所有用户邮箱同步） |

### Q: 如何确保简历不被重复解析？

系统使用 **SHA256 校验和** 进行文件去重：
- 同一个文件（内容相同）不会被重复处理
- 文件内容变更后（如重新保存），校验和不同，会重新解析

### Q: Token 过期了怎么办？

Token 默认有效期 24 小时。过期后系统自动清除 Token 并跳转登录页，重新登录即可。
`

onMounted(() => {
  renderedManual.value = md.render(userManualContent)
})
</script>

<style scoped>
.manual-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.view-title {
  margin: 0;
  font-size: var(--font-size-xl, 20px);
  color: var(--text-primary, #303133);
}

.manual-content {
  background: var(--bg-surface, #fff);
  border-radius: var(--border-radius-lg, 8px);
  padding: 32px;
  box-shadow: var(--shadow-card, 0 2px 12px rgba(0, 0, 0, 0.08));
}

.manual-content :deep(h1) {
  font-size: 24px;
  margin: 0 0 16px;
  color: var(--text-primary, #303133);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color, #ebeef5);
}

.manual-content :deep(h2) {
  font-size: 20px;
  margin: 32px 0 16px;
  color: var(--text-primary, #303133);
}

.manual-content :deep(h3) {
  font-size: 16px;
  margin: 24px 0 12px;
  color: var(--text-primary, #303133);
}

.manual-content :deep(h4) {
  font-size: 15px;
  margin: 20px 0 8px;
  color: var(--text-secondary, #606266);
}

.manual-content :deep(p) {
  line-height: 1.8;
  color: var(--text-primary, #303133);
  margin: 12px 0;
}

.manual-content :deep(ul),
.manual-content :deep(ol) {
  padding-left: 24px;
  line-height: 1.8;
}

.manual-content :deep(li) {
  margin: 6px 0;
}

.manual-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.manual-content :deep(th),
.manual-content :deep(td) {
  border: 1px solid var(--border-color, #ebeef5);
  padding: 10px 14px;
  text-align: left;
}

.manual-content :deep(th) {
  background: var(--bg-surface-hover, #f5f7fa);
  font-weight: 600;
}

.manual-content :deep(blockquote) {
  border-left: 4px solid var(--color-primary, #409eff);
  margin: 16px 0;
  padding: 12px 16px;
  background: var(--bg-surface-hover, #f5f7fa);
  color: var(--text-secondary, #606266);
}

.manual-content :deep(code) {
  background: var(--bg-surface-hover, #f5f7fa);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
  font-family: 'Courier New', monospace;
}

.manual-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color, #ebeef5);
  margin: 32px 0;
}

.manual-content :deep(strong) {
  color: var(--text-primary, #303133);
}
</style>
