<template>
  <div class="email-tutorial-view">
    <h2 class="view-title">邮箱配置教程</h2>

    <el-alert type="info" :closable="false" style="margin-bottom: 24px">
      <template #title>系统通过 IMAP 协议连接邮箱，自动抓取邮件附件中的简历文件。配置前需要先获取邮箱的「授权码」。</template>
    </el-alert>

    <!-- 通用配置步骤 -->
    <el-card class="tutorial-card" shadow="never">
      <template #header>
        <h3 class="section-title">通用配置步骤</h3>
      </template>
      <el-steps :active="3" finish-status="success" simple style="margin-bottom: 20px">
        <el-step title="开启 IMAP" />
        <el-step title="获取授权码" />
        <el-step title="填写配置" />
      </el-steps>

      <div class="step-list">
        <div class="step-item">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>开启 IMAP 服务</h4>
            <p>登录邮箱网页版，进入设置 → 账户 → POP3/IMAP/SMTP 服务，开启 IMAP 服务。</p>
          </div>
        </div>
        <div class="step-item">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>生成授权码</h4>
            <p>开启 IMAP 后，系统会要求你生成「授权码」（不是登录密码）。按提示操作并妥善保存。</p>
          </div>
        </div>
        <div class="step-item">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>填写配置信息</h4>
            <p>返回本系统邮箱管理页面，点击「新增邮箱配置」，填入 IMAP 服务器、邮箱地址、授权码等信息。</p>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 各邮箱详细教程 -->
    <div v-for="provider in providers" :key="provider.name" class="tutorial-card">
      <el-collapse>
        <el-collapse-item :name="provider.name">
          <template #title>
            <div class="provider-title">
              <el-tag :type="provider.tagType" size="small" style="margin-right: 8px">{{ provider.name }}</el-tag>
              <span>{{ provider.subtitle }}</span>
            </div>
          </template>

          <div class="provider-detail">
            <h4>配置参数</h4>
            <el-table :data="[provider.params]" border size="small">
              <el-table-column prop="server" label="IMAP 服务器" />
              <el-table-column prop="port" label="端口" width="80" />
              <el-table-column prop="ssl" label="SSL" width="80" />
            </el-table>

            <h4 style="margin-top: 20px">获取授权码步骤</h4>
            <ol class="instruction-list">
              <li v-for="(step, i) in provider.steps" :key="i">{{ step }}</li>
            </ol>

            <h4 style="margin-top: 20px">注意事项</h4>
            <ul class="tip-list">
              <li v-for="(tip, i) in provider.tips" :key="i">{{ tip }}</li>
            </ul>

            <el-alert v-if="provider.warning" :type="provider.warningType || 'warning'" :closable="false" style="margin-top: 16px">
              <template #title>{{ provider.warning }}</template>
            </el-alert>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 常见问题 -->
    <el-card class="tutorial-card" shadow="never">
      <template #header>
        <h3 class="section-title">常见问题</h3>
      </template>
      <el-collapse>
        <el-collapse-item v-for="qa in faqs" :key="qa.q" :title="qa.q">
          <p>{{ qa.a }}</p>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
const providers = [
  {
    name: 'QQ 邮箱',
    subtitle: 'qq.com / foxmail.com',
    tagType: 'danger',
    params: { server: 'imap.qq.com', port: '993', ssl: '是' },
    steps: [
      '登录 QQ 邮箱网页版 (mail.qq.com)',
      '点击顶部「设置」→「账户」标签页',
      '向下滚动找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务」',
      '点击「IMAP/SMTP 服务」右侧的「开启」按钮',
      '按提示发送短信 "配置邮件客户端" 到 1069070060',
      '短信发送成功后，页面会显示授权码，请复制保存',
    ],
    tips: [
      '授权码只显示一次，务必立即保存',
      '配置时密码/授权码栏填写授权码，不是 QQ 登录密码',
      '一个 QQ 邮箱可以生成多个授权码',
    ],
  },
  {
    name: '163 网易邮箱',
    subtitle: '163.com / 126.com',
    tagType: 'warning',
    params: { server: 'imap.163.com', port: '993', ssl: '是' },
    steps: [
      '登录 163 邮箱网页版 (mail.163.com)',
      '点击顶部「设置」→「POP3/SMTP/IMAP」',
      '找到「IMAP/SMTP 服务」选项',
      '点击「开启」按钮',
      '按提示通过手机发送短信验证',
      '页面会显示「客户端授权密码」，设置并记住它',
    ],
    tips: [
      '网易邮箱需要单独设置「客户端授权密码」，不是登录密码',
      '如果忘记密码，可以在同一页面关闭后重新开启',
      '126 邮箱的 IMAP 服务器为 imap.126.com',
    ],
  },
  {
    name: 'Gmail',
    subtitle: 'gmail.com',
    tagType: 'info',
    params: { server: 'imap.gmail.com', port: '993', ssl: '是' },
    steps: [
      '登录 Google 账号管理页面 (myaccount.google.com)',
      '进入「安全性」标签页',
      '开启「两步验证」（如果尚未开启）',
      '回到安全性页面，找到「应用专用密码」',
      '点击「选择应用」→「邮件」，选择设备类型为「其他」，自定义名称如 "简历系统"',
      '点击「生成」，页面会显示 16 位密码，复制保存',
    ],
    tips: [
      '必须先开启两步验证才能使用应用专用密码',
      '配置时填写的是 16 位应用专用密码，不是 Google 账号密码',
      '每个应用专用密码只能使用一次，但可以生成多个',
    ],
    warning: 'Gmail 在中国大陆可能需要科学上网才能正常连接 IMAP 服务。',
    warningType: 'error',
  },
  {
    name: 'Outlook / Hotmail',
    subtitle: 'outlook.com / hotmail.com / live.com',
    tagType: 'success',
    params: { server: 'outlook.office365.com', port: '993', ssl: '是' },
    steps: [
      '登录 Outlook 网页版 (outlook.live.com)',
      '点击右上角齿轮图标 →「查看所有 Outlook 设置」',
      '选择「同步电子邮件」→「POP 和 IMAP」',
      '确认 IMAP 已启用（默认应已开启）',
      '如果启用了两步验证，需要到 Microsoft 账户安全页面生成「应用密码」',
      '配置时使用应用密码代替账户密码',
    ],
    tips: [
      'Outlook 默认开启 IMAP，通常无需额外设置',
      '如果启用了两步验证，必须生成应用密码',
      '企业版 Outlook (Office 365) IMAP 服务器相同',
    ],
  },
  {
    name: '企业邮箱',
    subtitle: '阿里企业邮 / 腾讯企业邮 / 网易企业邮',
    tagType: '',
    params: { server: '请咨询管理员', port: '993', ssl: '是' },
    steps: [
      '联系企业邮箱管理员获取 IMAP 服务器地址',
      '登录企业邮箱网页版',
      '进入设置 → 账户安全 / 客户端授权',
      '开启 IMAP 服务并生成授权码（部分企业邮箱直接使用登录密码）',
    ],
    tips: [
      '腾讯企业邮 IMAP 服务器: imap.exmail.qq.com',
      '阿里企业邮 IMAP 服务器: imap.qiye.aliyun.com',
      '网易企业邮 IMAP 服务器: imap.qiye.163.com',
      '部分企业邮箱直接使用登录密码，无需授权码',
    ],
    warning: '企业邮箱的 IMAP 服务可能受管理员策略限制，如无法连接请联系管理员确认是否开启 IMAP。',
  },
]

const faqs = [
  {
    q: '授权码和登录密码有什么区别？',
    a: '授权码是专门用于第三方邮件客户端（如本系统）访问邮箱的专用密码。出于安全考虑，主流邮箱服务都要求使用授权码而非登录密码连接 IMAP。即使登录密码泄露，攻击者也无法通过授权码登录你的邮箱网页版。',
  },
  {
    q: '配置后多久同步一次？',
    a: '系统默认每 24 小时自动同步一次。你也可以在邮箱配置列表中点击「同步」按钮手动触发即时同步。',
  },
  {
    q: '同步会下载所有邮件吗？',
    a: '系统会扫描收件箱，仅下载带有附件（PDF/DOC/DOCX/PPT/PPTX 格式）的邮件附件作为简历文件。不含附件的邮件会被忽略。',
  },
  {
    q: '提示 "连接超时" 或 "认证失败" 怎么办？',
    a: '请检查：1) IMAP 服务器地址是否正确；2) 端口是否为 993；3) 授权码是否已过期或被重置；4) 网络是否能访问该 IMAP 服务器。部分企业网络可能限制了外部 IMAP 连接。',
  },
  {
    q: '可以配置多个邮箱吗？',
    a: '可以。每个邮箱配置独立管理，同步的简历会自动关联到对应账号下。你可以在首页通过「我的简历」Tab 查看从个人邮箱同步的简历。',
  },
  {
    q: '同步的简历存放在哪里？',
    a: '附件会下载到配置的「下载目录」下的 email_{邮箱前缀}/YYYY-MM-DD/ 子目录中。如果未填写下载目录，将使用系统默认路径。',
  },
]
</script>

<style scoped>
.email-tutorial-view {
  background: var(--bg-surface);
  border-radius: var(--border-radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
}

.view-title {
  margin: 0 0 20px;
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

.tutorial-card {
  margin-bottom: 20px;
}

.tutorial-card :deep(.el-card__header) {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color);
}

.section-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.step-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--font-size-sm);
}

.step-content h4 {
  margin: 0 0 4px;
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

.step-content p {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}

.provider-title {
  display: flex;
  align-items: center;
  width: 100%;
  font-size: var(--font-size-base);
  font-weight: 500;
}

.provider-detail h4 {
  margin: 0 0 8px;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
}

.instruction-list,
.tip-list {
  margin: 0;
  padding-left: 24px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 2;
}

.tip-list {
  list-style: disc;
}

.el-collapse-item :deep(.el-collapse-item__content) {
  padding-bottom: 16px;
}
</style>
