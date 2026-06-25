<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card class="stat-card">
          <div class="stat-icon" :style="{ background: stat.color }">
            <el-icon :size="32"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>最近上传</span>
      </template>
      <el-table :data="recentPhotos" style="width: 100%;">
        <el-table-column prop="photo_name" label="照片名称" />
        <el-table-column prop="pet_breed" label="品种" />
        <el-table-column prop="likes" label="点赞数" />
        <el-table-column prop="upload_time" label="上传时间" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="viewPhoto(row.id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Picture, Document, Collection, TrendCharts } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const stats = ref([
  { label: '总照片', value: 0, icon: Picture, color: '#409EFF' },
  { label: '猫咪', value: 0, icon: Document, color: '#67C23A' },
  { label: '狗狗', value: 0, icon: Collection, color: '#E6A23C' },
  { label: '总点赞', value: 0, icon: TrendCharts, color: '#F56C6C' }
])
const recentPhotos = ref([])

// 自动修复点赞统计
const fixLikes = async () => {
  try {
    await api.post('/fix-likes')
    console.log('✅ 点赞统计已自动修复')
  } catch (error) {
    console.error('修复点赞失败:', error)
  }
}

const loadData = async () => {
  try {
    const res = await api.get('/statistics')
    stats.value[0].value = res.total_photos || 0
    stats.value[1].value = res.cat_count || 0
    stats.value[2].value = res.dog_count || 0
    stats.value[3].value = res.total_likes || 0

    if (res.recent_photos) {
      recentPhotos.value = res.recent_photos
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const viewPhoto = (id) => {
  router.push(`/photos?highlight=${id}`)
}

onMounted(async () => {
  // 先修复点赞统计，再加载数据
  await fixLikes()
  await loadData()
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  padding: 10px;
}
.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
.stat-info {
  margin-left: 15px;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
}
.stat-label {
  color: #999;
  font-size: 14px;
}
</style>