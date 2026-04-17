import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/resume/:id',
    name: 'Detail',
    component: () => import('../views/DetailView.vue'),
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
  },
  {
    path: '/recycle-bin',
    name: 'RecycleBin',
    component: () => import('../views/RecycleBinView.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ── 全局导航守卫 ──────────────────────────────────────

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('auth_token')

  // 需要登录但无 token → 跳转登录
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  // 已登录用户访问登录/注册页 → 跳转首页
  if (to.meta.requiresGuest && token) {
    return next('/')
  }

  // 管理员页面的权限检查
  // 路由层只做基础的 token 检查（requiresAuth），
  // 详细的角色验证由 AdminView 组件内部通过 auth store 的 isAdmin 完成
  if (to.meta.requiresAdmin && !token) {
    return next('/login')
  }

  next()
})

export default router
