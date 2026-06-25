<template>
  <div class="statistics">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>宠物类型分布</span>
          </template>
          <div ref="pieChart" style="height: 350px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>品种排行</span>
          </template>
          <div ref="barChart" style="height: 350px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>统计数据概览</span>
      </template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="总照片数">{{ stats.total_photos || 0 }}</el-descriptions-item>
        <el-descriptions-item label="🐱 猫咪">{{ stats.cat_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="🐶 狗狗">{{ stats.dog_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="品种种类">{{ stats.breed_stats?.length || 0 }}</el-descriptions-item>
        <el-descriptions-item label="最近上传">{{ stats.recent_photos?.[0]?.upload_time || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="今日上传">{{ todayUploads }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

const stats = ref({})
const pieChart = ref(null)
const barChart = ref(null)
const todayUploads = ref(0)

const loadData = async () => {
  try {
    const res = await api.get('/statistics')
    stats.value = res

    if (res.recent_photos) {
      const today = new Date().toDateString()
      const todayPhotos = res.recent_photos.filter(p =>
        new Date(p.upload_time).toDateString() === today
      )
      todayUploads.value = todayPhotos.length
    }

    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const renderCharts = () => {
  if (pieChart.value) {
    const pieInstance = echarts.init(pieChart.value)
    pieInstance.setOption({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        type: 'pie',
        radius: '50%',
        data: [
          { value: stats.value.cat_count || 0, name: '🐱 猫咪', itemStyle: { color: '#67C23A' } },
          { value: stats.value.dog_count || 0, name: '🐶 狗狗', itemStyle: { color: '#E6A23C' } }
        ],
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
      }]
    })
  }

  if (barChart.value && stats.value.breed_stats && stats.value.breed_stats.length > 0) {
    const barInstance = echarts.init(barChart.value)
    const data = stats.value.breed_stats.slice(0, 10)
    barInstance.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: data.map(item => item.breed),
        axisLabel: { rotate: 30 }
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: data.map(item => item.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: '#79bbff' }
          ])
        }
      }]
    })
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => {})
})
</script>