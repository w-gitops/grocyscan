import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../pages/LoginPage.vue'), meta: { public: true } },
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: '/scan' },
      { path: 'scan', name: 'Scan', component: () => import('../pages/ScanPage.vue') },
      { path: 'products', name: 'Products', component: () => import('../pages/ProductsPage.vue') },
      { path: 'inventory', name: 'Inventory', component: () => import('../pages/InventoryPage.vue') },
      { path: 'locations', name: 'Locations', component: () => import('../pages/LocationsPage.vue') },
      { path: 'jobs', name: 'Jobs', component: () => import('../pages/JobsPage.vue') },
      { path: 'logs', name: 'Logs', component: () => import('../pages/LogsPage.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../pages/SettingsPage.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (!to.meta.public && auth.authEnabled && !auth.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
