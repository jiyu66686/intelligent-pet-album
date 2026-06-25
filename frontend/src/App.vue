<template>
  <div id="app">
    <el-container>
      <el-header v-if="isLoggedIn">
        <el-menu mode="horizontal" :router="true">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/photos">相册</el-menu-item>
          <el-menu-item index="/upload">上传照片</el-menu-item>
          <el-menu-item index="/statistics">统计</el-menu-item>
          <el-menu-item v-if="isAdmin" index="/logs">操作日志</el-menu-item>
          <el-menu-item style="float: right;" @click="handleLogout">退出</el-menu-item>
          <span style="float: right; line-height: 60px; margin-right: 20px; color: #666;">
            欢迎，{{ currentUser?.username }}
          </span>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const currentUser = ref(null)

const isLoggedIn = computed(() => !!currentUser.value)
const isAdmin = computed(() => currentUser.value?.role === 'admin')

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  currentUser.value = null
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')
  if (token && user) {
    currentUser.value = JSON.parse(user)
  }
})
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Arial, sans-serif;
}
.el-header {
  padding: 0;
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
}
.el-main {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>