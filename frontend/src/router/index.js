import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Home from '../views/Home.vue'
import PhotoList from '../views/PhotoList.vue'
import PhotoUpload from '../views/PhotoUpload.vue'
import Statistics from '../views/Statistics.vue'
import Logs from '../views/Logs.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/', component: Home, meta: { requiresAuth: true } },
  { path: '/photos', component: PhotoList, meta: { requiresAuth: true } },
  { path: '/upload', component: PhotoUpload, meta: { requiresAuth: true } },
  { path: '/statistics', component: Statistics, meta: { requiresAuth: true } },
  { path: '/logs', component: Logs, meta: { requiresAuth: true, adminOnly: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.adminOnly && user.role !== 'admin') {
    next('/')
  } else {
    next()
  }
})

export default router