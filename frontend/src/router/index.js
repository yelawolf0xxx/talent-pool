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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
